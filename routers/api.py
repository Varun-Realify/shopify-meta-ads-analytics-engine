from fastapi import APIRouter, HTTPException
from datetime import date, timedelta
from typing import List
import asyncio

from models.schemas import (
    ConnectionStatus, ProductModel, OrderModel, OrderItem,
    CampaignMetrics, AnalyticsResponse, OverviewStats,
    ProductSalesSummary, TopAction, AnalyticsRequest
)
from services import shopify_service, meta_service, analytics_service, woocommerce_service

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
#  HEALTH & CONNECTION
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "Shopify × Meta Analytics API is running"}


@router.get("/connections", response_model=ConnectionStatus, tags=["Health"])
async def test_connections():
    """Test Shopify, Meta, and WooCommerce API connections."""
    errors = []

    results = await asyncio.gather(
        shopify_service.test_connection(),
        meta_service.test_connection(),
        woocommerce_service.test_connection()
    )
    
    shopify, meta, woo = results

    if not shopify.get("connected"):
        errors.append(f"Shopify: {shopify.get('error', 'Unknown error')}")
    if not meta.get("connected"):
        errors.append(f"Meta: {meta.get('error', 'Unknown error')}")
    if not woo.get("connected"):
        errors.append(f"WooCommerce: {woo.get('error', 'Unknown error')}")

    from core.config import Config
    return ConnectionStatus(
        shopify           = shopify.get("connected", False),
        meta              = meta.get("connected", False),
        woocommerce       = woo.get("connected", False),
        shopify_store     = shopify.get("store"),
        shopify_currency  = shopify.get("currency"),
        meta_user         = meta.get("user"),
        meta_ad_account   = meta.get("ad_account"),
        woo_url           = Config.WOO_URL,
        errors            = errors,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  CATALOG & AUTOMATION
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/meta/catalog/sync", tags=["Meta"])
async def sync_shopify_to_meta():
    """Sync all Shopify products to Meta Catalog."""
    try:
        products = await shopify_service.get_all_products()
        results = []
        for p in products:
            res = await meta_service.create_catalog_product(
                name=p["title"],
                description=f"Shopify product {p['title']}",
                link=f"https://{shopify_service.Config.SHOPIFY_STORE_NAME}/products/{p['id']}",
                image_url="", 
                price=p["selling_price"],
                brand=p.get("vendor", "Generic")
            )
            results.append({"product": p["title"], "status": res})
        return {"total_synced": len(results), "details": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/shopify/products", tags=["Shopify"])
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


# ═══════════════════════════════════════════════════════════════════════════════
#  SHOPIFY — ORDERS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/shopify/orders", tags=["Shopify"])
async def get_shopify_orders(
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


@router.get("/realtime/cross-check", tags=["Realtime"])
async def cross_check_realtime(minutes: int = 60):
    """
    Cross-checks Shopify orders in the last 'minutes' with Meta Ad performance.
    """
    try:
        shopify_orders_task = shopify_service.get_realtime_orders(minutes)
        meta_status_task = meta_service.test_connection()
        campaigns_task = meta_service.get_all_campaigns()

        shopify_orders, meta_status, campaigns = await asyncio.gather(
            shopify_orders_task, meta_status_task, campaigns_task
        )

        total_shopify_revenue = sum(float(o.get('total_price', 0)) for o in shopify_orders)
        order_count = len(shopify_orders)
        active_campaigns = [c for c in campaigns if c['status'] == 'ACTIVE']

        return {
            "window_minutes": minutes,
            "shopify": {
                "order_count": order_count,
                "revenue": total_shopify_revenue,
                "recent_orders": [o.get('id') for o in shopify_orders[:5]]
            },
            "meta": {
                "connected": meta_status.get('connected'),
                "active_campaign_count": len(active_campaigns),
                "active_campaigns": active_campaigns
            },
            "timestamp": date.today().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/shopify/sales", tags=["Shopify"])
async def get_sales_summary(
    start_date: date = date.today() - timedelta(days=30),
    end_date:   date = date.today()
):
    """Get sales aggregated by product."""
    try:
        sales = await shopify_service.get_sales_by_product(start_date, end_date)
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


@router.get("/shopify/sales/timeseries/{product_id}", tags=["Shopify"])
async def get_sales_timeseries(
    product_id: str,
    start_date: date = date.today() - timedelta(days=30),
    end_date:   date = date.today()
):
    """Get day-by-day sales for a specific product."""
    try:
        ts = await shopify_service.get_daily_sales_timeseries(product_id, start_date, end_date)
        return {
            "product_id": product_id,
            "period":     f"{start_date} → {end_date}",
            "days":       len(ts),
            "timeseries": ts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
#  META — CAMPAIGNS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/meta/campaigns", tags=["Meta"])
async def get_campaigns():
    """Fetch all Meta ad campaigns."""
    try:
        campaigns = await meta_service.get_all_campaigns()
        return {"count": len(campaigns), "campaigns": campaigns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meta/campaigns/{campaign_id}/insights", tags=["Meta"])
async def get_campaign_insights(
    campaign_id: str,
    start_date:  date = date.today() - timedelta(days=30),
    end_date:    date = date.today()
):
    """Get performance insights for a specific campaign."""
    try:
        insights = await meta_service.get_campaign_insights(campaign_id, start_date, end_date)
        return {"campaign_id": campaign_id, "period": f"{start_date} → {end_date}", **insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meta/campaigns/{campaign_id}/timeseries", tags=["Meta"])
async def get_campaign_timeseries(
    campaign_id: str,
    start_date:  date = date.today() - timedelta(days=30),
    end_date:    date = date.today()
):
    """Get daily spend/performance breakdown for a campaign."""
    try:
        ts = await meta_service.get_daily_spend_timeseries(campaign_id, start_date, end_date)
        return {"campaign_id": campaign_id, "days": len(ts), "timeseries": ts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
#  WOOCOMMERCE
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/woo/products", tags=["WooCommerce"])
async def get_woo_products():
    """Fetch all products from WooCommerce store."""
    try:
        products = await woocommerce_service.get_all_products()
        return {
            "count": len(products),
            "products": products
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/woo/orders", tags=["WooCommerce"])
async def get_woo_orders(
    start_date: date = date.today() - timedelta(days=30),
    end_date: date = date.today()
):
    """Fetch all orders from WooCommerce in a date range."""
    try:
        orders = await woocommerce_service.get_orders(start_date, end_date)
        return {"count": len(orders), "orders": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
#  ANALYTICS — CORE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/analytics/overview", tags=["Analytics"])
async def get_analytics_overview(
    start_date: date = date.today() - timedelta(days=90),
    end_date:   date = date.today()
):
    """
    Full analytics pipeline with Shopify, Meta, and WooCommerce.
    """
    try:
        # Fetch base data in parallel
        results = await asyncio.gather(
            shopify_service.get_all_products(),
            shopify_service.get_sales_by_product(start_date, end_date),
            meta_service.get_all_campaigns(),
            woocommerce_service.get_orders(start_date, end_date)
        )
        
        products, sh_sales, campaigns, woo_orders = results
        product_map = {p["id"]: p for p in products}

        # Calculate revenue from both sources
        shopify_revenue = sum(s["revenue"] for s in sh_sales.values())
        woo_revenue = sum(float(o.get("total", 0)) for o in woo_orders if o.get("status") in ["completed", "processing"])
        total_revenue = shopify_revenue + woo_revenue
        
        total_units = sum(s["units_sold"] for s in sh_sales.values())
        total_units += sum(sum(item.get("quantity", 0) for item in o.get("line_items", [])) for o in woo_orders)

        # Basic ROI Stats
        avg_cost = 0.0
        if product_map:
            costs = [p["cost_price"] for p in product_map.values() if p["cost_price"] > 0]
            avg_cost = sum(costs) / len(costs) if costs else 0

        total_spend = 0.0
        campaign_results = []
        
        for c in campaigns:
            cs = date.fromisoformat(c["start_time"][:10]) if c.get("start_time") else start_date
            ce = date.fromisoformat(c["stop_time"][:10]) if c.get("stop_time") else end_date
            
            insights = await meta_service.get_campaign_insights(c["id"], max(cs, start_date), min(ce, end_date))
            spend = insights.get("spend", 0)
            total_spend += spend
            
            # Simple aggregation logic as before
            profit = total_revenue - (total_units * avg_cost) - spend
            roas = total_revenue / spend if spend > 0 else 0
            
            campaign_results.append({
                "campaign_id": c["id"],
                "campaign_name": c["name"],
                "spend": spend,
                "revenue": total_revenue, # Simplified: attributing all revenue to ads
                "profit": profit,
                "roas": roas
            })

        return {
            "store": "Omnichannel",
            "start_date": start_date,
            "end_date": end_date,
            "total_revenue": round(total_revenue, 2),
            "shopify_revenue": round(shopify_revenue, 2),
            "woo_revenue": round(woo_revenue, 2),
            "total_ad_spend": round(total_spend, 2),
            "total_profit": round(total_revenue - (total_units * avg_cost) - total_spend, 2),
            "order_count": len(sh_sales) + len(woo_orders),
            "campaign_count": len(campaign_results),
            "campaigns": campaign_results
        }
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
