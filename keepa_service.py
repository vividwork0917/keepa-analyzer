"""
Keepa API Integration Service
Handles all communication with Keepa API
"""
import requests
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from decimal import Decimal
from config import KEEPA_API_KEY, KEEPA_API_BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES
from models import Product, PriceHistory
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class KeepaAPIService:
    """Service to interact with Keepa API"""

    def __init__(self, api_key: str = KEEPA_API_KEY):
        self.api_key = api_key
        self.base_url = KEEPA_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Keepa-Analyzer/1.0'
        })

    def get_product_data(self, asin: str, history: int = 1) -> Optional[Dict]:
        """
        Get product data from Keepa API

        Args:
            asin: Amazon ASIN
            history: Include price history (0=no, 1=yes)

        Returns:
            Product data dict or None if failed
        """
        try:
            url = f"{self.base_url}/product"
            params = {
                'key': self.api_key,
                'asin': asin,
                'domain': 'JP',  # Japan domain
                'history': history,
                'stats': 1,  # Include statistics
                'offers': 1  # Include offer information
            }

            response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            data = response.json()

            if data.get('products'):
                return data['products'][0]
            else:
                logger.warning(f"No product data returned for ASIN: {asin}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Keepa API request failed for ASIN {asin}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error processing Keepa response for ASIN {asin}: {str(e)}")
            return None

    def extract_price_history(self, product_data: Dict, asin: str) -> List[Dict]:
        """
        Extract price history from Keepa product data

        Args:
            product_data: Raw Keepa product data
            asin: Product ASIN

        Returns:
            List of price history records
        """
        price_history = []

        try:
            # Keepa stores prices as [timestamp, price] pairs
            if 'csv' in product_data:
                csv_data = product_data['csv']

                # CSV structure: [0]=ASIN, [1]=Amazon, [2]=New, [3]=Used, [4]=Refurb, [5]=Rental, etc.
                if len(csv_data) > 1:
                    # Amazon price history [csv[1]]
                    amazon_prices = csv_data[1] if len(csv_data) > 1 else []
                    # New offer count [csv[2]]
                    new_offer_counts = csv_data[2] if len(csv_data) > 2 else []
                    # Used offer count [csv[3]]
                    used_offer_counts = csv_data[3] if len(csv_data) > 3 else []

                    # Process price data (timestamps come in pairs)
                    for i in range(0, len(amazon_prices), 2):
                        if i + 1 < len(amazon_prices):
                            timestamp_ms = amazon_prices[i]
                            price_cents = amazon_prices[i + 1]

                            # Convert Keepa timestamp to date
                            # Keepa epoch: 2011-01-01 00:00:00
                            keepa_epoch = datetime(2011, 1, 1)
                            date = keepa_epoch + timedelta(days=timestamp_ms)

                            price_history.append({
                                'date': date.date(),
                                'amazon_price': Decimal(price_cents) / 100 if price_cents > 0 else None,
                                'timestamp': timestamp_ms
                            })

        except Exception as e:
            logger.error(f"Error extracting price history for ASIN {asin}: {str(e)}")

        return price_history

    def extract_product_info(self, product_data: Dict) -> Dict:
        """
        Extract key product information from Keepa data

        Args:
            product_data: Raw Keepa product data

        Returns:
            Cleaned product info dict
        """
        return {
            'asin': product_data.get('asin'),
            'title': product_data.get('title'),
            'category': product_data.get('categoryTree', [None])[0],
            'latest_price': Decimal(product_data.get('amazonPrice', 0) or 0) / 100,
            'lowest_price': Decimal(product_data.get('amazonPriceHistory', [None])[-1] or 0) / 100 if product_data.get('amazonPriceHistory') else None,
            'bsr': product_data.get('salesRanks', {}),
            'rating': Decimal(product_data.get('reviews', [0, 0])[0] or 0) / 10,
            'review_count': product_data.get('reviews', [0, None])[1] or 0,
            'new_offer_count': product_data.get('offers', 0),
        }

    def fetch_and_store_product(
        self,
        product_id: int,
        asin: str,
        db: Session
    ) -> bool:
        """
        Fetch product data from Keepa and store price history

        Args:
            product_id: Database product ID
            asin: Amazon ASIN
            db: Database session

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get product data from Keepa
            product_data = self.get_product_data(asin)
            if not product_data:
                logger.error(f"Failed to fetch data for ASIN: {asin}")
                return False

            # Extract price history
            price_records = self.extract_price_history(product_data, asin)

            # Store price history in database
            for record in price_records:
                # Check if record already exists
                existing = db.query(PriceHistory).filter(
                    (PriceHistory.product_id == product_id) &
                    (PriceHistory.date == record['date'])
                ).first()

                if not existing:
                    new_record = PriceHistory(
                        product_id=product_id,
                        asin=asin,
                        date=record['date'],
                        amazon_price=record.get('amazon_price'),
                        keepa_request_ts=datetime.now()
                    )
                    db.add(new_record)

            db.commit()
            logger.info(f"Stored {len(price_records)} price records for ASIN: {asin}")
            return True

        except Exception as e:
            logger.error(f"Error fetching/storing product data for ASIN {asin}: {str(e)}")
            db.rollback()
            return False

    def bulk_fetch_products(
        self,
        asins: List[str],
        db: Session,
        callback=None
    ) -> Dict[str, bool]:
        """
        Fetch multiple products from Keepa

        Args:
            asins: List of ASINs to fetch
            db: Database session
            callback: Optional progress callback

        Returns:
            Dict mapping ASIN to success status
        """
        results = {}

        for i, asin in enumerate(asins):
            if callback:
                callback(i + 1, len(asins), asin)

            # Get product from database
            product = db.query(Product).filter(Product.asin == asin).first()
            if product:
                success = self.fetch_and_store_product(product.id, asin, db)
                results[asin] = success
            else:
                logger.warning(f"Product not found in DB for ASIN: {asin}")
                results[asin] = False

        return results

    def get_latest_price_info(self, asin: str, db: Session) -> Optional[Dict]:
        """
        Get latest price information for a product

        Args:
            asin: Product ASIN
            db: Database session

        Returns:
            Latest price record or None
        """
        latest = db.query(PriceHistory).filter(
            PriceHistory.asin == asin
        ).order_by(PriceHistory.date.desc()).first()

        return latest if latest else None
