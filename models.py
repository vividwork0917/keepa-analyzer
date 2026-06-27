"""
SQLAlchemy ORM Models
"""
from sqlalchemy import Column, Integer, String, Decimal, DateTime, Date, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    jan = Column(String(13), unique=True, nullable=False, index=True)
    asin = Column(String(10), unique=True, nullable=False, index=True)
    product_name = Column(String(500), nullable=False)
    product_url = Column(String(1000))
    cost_price = Column(Decimal(10, 2), nullable=False)
    category = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    price_histories = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    profit_calculations = relationship("ProfitCalculation", back_populates="product", cascade="all, delete-orphan")
    rival_comparisons = relationship("RivalComparison", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(asin={self.asin}, jan={self.jan}, name={self.product_name})>"


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (
        Index("idx_product_date", "product_id", "date"),
        Index("idx_asin_date", "asin", "date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    asin = Column(String(10), index=True)
    date = Column(Date, nullable=False)
    amazon_price = Column(Decimal(10, 2))
    lowest_price = Column(Decimal(10, 2))
    new_offer_count = Column(Integer)
    used_offer_count = Column(Integer)
    bsr = Column(Integer)
    bsr_category = Column(String(100))
    rating = Column(Decimal(3, 2))
    review_count = Column(Integer)
    keepa_request_ts = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    product = relationship("Product", back_populates="price_histories")

    def __repr__(self):
        return f"<PriceHistory(asin={self.asin}, date={self.date}, price={self.amazon_price})>"


class FBACategory(Base):
    __tablename__ = "fba_categories"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(100), unique=True, nullable=False)
    fba_fee_rate = Column(Decimal(5, 2), nullable=False)
    shipping_cost = Column(Decimal(10, 2), nullable=False)
    storage_cost_small = Column(Decimal(10, 2))
    storage_cost_large = Column(Decimal(10, 2))
    weight_kg = Column(Decimal(10, 3))
    note = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<FBACategory(name={self.category_name}, fee_rate={self.fba_fee_rate}%)>"


class ProfitCalculation(Base):
    __tablename__ = "profit_calculations"
    __table_args__ = (
        Index("idx_calc_product_date", "product_id", "date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    selling_price = Column(Decimal(10, 2), nullable=False)
    cost_price = Column(Decimal(10, 2), nullable=False)
    fba_fee = Column(Decimal(10, 2), nullable=False)
    referral_fee = Column(Decimal(10, 2), nullable=False)
    variable_closing_fee = Column(Decimal(10, 2), nullable=False)
    shipping_cost = Column(Decimal(10, 2))
    profit = Column(Decimal(10, 2))
    profit_margin = Column(Decimal(5, 2))
    calculated_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    product = relationship("Product", back_populates="profit_calculations")

    def __repr__(self):
        return f"<ProfitCalculation(product_id={self.product_id}, date={self.date}, profit={self.profit})>"


class ImportRecord(Base):
    __tablename__ = "import_records"

    id = Column(Integer, primary_key=True, index=True)
    import_date = Column(DateTime, default=func.now())
    file_name = Column(String(255))
    total_rows = Column(Integer)
    success_count = Column(Integer)
    error_count = Column(Integer)
    status = Column(String(50))  # success, partial, failed
    error_log = Column(Text)
    processed_by = Column(String(100))

    def __repr__(self):
        return f"<ImportRecord(file={self.file_name}, status={self.status})>"


class RivalComparison(Base):
    __tablename__ = "rival_comparison"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    rival_asin = Column(String(10), nullable=False)
    rival_product_name = Column(String(500))
    comparison_date = Column(Date)
    our_price = Column(Decimal(10, 2))
    rival_price = Column(Decimal(10, 2))
    our_bsr = Column(Integer)
    rival_bsr = Column(Integer)
    our_rating = Column(Decimal(3, 2))
    rival_rating = Column(Decimal(3, 2))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    product = relationship("Product", back_populates="rival_comparisons")

    def __repr__(self):
        return f"<RivalComparison(our_asin={self.product_id}, rival_asin={self.rival_asin})>"
