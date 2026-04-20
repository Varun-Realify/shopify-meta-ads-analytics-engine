from fastapi import APIRouter, HTTPException
from datetime import date, timedelta
from typing import List
from services.woocommerce_service import woocommerce_service

router = APIRouter(tags=["WooCommerce"])

@router.get("/woocommerce/products")
async def get_products():
    """Fetch all products from WooCommerce."""
    try:
        return await woocommerce_service.get_all_products()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/woocommerce/orders")
async def get_orders(
    start_date: date = date.today() - timedelta(days=30),
    end_date: date = date.today()
):
    """Fetch orders from WooCommerce within a date range."""
    try:
        return await woocommerce_service.get_orders(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/woocommerce/test")
async def test_connection():
    """Test connection to WooCommerce."""
    return await woocommerce_service.test_connection()
