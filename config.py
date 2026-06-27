"""
Configuration module for Keepa Analyzer
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/keepa_analyzer")

# Keepa API
KEEPA_API_KEY = os.getenv("KEEPA_API_KEY", "7j94dv0omf10s7q1qimr0poe29pv941qs7432pu6ibco03gjsh9r39117pta992q")
KEEPA_API_BASE_URL = "https://api.keepa.com"

# App Settings
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

# File Upload
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Amazon Settings
AMAZON_REFERRAL_FEE_RATE = 0.15  # Default 15%

# Request Settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
