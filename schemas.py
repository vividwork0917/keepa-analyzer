"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

# ==================== Product ====================
class ProductBase(BaseModel):
    jan: str
    asin: str
    product_name: str
    product_url: Optional[str] = None
    cost_price: Decimal
    category: str

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    product_url: Optional[str] = None
    cost_price: Optional[Decimal] = None
    category: Optional[str] = None

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Price History ====================
class PriceHistoryBase(BaseModel):
    asin: str
    date: date
    amazon_price: Optional[Decimal] = None
    lowest_price: Optional[Decimal] = None
    new_offer_count: Optional[int] = None
    used_offer_count: Optional[int] = None
    bsr: Optional[int] = None
    bsr_category: Optional[str] = None
    rating: Optional[Decimal] = None
    review_count: Optional[int] = None

class PriceHistoryCreate(PriceHistoryBase):
    product_id: int

class PriceHistoryResponse(PriceHistoryBase):
    id: int
    product_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== FBA Category ====================
class FBACategoryBase(BaseModel):
    category_name: str
    fba_fee_rate: Decimal
    shipping_cost: Decimal
    storage_cost_small: Optional[Decimal] = None
    storage_cost_large: Optional[Decimal] = None
    weight_kg: Optional[Decimal] = None
    note: Optional[str] = None

class FBACategoryCreate(FBACategoryBase):
    pass

class FBACategoryUpdate(BaseModel):
    fba_fee_rate: Optional[Decimal] = None
    shipping_cost: Optional[Decimal] = None
    storage_cost_small: Optional[Decimal] = None
    storage_cost_large: Optional[Decimal] = None

class FBACategoryResponse(FBACategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Profit Calculation ====================
class ProfitCalculationBase(BaseModel):
    date: date
    selling_price: Decimal
    cost_price: Decimal
    fba_fee: Decimal
    referral_fee: Decimal
    variable_closing_fee: Decimal
    shipping_cost: Optional[Decimal] = None
    profit: Optional[Decimal] = None
    profit_margin: Optional[Decimal] = None

class ProfitCalculationCreate(ProfitCalculationBase):
    product_id: int

class ProfitCalculationResponse(ProfitCalculationBase):
    id: int
    product_id: int
    calculated_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Import ====================
class ImportRecordResponse(BaseModel):
    id: int
    import_date: datetime
    file_name: str
    total_rows: int
    success_count: int
    error_count: int
    status: str
    error_log: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== Rival Comparison ====================
class RivalComparisonBase(BaseModel):
    rival_asin: str
    rival_product_name: Optional[str] = None
    comparison_date: Optional[date] = None
    our_price: Optional[Decimal] = None
    rival_price: Optional[Decimal] = None
    our_bsr: Optional[int] = None
    rival_bsr: Optional[int] = None
    our_rating: Optional[Decimal] = None
    rival_rating: Optional[Decimal] = None

class RivalComparisonCreate(RivalComparisonBase):
    product_id: int

class RivalComparisonResponse(RivalComparisonBase):
    id: int
    product_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Dashboard ====================
class PriceChartData(BaseModel):
    date: date
    amazon_price: Optional[Decimal]
    lowest_price: Optional[Decimal]
    bsr: Optional[int]
    rating: Optional[Decimal]

class PriceChartResponse(BaseModel):
    asin: str
    product_name: str
    period: str  # "30d", "90d", "1y"
    data: List[PriceChartData]

class ProductProfitSummary(BaseModel):
    product_id: int
    asin: str
    product_name: str
    latest_price: Optional[Decimal]
    latest_profit: Optional[Decimal]
    latest_profit_margin: Optional[Decimal]
    avg_profit_30d: Optional[Decimal]
    avg_bsr: Optional[int]
    latest_rating: Optional[Decimal]

class DashboardResponse(BaseModel):
    total_products: int
    total_profit_30d: Decimal
    avg_profit_margin_30d: Decimal
    products: List[ProductProfitSummary]
    top_performers: List[ProductProfitSummary]

class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
