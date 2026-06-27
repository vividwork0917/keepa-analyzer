"""
Products API Router
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from database import get_db
from models import Product, PriceHistory, ProfitCalculation
from schemas import ProductCreate, ProductUpdate, ProductResponse, ProfitCalculationResponse
from keepa_service import KeepaAPIService
from fba_calculator import FBACalculator

router = APIRouter(prefix="/api/products", tags=["products"])

# Services
keepa_service = KeepaAPIService()
fba_calc = FBACalculator()

# ==================== Product CRUD ====================

@router.post("", response_model=ProductResponse)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    # Check if product exists
    existing = db.query(Product).filter(
        (Product.asin == product.asin) | (Product.jan == product.jan)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Product already exists")

    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return db_product


@router.get("", response_model=List[ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all products with pagination"""
    products = db.query(Product).offset(skip).limit(limit).all()
    return products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product by ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/asin/{asin}", response_model=ProductResponse)
async def get_product_by_asin(asin: str, db: Session = Depends(get_db)):
    """Get product by ASIN"""
    product = db.query(Product).filter(Product.asin == asin).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):
    """Update product details"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)

    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return db_product


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()

    return {"message": "Product deleted successfully"}


# ==================== Price History ====================

@router.get("/{product_id}/prices")
async def get_product_prices(
    product_id: int,
    period: str = Query("30d", regex="^(30d|90d|1y)$"),
    db: Session = Depends(get_db)
):
    """Get price history for product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Calculate date range
    end_date = datetime.now().date()
    if period == "30d":
        start_date = end_date - timedelta(days=30)
    elif period == "90d":
        start_date = end_date - timedelta(days=90)
    else:  # 1y
        start_date = end_date - timedelta(days=365)

    prices = db.query(PriceHistory).filter(
        (PriceHistory.product_id == product_id) &
        (PriceHistory.date >= start_date) &
        (PriceHistory.date <= end_date)
    ).order_by(PriceHistory.date).all()

    return {
        "product_id": product_id,
        "asin": product.asin,
        "period": period,
        "data": prices,
        "count": len(prices)
    }


# ==================== Keepa Sync ====================

@router.post("/{product_id}/sync-keepa")
async def sync_product_from_keepa(product_id: int, db: Session = Depends(get_db)):
    """Fetch latest data from Keepa API for product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    success = keepa_service.fetch_and_store_product(product.id, product.asin, db)

    if success:
        return {
            "message": f"Successfully synced product {product.asin}",
            "product_id": product_id
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to sync with Keepa API")


@router.post("/sync-all")
async def sync_all_products(db: Session = Depends(get_db)):
    """Sync all products from Keepa API"""
    products = db.query(Product).all()
    asins = [p.asin for p in products]

    results = keepa_service.bulk_fetch_products(asins, db)

    success_count = sum(1 for v in results.values() if v)
    return {
        "total": len(asins),
        "success": success_count,
        "failed": len(asins) - success_count,
        "details": results
    }


# ==================== Profit Calculation ====================

@router.post("/{product_id}/calculate-profit", response_model=ProfitCalculationResponse)
async def calculate_profit(
    product_id: int,
    selling_price: float,
    db: Session = Depends(get_db)
):
    """Calculate profit for product at given selling price"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    record = fba_calc.save_profit_calculation(
        product_id=product_id,
        calculation_date=datetime.now().date(),
        selling_price=selling_price,
        cost_price=float(product.cost_price),
        category=product.category,
        db=db
    )

    if not record:
        raise HTTPException(status_code=500, detail="Failed to calculate profit")

    return record


@router.get("/{product_id}/profit-history")
async def get_profit_history(
    product_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get profit calculation history"""
    start_date = datetime.now().date() - timedelta(days=days)

    calcs = db.query(ProfitCalculation).filter(
        (ProfitCalculation.product_id == product_id) &
        (ProfitCalculation.date >= start_date)
    ).order_by(ProfitCalculation.date).all()

    return {
        "product_id": product_id,
        "period_days": days,
        "data": calcs,
        "count": len(calcs)
    }


@router.get("/{product_id}/breakeven-price")
async def get_breakeven_price(product_id: int, db: Session = Depends(get_db)):
    """Get breakeven selling price for product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    breakeven = fba_calc.get_breakeven_price(
        cost_price=product.cost_price,
        category=product.category,
        db=db
    )

    return {
        "product_id": product_id,
        "cost_price": float(product.cost_price),
        "breakeven_price": float(breakeven)
    }


@router.get("/{product_id}/target-price")
async def get_target_price(
    product_id: int,
    target_margin: float = Query(20, ge=0, le=100),
    db: Session = Depends(get_db)
):
    """Get required selling price for target profit margin"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    target_price = fba_calc.get_target_price_for_margin(
        cost_price=product.cost_price,
        target_margin_percent=target_margin,
        category=product.category,
        db=db
    )

    return {
        "product_id": product_id,
        "cost_price": float(product.cost_price),
        "target_margin_percent": target_margin,
        "required_selling_price": float(target_price)
    }
