from fastapi import APIRouter, HTTPException
from datetime import date, timedelta
from typing import List
import asyncio
import traceback

from models.analytics_models import (
    AnalyticsResponse, OverviewStats, ProductSalesSummary, TopAction
)
import services.analytics_service as analytics_service
from services.woocommerce_service import woocommerce_service

router = APIRouter(tags=['Analytics'])

@router.get('/analytics/overview')
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
