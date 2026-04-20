from fastapi import APIRouter, HTTPException
from datetime import date, timedelta
from typing import List
from models.shopify_models import OrderModel, OrderItem
from services import shopify_service

router = APIRouter(prefix="/shopify", tags=["Shopify"])

@router.get("/products")
async def get_products():
    """Fetch all products from Shopify store."""
    try:
        products = await shopify_service.get_all_products()
        return {
            "count":    len(products),
            "products": products
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
async def get_orders(
    start_date: date = date.today() - timedelta(days=30),
    end_date:   date = date.today()
):
    """Fetch all orders in a date range."""
    try:
        orders = await shopify_service.get_orders(start_date, end_date)
        result = []
        for o in orders:
            items = [
                OrderItem(
                    product_id = str(li.get("product_id", "")),
                    title      = li.get("title", ""),
                    quantity   = li.get("quantity", 0),
                    price      = float(li.get("price", 0)),
                    revenue    = float(li.get("price", 0)) * li.get("quantity", 0),
                )
                for li in o.get("line_items", [])
            ]
            result.append(OrderModel(
                id               = str(o["id"]),
                created_at       = o["created_at"],
                financial_status = o.get("financial_status", ""),
                total_price      = float(o.get("total_price", 0)),
                line_items       = items,
            ))
        return {"count": len(result), "orders": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sales")
def get_sales_summary(
    start_date: date = date.today() - timedelta(days=30),
    end_date:   date = date.today()
):
    """Get sales aggregated by product."""
    try:
        sales = shopify_service.get_sales_by_product(start_date, end_date)
        return {
            "period":   f"{start_date} → {end_date}",
            "count":    len(sales),
            "sales":    list(sales.values()),
            "totals": {
                "units_sold":  sum(s["units_sold"] for s in sales.values()),
                "revenue":     round(sum(s["revenue"] for s in sales.values()), 2),
                "order_count": sum(s["order_count"] for s in sales.values()),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sales/timeseries/{product_id}")
def get_sales_timeseries(
    product_id: str,
    start_date: date = date.today() - timedelta(days=30),
    end_date:   date = date.today()
):
    """Get day-by-day sales for a specific product."""
    try:
        ts = shopify_service.get_daily_sales_timeseries(product_id, start_date, end_date)
        return {
            "product_id": product_id,
            "period":     f"{start_date} → {end_date}",
            "days":       len(ts),
            "timeseries": ts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
