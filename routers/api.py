from fastapi import APIRouter, HTTPException
from datetime import date, timedelta
from typing import List

from models.schemas import (
    ConnectionStatus, ProductModel, OrderModel, OrderItem,
    CampaignMetrics, AnalyticsResponse, OverviewStats,
    ProductSalesSummary, TopAction, AnalyticsRequest
)
from services import shopify_service, woocommerce_service, meta_service, analytics_service
from services.shop_context import get_shop_data

router = APIRouter()

def get_platform_service(shop: str):
    ctx = get_shop_data(shop)
    if ctx.get("platform") == "woocommerce":
        return woocommerce_service
    return shopify_service


# ═══════════════════════════════════════════════════════════════════════
# HEALTH & CONNECTION
# ═══════════════════════════════════════════════════════════════════════

@router.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Shopify × Meta Analytics API is running"}


@router.get("/connections", response_model=ConnectionStatus, tags=["Health"])
def test_connections():
    errors = []

    shopify = shopify_service.test_connection()
    meta    = meta_service.test_connection()

    if not shopify.get("connected"):
        errors.append(f"Shopify: {shopify.get('error', 'Unknown error')}")
    if not meta.get("connected"):
        errors.append(f"Meta: {meta.get('error', 'Unknown error')}")

    return ConnectionStatus(
        shopify=shopify.get("connected", False),
        meta=meta.get("connected", False),
        shopify_store=shopify.get("store"),
        shopify_currency=shopify.get("currency"),
        meta_user=meta.get("user"),
        meta_ad_account=meta.get("ad_account"),
        errors=errors,
    )


# ═══════════════════════════════════════════════════════════════════════
# PRODUCTS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/{platform}/products", tags=["Platform"])
def get_products(platform: str, shop: str):
    try:
        service = get_platform_service(shop)
        products = service.get_all_products(shop)
        return {"count": len(products), "products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# ORDERS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/{platform}/orders", tags=["Platform"])
def get_orders(
    platform: str,
    shop: str,
    start_date: date = date.today() - timedelta(days=30),
    end_date: date = date.today()
):
    try:
        service = get_platform_service(shop)
        orders = service.get_orders(shop, start_date, end_date)

        result = []
        for o in orders:
            items = [
                OrderItem(
                    product_id=str(li.get("product_id", "")),
                    title=li.get("title", ""),
                    quantity=li.get("quantity", 0),
                    price=float(li.get("price", 0)),
                    revenue=float(li.get("price", 0)) * li.get("quantity", 0),
                )
                for li in o.get("line_items", [])
            ]

            result.append(OrderModel(
                id=str(o["id"]),
                created_at=o["created_at"],
                financial_status=o.get("financial_status", ""),
                total_price=float(o.get("total_price", 0)),
                line_items=items,
            ))

        return {"count": len(result), "orders": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# SALES
# ═══════════════════════════════════════════════════════════════════════

@router.get("/{platform}/sales", tags=["Platform"])
def get_sales_summary(
    platform: str,
    shop: str,
    start_date: date = date.today() - timedelta(days=30),
    end_date: date = date.today()
):
    try:
        service = get_platform_service(shop)
        sales = service.get_sales_by_product(shop, start_date, end_date)

        return {
            "period": f"{start_date} → {end_date}",
            "count": len(sales),
            "sales": list(sales.values()),
            "totals": {
                "units_sold": sum(s["units_sold"] for s in sales.values()),
                "revenue": round(sum(s["revenue"] for s in sales.values()), 2),
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/shop-profile", tags=["Platform"])
def get_shop_profile(platform: str, shop: str):
    from database.db import SessionLocal
    from models.shop_model import Shop
    
    db = SessionLocal()
    try:
        data = db.query(Shop).filter(Shop.shop_domain == shop).first()
        if not data:
            raise HTTPException(404, "Shop profile not found")
        
        return {
            "name": data.shop_name or data.shop_domain,
            "email": data.email,
            "currency": data.currency,
            "domain": data.shop_domain
        }
    finally:
        db.close()


@router.get("/{platform}/sales-intelligence", tags=["Platform"])
def get_sales_intelligence(platform: str, shop: str):
    try:
        service = get_platform_service(shop)
        summary = service.get_intelligence_summary(shop)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/top-products", tags=["Platform"])
def get_top_products(platform: str, shop: str, limit: int = 5):
    try:
        service = get_platform_service(shop)
        products = service.get_top_performing_products(shop, limit)
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
@router.get("/{platform}/margin-intelligence", tags=["Platform"])
def get_margin_intel(platform: str, shop: str):
    try:
        service = get_platform_service(shop)
        data = service.get_margin_intelligence(shop)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/inventory-intelligence", tags=["Platform"])
def get_inventory_intel(platform: str, shop: str):
    try:
        service = get_platform_service(shop)
        data = service.get_inventory_intelligence(shop)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# META — CAMPAIGNS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/meta/campaigns", tags=["Meta"])
def get_campaigns():
    try:
        campaigns = meta_service.get_all_campaigns()
        return {"count": len(campaigns), "campaigns": campaigns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# ANALYTICS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/{platform}/analytics", tags=["Platform"])
def get_analytics(
    platform: str,
    shop: str,
    start_date: date = date.today() - timedelta(days=30),
    end_date: date = date.today()
):
    try:
        service = get_platform_service(shop)
        sales_data = service.get_sales_by_product(shop, start_date, end_date)

        total_revenue = sum(s["revenue"] for s in sales_data.values())
        total_units = sum(s["units_sold"] for s in sales_data.values())

        campaigns = meta_service.get_all_campaigns()
        total_spend = 0.0

        for c in campaigns:
            insights = meta_service.get_campaign_insights(c["id"], start_date, end_date)
            total_spend += insights.get("spend", 0)

        return {
            "shop": shop,
            "revenue": total_revenue,
            "units_sold": total_units,
            "ad_spend": total_spend,
            "roas": round(total_revenue / total_spend, 2) if total_spend > 0 else 0
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# ANALYTICS OVERVIEW (MAIN API)
# ═══════════════════════════════════════════════════════════════════════

@router.get("/{platform}/analytics/overview", tags=["Platform"])
def get_analytics_overview(
    platform: str,
    shop: str,
    start_date: date = date.today() - timedelta(days=90),
    end_date: date = date.today()
):
    try:
        service = get_platform_service(shop)
        products = service.get_all_products(shop)
        sales = service.get_sales_by_product(shop, start_date, end_date)
        campaigns = meta_service.get_all_campaigns()

        total_revenue = sum(s["revenue"] for s in sales.values())
        total_units = sum(s["units_sold"] for s in sales.values())

        total_spend = 0
        for c in campaigns:
            insights = meta_service.get_campaign_insights(c["id"], start_date, end_date)
            total_spend += insights.get("spend", 0)

        return {
            "shop": shop,
            "summary": {
                "revenue": total_revenue,
                "units": total_units,
                "ad_spend": total_spend,
                "roas": round(total_revenue / total_spend, 2) if total_spend > 0 else 0
            },
            "products": products,
            "sales": list(sales.values()),
            "campaigns": campaigns
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))