from pydantic import BaseModel
from typing import List
from datetime import date
from .meta_models import CampaignMetrics

class AnalyticsRequest(BaseModel):
    start_date: date
    end_date: date


class PeriodStats(BaseModel):
    avg_daily_units: float
    total_revenue: float
    total_units: int
    days: int


class PeriodComparison(BaseModel):
    before: PeriodStats
    during: PeriodStats
    after: PeriodStats
    sales_lift_during: float
    sales_lift_after: float


class ProductSalesSummary(BaseModel):
    product_id: str
    title: str
    units_sold: int
    revenue: float
    ad_cost: float
    net_profit: float
    margin: float
    rank: int


class OverviewStats(BaseModel):
    store: str
    start_date: date
    end_date: date
    total_revenue: float
    total_ad_spend: float
    total_profit: float
    blended_roas: float
    campaign_count: int
    product_count: int
    order_count: int


class TopAction(BaseModel):
    priority: int
    campaign_name: str
    level: str
    action: str
    potential_impact: float


class AnalyticsResponse(BaseModel):
    overview: OverviewStats
    campaigns: List[CampaignMetrics]
    product_ranking: List[ProductSalesSummary]
    top_actions: List[TopAction]
