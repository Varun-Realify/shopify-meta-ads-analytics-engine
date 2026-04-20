from fastapi import APIRouter, HTTPException
from datetime import date, timedelta
from services.localwp_service import localwp_service

router = APIRouter(tags=["LocalWP"])

@router.get("/localwp/products")
async def get_products():
    """Fetch all products from LocalWP."""
    try:
        return await localwp_service.get_all_products()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/localwp/orders")
async def get_orders(
    start_date: date = date.today() - timedelta(days=30),
    end_date: date = date.today()
):
    """Fetch orders from LocalWP within a date range."""
    try:
        return await localwp_service.get_orders(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/localwp/test")
async def test_connection():
    """Test connection to LocalWP."""
    return await localwp_service.test_connection()
