"""
Excel/CSV Import Handler
Handles importing product data from Excel/CSV files
Expected columns: JAN, 納品価格 (Cost Price), 商品URL, ASIN
"""
import logging
import pandas as pd
from typing import Tuple, List, Dict, Optional
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from models import Product, ImportRecord
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class ExcelHandler:
    """Handle Excel/CSV file imports"""

    # Expected column mappings
    COLUMN_MAPPINGS = {
        'jan': ['jan', 'JAN', 'jan_code', 'barcode'],
        'cost_price': ['納品価格', '原価', 'cost_price', 'cost', '単価'],
        'product_url': ['商品URL', 'url', 'product_url', 'URL'],
        'asin': ['ASIN', 'asin'],
    }

    def __init__(self):
        self.required_columns = ['asin', 'jan', 'cost_price']
        self.optional_columns = ['product_url']

    def _normalize_column_name(self, col_name: str) -> Optional[str]:
        """
        Map Excel column name to standard field name

        Args:
            col_name: Column name from Excel

        Returns:
            Normalized field name or None
        """
        for field, aliases in self.COLUMN_MAPPINGS.items():
            if col_name in aliases or col_name.strip() in aliases:
                return field
            # Try case-insensitive matching
            if col_name.lower() in [a.lower() for a in aliases]:
                return field

        return None

    def read_excel_file(self, file_path: str) -> Tuple[Optional[pd.DataFrame], List[str]]:
        """
        Read Excel or CSV file

        Args:
            file_path: Path to Excel/CSV file

        Returns:
            Tuple of (DataFrame or None, list of errors)
        """
        errors = []

        try:
            if not Path(file_path).exists():
                errors.append(f"File not found: {file_path}")
                return None, errors

            # Detect file type
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                errors.append("Unsupported file format. Use CSV or Excel (.xlsx/.xls)")
                return None, errors

            if df.empty:
                errors.append("Excel file is empty")
                return None, errors

            # Normalize column names
            normalized_df = pd.DataFrame()
            for col in df.columns:
                normalized_name = self._normalize_column_name(str(col))
                if normalized_name:
                    normalized_df[normalized_name] = df[col]

            # Check required columns
            missing_cols = [c for c in self.required_columns if c not in normalized_df.columns]
            if missing_cols:
                errors.append(f"Missing required columns: {', '.join(missing_cols)}")
                return None, errors

            logger.info(f"Successfully read Excel file: {len(normalized_df)} rows")
            return normalized_df, errors

        except Exception as e:
            logger.error(f"Error reading Excel file: {str(e)}")
            errors.append(f"Error reading file: {str(e)}")
            return None, errors

    def validate_row(self, row: Dict, row_num: int) -> Tuple[bool, Optional[Dict], str]:
        """
        Validate a single data row

        Args:
            row: Row data as dict
            row_num: Row number for error reporting

        Returns:
            Tuple of (is_valid, cleaned_data, error_message)
        """
        cleaned = {}
        errors = []

        try:
            # Validate ASIN
            asin = str(row.get('asin', '')).strip().upper()
            if not asin or len(asin) != 10:
                errors.append(f"Invalid ASIN: {asin}")
            else:
                cleaned['asin'] = asin

            # Validate JAN
            jan = str(row.get('jan', '')).strip()
            if not jan:
                errors.append("JAN is required")
            else:
                cleaned['jan'] = jan

            # Validate cost price
            try:
                cost_price = Decimal(str(row.get('cost_price', 0)).replace('¥', '').replace(',', ''))
                if cost_price <= 0:
                    errors.append(f"Cost price must be positive: {cost_price}")
                else:
                    cleaned['cost_price'] = cost_price
            except:
                errors.append(f"Invalid cost price: {row.get('cost_price')}")

            # Optional: product URL
            if 'product_url' in row and row['product_url']:
                cleaned['product_url'] = str(row['product_url']).strip()
            else:
                cleaned['product_url'] = None

            if errors:
                return False, None, f"Row {row_num}: {'; '.join(errors)}"

            return True, cleaned, ""

        except Exception as e:
            return False, None, f"Row {row_num}: {str(e)}"

    def import_products(
        self,
        file_path: str,
        db: Session,
        callback=None
    ) -> Tuple[int, int, int, List[str]]:
        """
        Import products from Excel file to database

        Args:
            file_path: Path to Excel/CSV file
            db: Database session
            callback: Optional progress callback (current, total, message)

        Returns:
            Tuple of (total_rows, success_count, error_count, error_list)
        """
        # Read file
        df, read_errors = self.read_excel_file(file_path)
        if df is None:
            return 0, 0, 0, read_errors

        total_rows = len(df)
        success_count = 0
        error_count = 0
        errors_list = []

        # Process each row
        for idx, (_, row) in enumerate(df.iterrows()):
            row_num = idx + 2  # +2 because headers are row 1

            if callback:
                callback(idx + 1, total_rows, f"Processing row {row_num}")

            # Validate row
            is_valid, cleaned_data, error_msg = self.validate_row(row.to_dict(), row_num)

            if not is_valid:
                error_count += 1
                errors_list.append(error_msg)
                logger.warning(error_msg)
                continue

            try:
                # Check if product already exists
                existing = db.query(Product).filter(
                    (Product.asin == cleaned_data['asin']) |
                    (Product.jan == cleaned_data['jan'])
                ).first()

                if existing:
                    errors_list.append(
                        f"Row {row_num}: Product already exists (ASIN: {cleaned_data['asin']})"
                    )
                    error_count += 1
                    logger.info(f"Product already exists: {cleaned_data['asin']}")
                    continue

                # Create new product
                new_product = Product(
                    jan=cleaned_data['jan'],
                    asin=cleaned_data['asin'],
                    product_name=f"ASIN: {cleaned_data['asin']}",  # Placeholder
                    product_url=cleaned_data.get('product_url'),
                    cost_price=cleaned_data['cost_price'],
                    category='Unknown'  # Will be updated from Keepa
                )

                db.add(new_product)
                db.commit()
                db.refresh(new_product)

                success_count += 1
                logger.info(f"Imported product: ASIN={cleaned_data['asin']}, JAN={cleaned_data['jan']}")

            except Exception as e:
                error_count += 1
                errors_list.append(f"Row {row_num}: Database error - {str(e)}")
                db.rollback()
                logger.error(f"Error inserting row {row_num}: {str(e)}")

        # Save import record
        self._save_import_record(
            file_path, total_rows, success_count, error_count, errors_list, db
        )

        return total_rows, success_count, error_count, errors_list

    def _save_import_record(
        self,
        file_name: str,
        total_rows: int,
        success_count: int,
        error_count: int,
        error_log: List[str],
        db: Session
    ):
        """Save import record to database"""
        try:
            record = ImportRecord(
                file_name=Path(file_name).name,
                total_rows=total_rows,
                success_count=success_count,
                error_count=error_count,
                status='success' if error_count == 0 else 'partial' if success_count > 0 else 'failed',
                error_log='\n'.join(error_log[:100]) if error_log else None,  # Limit log size
                processed_by='system'
            )
            db.add(record)
            db.commit()
            logger.info(f"Saved import record: {success_count}/{total_rows} successful")
        except Exception as e:
            logger.error(f"Error saving import record: {str(e)}")
            db.rollback()

    def export_products_template(self, output_path: str) -> bool:
        """
        Export template Excel file for product import

        Args:
            output_path: Path to save template

        Returns:
            True if successful
        """
        try:
            template_data = {
                'ASIN': ['B123456789', 'B123456790'],
                'JAN': ['4589123456789', '4589123456790'],
                '納品価格': [1500, 2500],
                '商品URL': ['https://amazon.co.jp/dp/B123456789', 'https://amazon.co.jp/dp/B123456790']
            }

            df = pd.DataFrame(template_data)
            df.to_excel(output_path, index=False, engine='openpyxl')

            logger.info(f"Template exported: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting template: {str(e)}")
            return False
