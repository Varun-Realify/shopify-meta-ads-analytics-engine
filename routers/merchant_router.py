from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
import logging
from services import google_merchant_service
from core.config import Config

router = APIRouter(prefix="/merchant", tags=["merchant"])

@router.get("/google/benchmarks")
async def get_google_benchmarks():
    """
    The Professional Method: Uses Google Merchant API for market-wide price benchmarks.
    Requires GOOGLE_SERVICE_ACCOUNT_JSON_PATH and GOOGLE_MERCHANT_ID in .env
    """
    if not Config.GOOGLE_MERCHANT_ID:
        raise HTTPException(status_code=400, detail="Google Merchant ID not configured.")
    
    try:
        # 1. Fetch products from GMC
        my_gmc_products = google_merchant_service.get_my_products(Config.GOOGLE_MERCHANT_ID)
        product_ids = [p["id"] for p in my_gmc_products]
        
        # 2. Get benchmarks from GMC
        benchmarks = google_merchant_service.get_price_benchmarks(Config.GOOGLE_MERCHANT_ID, product_ids)
        
        for p in my_gmc_products:
            p["market_benchmark"] = benchmarks.get(p["id"], {}).get("price_benchmark")
            p["competitiveness"] = benchmarks.get(p["id"], {}).get("competitiveness")
            
        return {
            "merchant_id": Config.GOOGLE_MERCHANT_ID,
            "products": my_gmc_products,
            "source": "Google Merchant API"
        }
    except Exception as e:
        logging.error(f"GMC Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Google API Error: {str(e)}")

