from fastapi import APIRouter, HTTPException
from datetime import date, timedelta
from typing import List
import asyncio
import traceback

from models.analytics_models import (
    AnalyticsResponse, OverviewStats, ProductSalesSummary, TopAction
)
from services import shopify_service, meta_service, analytics_service, woocommerce_service
from services.woocommerce_service import woocommerce_service
from services.plaid_service import plaid_service

router = APIRouter(tags=["Analytics"])

@router.get("/realtime/cross-check")
async def cross_check_realtime(minutes: int = 60):
    """
    Cross-checks Shopify orders in the last 'minutes' with Meta Ad performance.
    """
    try:
        shopify_orders = await shopify_service.get_realtime_orders(minutes)
        total_shopify_revenue = sum(float(o.get('total_price', 0)) for o in shopify_orders)
        order_count = len(shopify_orders)

        # Basic health check for Meta
        meta_status = await meta_service.test_connection()
        campaigns = await meta_service.get_all_campaigns()
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


@router.get("/analytics/comparison")
async def get_campaign_comparison(
    campaign_id: str,
    product_id: str,
    window_days: int = 30
):
    """
    Comparison analysis:
    Sales before ad campaign and sales during ad campaign of specific products
    """
    try:
        # 1. Start by getting campaign details to find the start date
        campaigns = await meta_service.get_all_campaigns()
        target_camp = next((c for c in campaigns if c["id"] == campaign_id), None)
        if not target_camp:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Use the actual campaign start date
        try:
            camp_start = date.fromisoformat(target_camp["start_time"])
        except (ValueError, KeyError):
            camp_start = date.today() - timedelta(days=15)
            
        today = date.today()
        
        # Define ranges
        pre_start = camp_start - timedelta(days=window_days)
        pre_end = camp_start - timedelta(days=1)
        
        # Define during window
        during_end = camp_start + timedelta(days=window_days)
        if during_end > today: during_end = today
        
        # Get historical sales for the product
        all_sales_before = await shopify_service.get_daily_sales_timeseries_all(pre_start, pre_end)
        all_sales_during = await shopify_service.get_daily_sales_timeseries_all(camp_start, during_end)
        
        # If product_id is provided, prioritize product-specific data for incrementality
        if product_id and product_id != 'default':
            all_sales_before = await shopify_service.get_daily_sales_timeseries(product_id, pre_start, pre_end)
            all_sales_during = await shopify_service.get_daily_sales_timeseries(product_id, camp_start, during_end)
        
        # Ensure we have data for all days in the range (fill zeros)
        def fill_days(data_list, start, end):
            data_map = {d["date"]: d for d in data_list}
            result = []
            curr = start
            while curr <= end:
                date_str = curr.isoformat()
                if date_str in data_map:
                    result.append(data_map[date_str])
                else:
                    result.append({"date": date_str, "units_sold": 0, "revenue": 0.0})
                curr += timedelta(days=1)
            return result

        full_before = fill_days(all_sales_before, pre_start, pre_end)
        full_during = fill_days(all_sales_during, camp_start, during_end)

        def calculate_avg(stats_list):
            if not stats_list: return 0.0
            return sum(s["units_sold"] for s in stats_list) / len(stats_list)

        avg_before = calculate_avg(full_before)
        avg_during = calculate_avg(full_during)
        
        total_before = sum(s["units_sold"] for s in full_before)
        total_during = sum(s["units_sold"] for s in full_during)
        
        lift = analytics_service.calculate_sales_lift(avg_before, avg_during)
        
        return {
            "campaign": target_camp["name"],
            "product_id": product_id,
            "period_start": camp_start,
            "window_days": window_days,
            "stats": {
                "avg_daily_before": round(avg_before, 2),
                "avg_daily_during": round(avg_during, 2),
                "total_before": total_before,
                "total_during": total_during,
                "sales_lift_pct": lift
            },
            "raw_data": {
                "before": full_before,
                "during": full_during
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_analytics(
    start_date: date = date.today() - timedelta(days=30),
    end_date:   date = date.today()
):
    """
    Get generic analytics for Shopify, WooCommerce and Meta Ads in a date range.
    """
    try:
        # Fetch Sales concurrently
        shopify_sales_task = shopify_service.get_sales_by_product(start_date, end_date)
        woo_sales_task = woocommerce_service.get_sales_by_product(start_date, end_date)
        campaigns_task = meta_service.get_all_campaigns()
        
        shopify_sales_data, woo_sales_data, campaigns = await asyncio.gather(
            shopify_sales_task, woo_sales_task, campaigns_task
        )

        total_shopify_revenue = sum(s["revenue"] for s in shopify_sales_data.values())
        total_shopify_units = sum(s["units_sold"] for s in shopify_sales_data.values())
        
        total_woo_revenue = sum(s["revenue"] for s in woo_sales_data.values())
        total_woo_units = sum(s["units_sold"] for s in woo_sales_data.values())

        total_revenue = total_shopify_revenue + total_woo_revenue
        total_units = total_shopify_units + total_woo_units

        # Fetch Ads data from Meta
        ad_summary = []
        total_spend = 0.0

        # Run insight fetches concurrently
        insight_tasks = [meta_service.get_campaign_insights(c["id"], start_date, end_date) for c in campaigns]
        insights_results = await asyncio.gather(*insight_tasks)

        for c, insights in zip(campaigns, insights_results):
            spend = insights.get("spend", 0)
            if spend > 0 or c.get("status") == "ACTIVE":
                total_spend += spend
                ad_summary.append({
                    "id": c["id"],
                    "name": c["name"],
                    "spend": spend,
                    "clicks": insights.get("clicks", 0),
                    "impressions": insights.get("impressions", 0),
                    "status": c.get("status")
                })

        return {
            "period": {
                "start": start_date,
                "end": end_date
            },
            "shopify": {
                "total_revenue": total_shopify_revenue,
                "total_units_sold": total_shopify_units,
                "product_breakdown": list(shopify_sales_data.values()),
                "daily_sales": await shopify_service.get_daily_sales_timeseries_all(start_date, end_date)
            },
            "woocommerce": {
                "total_revenue": total_woo_revenue,
                "total_units_sold": total_woo_units,
                "product_breakdown": list(woo_sales_data.values()),
                "daily_sales": await woocommerce_service.get_daily_sales_timeseries_all(start_date, end_date)
            },
            "meta_ads": {
                "total_spend": total_spend,
                "campaigns": ad_summary
            },
            "summary": {
                "roas": round(total_revenue / total_spend, 2) if total_spend > 0 else 0,
                "profit": round(total_revenue - total_spend, 2)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/overview")
async def get_analytics_overview(
    start_date: date = date.today() - timedelta(days=90),
    end_date:   date = date.today()
):
    try:
        woo_sales_task = woocommerce_service.get_sales_by_product(start_date, end_date)
        products = await woocommerce_service.get_all_products()
        all_woo_period_sales = await woo_sales_task
        product_map = {p['id']: p for p in products}
        avg_cost = 0.0
        if product_map:
            costs = [p.get('cost_price', 0) for p in product_map.values() if p.get('cost_price', 0) > 0]
            avg_cost = sum(costs) / len(costs) if costs else 0
        total_units = sum(s.get('units_sold', 0) for s in all_woo_period_sales.values())
        total_revenue = sum(s.get('revenue', 0) for s in all_woo_period_sales.values())
        def safe_profit(s):
            pid = s.get('product_id')
            prod = product_map.get(pid, {})
            cost = prod.get('cost_price', avg_cost)
            return analytics_service.calculate_profit(s.get('revenue', 0), s.get('units_sold', 0), cost, 0)
        total_profit = sum(safe_profit(s) for s in all_woo_period_sales.values())
        resp = AnalyticsResponse(
            overview=OverviewStats(
                store='WooCommerce',
                start_date=start_date,
                end_date=end_date,
                total_revenue=round(total_revenue, 2),
                total_ad_spend=0.0,
                total_profit=round(total_profit, 2),
                blended_roas=0.0,
                campaign_count=0,
                product_count=len(products),
                order_count=total_units
            ),
            campaigns=[],
            product_ranking=[],
            top_actions=[]
        )
        return resp
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/metrics")
def calculate_custom_metrics(
    revenue:       float = 1000.0,
    ad_spend:      float = 100.0,
    units_sold:    int   = 20,
    cost_price:    float = 10.0,
    selling_price: float = 50.0,
    impressions:   int   = 10000,
    clicks:        int   = 300,
    conversions:   int   = 20,
):
    """Calculate all KPIs for custom input values — useful for ad spend simulation."""
    profit        = analytics_service.calculate_profit(revenue, units_sold, cost_price, ad_spend)
    profit_margin = analytics_service.calculate_profit_margin(profit, revenue)
    roas          = analytics_service.calculate_roas(revenue, ad_spend)
    ctr           = analytics_service.calculate_ctr(clicks, impressions)
    cpa           = analytics_service.calculate_cpa(ad_spend, conversions)
    breakeven     = analytics_service.calculate_breakeven_units(ad_spend, selling_price, cost_price)

    metrics = {
        "revenue": revenue, "ad_spend": ad_spend, "profit": profit,
        "profit_margin": profit_margin, "roas": roas, "ctr": ctr,
        "cpa": cpa, "true_roas": 0, "sales_lift": 0,
        "selling_price": selling_price, "cost_price": cost_price,
    }
    rec = analytics_service.generate_recommendation(metrics)

    return {
        "inputs":          {"revenue": revenue, "ad_spend": ad_spend, "units_sold": units_sold,
                            "cost_price": cost_price, "selling_price": selling_price},
        "profit":          profit,
        "profit_margin":   profit_margin,
        "roas":            roas,
        "ctr":             ctr,
        "cpa":             cpa,
        "breakeven_units": breakeven,
        "recommendation":  rec,
    }