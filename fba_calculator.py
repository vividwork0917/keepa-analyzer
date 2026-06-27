"""
FBA Cost & Profit Calculator
Calculates profit margins considering all Amazon seller fees
"""
import logging
from typing import Optional, Dict
from decimal import Decimal
from datetime import date
from config import AMAZON_REFERRAL_FEE_RATE
from models import FBACategory, Product, ProfitCalculation
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class FBACalculator:
    """Calculate FBA fees and profit margins"""

    # Amazon's variable closing fee (varies by category)
    VARIABLE_CLOSING_FEES = {
        'Media': Decimal('0.45'),  # Books, Music, DVDs
        'Electronics': Decimal('0.00'),
        'Clothing': Decimal('2.00'),
        'Jewelry': Decimal('0.00'),
        'Sports': Decimal('0.00'),
        'Default': Decimal('0.00')
    }

    # FBA fulfillment fees by weight (Small Standard-Size)
    WEIGHT_FEE_TIERS = [
        (0.0, 0.25, Decimal('2.41')),      # 0-250g
        (0.25, 0.5, Decimal('2.41')),      # 250-500g
        (0.5, 1.0, Decimal('2.41')),       # 500g-1kg
        (1.0, 2.0, Decimal('3.87')),       # 1-2kg
        (2.0, 20.0, Decimal('4.79')),      # 2-20kg (add 0.38 per kg over 2kg)
    ]

    def __init__(self):
        self.referral_fee_rate = Decimal(str(AMAZON_REFERRAL_FEE_RATE))

    def get_referral_fee(self, category: str, selling_price: Decimal) -> Decimal:
        """
        Calculate referral fee based on category

        Args:
            category: Amazon category
            selling_price: Product selling price

        Returns:
            Referral fee amount
        """
        # Most categories are 15%, some are different
        category_specific_rates = {
            'Jewelry': Decimal('0.20'),
            'Watches': Decimal('0.20'),
            'Fine Art': Decimal('0.05'),
            'Industrial Supplies': Decimal('0.08'),
        }

        rate = category_specific_rates.get(category, self.referral_fee_rate)
        return selling_price * rate

    def get_variable_closing_fee(self, category: str) -> Decimal:
        """
        Get variable closing fee for category

        Args:
            category: Amazon category

        Returns:
            Variable closing fee
        """
        for key, fee in self.VARIABLE_CLOSING_FEES.items():
            if key.lower() in category.lower():
                return fee
        return self.VARIABLE_CLOSING_FEES['Default']

    def get_fba_fee(
        self,
        category: str,
        weight_kg: Optional[Decimal] = None,
        db: Optional[Session] = None
    ) -> Decimal:
        """
        Calculate FBA fulfillment fee

        Args:
            category: Amazon category
            weight_kg: Product weight in kg
            db: Database session to fetch category config

        Returns:
            FBA fee amount
        """
        if db:
            fba_cat = db.query(FBACategory).filter(
                FBACategory.category_name == category
            ).first()
            if fba_cat:
                return fba_cat.shipping_cost  # Using configured shipping cost as FBA fee

        # Default FBA fee calculation
        # Small Standard-Size items
        if weight_kg is None:
            weight_kg = Decimal('0.5')

        weight_kg = Decimal(str(weight_kg))

        # Calculate based on weight tier
        for min_w, max_w, base_fee in self.WEIGHT_FEE_TIERS:
            if min_w <= weight_kg < max_w:
                if weight_kg > Decimal('2.0'):
                    # Add extra fee for weight over 2kg
                    extra_weight = weight_kg - Decimal('2.0')
                    return base_fee + (extra_weight * Decimal('0.38'))
                return base_fee

        # Over 20kg (Large Standard-Size)
        return Decimal('12.86')

    def calculate_profit(
        self,
        selling_price: Decimal,
        cost_price: Decimal,
        category: str,
        weight_kg: Optional[Decimal] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Decimal]:
        """
        Calculate profit and all associated fees

        Args:
            selling_price: Amazon selling price
            cost_price: Product cost/acquisition price
            category: Amazon category
            weight_kg: Product weight in kg
            db: Database session

        Returns:
            Dict with all cost breakdown
        """
        selling_price = Decimal(str(selling_price))
        cost_price = Decimal(str(cost_price))

        # Calculate fees
        referral_fee = self.get_referral_fee(category, selling_price)
        variable_closing_fee = self.get_variable_closing_fee(category)
        fba_fee = self.get_fba_fee(category, weight_kg, db)

        # Get shipping cost from DB if available
        shipping_cost = Decimal('0')
        if db:
            fba_cat = db.query(FBACategory).filter(
                FBACategory.category_name == category
            ).first()
            if fba_cat:
                shipping_cost = fba_cat.shipping_cost

        # Calculate profit
        total_fees = referral_fee + variable_closing_fee + fba_fee + shipping_cost
        profit = selling_price - cost_price - total_fees

        # Calculate profit margin
        profit_margin = (profit / selling_price * Decimal('100')) if selling_price > 0 else Decimal('0')

        return {
            'selling_price': selling_price,
            'cost_price': cost_price,
            'referral_fee': referral_fee,
            'variable_closing_fee': variable_closing_fee,
            'fba_fee': fba_fee,
            'shipping_cost': shipping_cost,
            'total_fees': total_fees,
            'profit': profit,
            'profit_margin': profit_margin.quantize(Decimal('0.01'))
        }

    def save_profit_calculation(
        self,
        product_id: int,
        calculation_date: date,
        selling_price: Decimal,
        cost_price: Decimal,
        category: str,
        weight_kg: Optional[Decimal] = None,
        db: Optional[Session] = None
    ) -> Optional[ProfitCalculation]:
        """
        Calculate and save profit calculation to database

        Args:
            product_id: Product ID
            calculation_date: Date of calculation
            selling_price: Selling price
            cost_price: Cost price
            category: Product category
            weight_kg: Weight in kg
            db: Database session

        Returns:
            ProfitCalculation record or None
        """
        if not db:
            return None

        try:
            # Calculate profit breakdown
            breakdown = self.calculate_profit(
                selling_price, cost_price, category, weight_kg, db
            )

            # Create new profit calculation record
            record = ProfitCalculation(
                product_id=product_id,
                date=calculation_date,
                selling_price=breakdown['selling_price'],
                cost_price=breakdown['cost_price'],
                fba_fee=breakdown['fba_fee'],
                referral_fee=breakdown['referral_fee'],
                variable_closing_fee=breakdown['variable_closing_fee'],
                shipping_cost=breakdown['shipping_cost'],
                profit=breakdown['profit'],
                profit_margin=breakdown['profit_margin']
            )

            db.add(record)
            db.commit()
            db.refresh(record)

            logger.info(f"Saved profit calculation for product {product_id}: ¥{breakdown['profit']}")
            return record

        except Exception as e:
            logger.error(f"Error saving profit calculation: {str(e)}")
            db.rollback()
            return None

    def get_breakeven_price(
        self,
        cost_price: Decimal,
        category: str,
        weight_kg: Optional[Decimal] = None,
        db: Optional[Session] = None
    ) -> Decimal:
        """
        Calculate breakeven selling price

        Args:
            cost_price: Product cost
            category: Amazon category
            weight_kg: Weight in kg
            db: Database session

        Returns:
            Minimum selling price to break even
        """
        cost_price = Decimal(str(cost_price))

        # Estimate average fees (as percentage of selling price)
        # Typically 15% referral + FBA + other = ~25-30% total

        # Approximate calculation
        # Profit = Selling_Price - Cost - (Selling_Price * fee_rate)
        # For breakeven: Profit = 0
        # Cost = Selling_Price * (1 - fee_rate)
        # Selling_Price = Cost / (1 - fee_rate)

        estimated_fee_rate = Decimal('0.25')  # 25% average
        breakeven_price = cost_price / (Decimal('1') - estimated_fee_rate)

        return breakeven_price.quantize(Decimal('0.01'))

    def get_target_price_for_margin(
        self,
        cost_price: Decimal,
        target_margin_percent: Decimal,
        category: str,
        weight_kg: Optional[Decimal] = None,
        db: Optional[Session] = None
    ) -> Decimal:
        """
        Calculate selling price needed to achieve target profit margin

        Args:
            cost_price: Product cost
            target_margin_percent: Target profit margin %
            category: Amazon category
            weight_kg: Weight in kg
            db: Database session

        Returns:
            Required selling price
        """
        cost_price = Decimal(str(cost_price))
        target_margin = Decimal(str(target_margin_percent))

        # Estimate fee rate
        # Typically 25-30% of selling price
        estimated_fee_rate = Decimal('0.27')

        # Target_Profit = Selling_Price * (target_margin / 100)
        # Selling_Price - Cost - (Selling_Price * fee_rate) = Target_Profit
        # Selling_Price * (1 - fee_rate - margin%) = Cost
        # Solving: Selling_Price = Cost / (1 - fee_rate - margin%)

        margin_rate = target_margin / Decimal('100')
        denominator = Decimal('1') - estimated_fee_rate - margin_rate

        if denominator <= 0:
            return cost_price * Decimal('2')  # Fallback

        required_price = cost_price / denominator
        return required_price.quantize(Decimal('0.01'))
