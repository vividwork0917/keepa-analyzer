"""
Main FastAPI Application
Keepa Analyzer - Amazon Product Intelligence Tool
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import os

from config import CORS_ORIGINS, DEBUG
from database import get_db, init_db
from models import Product, PriceHistory, FBACategory
from schemas import ProductCreate, ProductResponse

# Initialize FastAPI app
app = FastAPI(
    title="Keepa Analyzer API",
    description="Amazon商品情報分析・比較ツール",
    version="1.0.0",
    debug=DEBUG
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Startup & Shutdown ====================
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("✅ Database initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Application shutting down")

# ==================== Health Check ====================
@app.get("/health")
async def health_check():
    """API health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "environment": "production" if not DEBUG else "development"
    }

# ==================== Products API ====================
@app.post("/api/products", response_model=ProductResponse)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Create a new product
    """
    # Check if product already exists
    existing = db.query(Product).filter(
        (Product.asin == product.asin) | (Product.jan == product.jan)
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Product with this ASIN or JAN already exists"
        )

    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/api/products", response_model=list)
async def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all products with pagination
    """
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

@app.get("/api/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Get product by ID
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get("/api/products/asin/{asin}", response_model=ProductResponse)
async def get_product_by_asin(asin: str, db: Session = Depends(get_db)):
    """
    Get product by ASIN
    """
    product = db.query(Product).filter(Product.asin == asin).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# ==================== Price History API ====================
@app.get("/api/prices/{asin}")
async def get_price_history(asin: str, period: str = "30d", db: Session = Depends(get_db)):
    """
    Get price history for a product (30d, 90d, 1y)
    """
    if period not in ["30d", "90d", "1y"]:
        raise HTTPException(status_code=400, detail="Invalid period. Use: 30d, 90d, 1y")

    prices = db.query(PriceHistory).filter(
        PriceHistory.asin == asin
    ).order_by(PriceHistory.date).all()

    if not prices:
        raise HTTPException(status_code=404, detail="Price history not found")

    return {
        "asin": asin,
        "period": period,
        "data": prices,
        "count": len(prices)
    }

# ==================== FBA Categories API ====================
@app.get("/api/fba-categories")
async def list_fba_categories(db: Session = Depends(get_db)):
    """
    List all FBA fee categories
    """
    categories = db.query(FBACategory).all()
    return categories

@app.get("/api/fba-categories/{category_name}")
async def get_fba_category(category_name: str, db: Session = Depends(get_db)):
    """
    Get FBA category by name
    """
    category = db.query(FBACategory).filter(
        FBACategory.category_name == category_name
    ).first()

    if not category:
        raise HTTPException(status_code=404, detail="FBA category not found")

    return category

# ==================== Dashboard API ====================
@app.get("/api/dashboard")
async def get_dashboard(db: Session = Depends(get_db)):
    """
    Get dashboard summary
    """
    total_products = db.query(Product).count()

    if total_products == 0:
        return {
            "total_products": 0,
            "total_profit_30d": 0,
            "avg_profit_margin_30d": 0,
            "products": [],
            "top_performers": []
        }

    return {
        "total_products": total_products,
        "message": "Dashboard implementation pending - Keepa API integration required",
        "status": "building"
    }

# ==================== Info ====================
@app.get("/api/info")
async def get_info():
    """
    Get API information
    """
    return {
        "name": "Keepa Analyzer API",
        "version": "1.0.0",
        "description": "Amazon商品情報分析・比較ツール",
        "endpoints": {
            "products": "/api/products",
            "prices": "/api/prices/{asin}",
            "fba": "/api/fba-categories",
            "dashboard": "/api/dashboard"
        }
    }

# ==================== Root ====================
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Keepa Analyzer API is running",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
