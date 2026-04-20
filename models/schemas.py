from pydantic import BaseModel
from typing import Optional, List
from datetime import date


# ── Request Models ────────────────────────────────────────────────────────────

class AnalyticsRequest(BaseModel):
    start_date: date
    end_date: date


# ── Response Models ───────────────────────────────────────────────────────────

class ProductModel(BaseModel):
    id: str
    title: str
    vendor: str
    product_type: str
    selling_price: float
    cost_price: float
    stock: int


class OrderItem(BaseModel):
    product_id: str
    title: str
    quantity: int
    price: float
    revenue: float


class OrderModel(BaseModel):
    id: str
    created_at: str
    financial_status: str
    total_price: float
    line_items: List[OrderItem]


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


class CampaignMetrics(BaseModel):
    campaign_id: str
    campaign_name: str
    platform: str
    status: str
    ad_spend: float
    revenue: float
    profit: float
    profit_margin: float
    roas: float
    true_roas: float
    ctr: float
    cpa: float
    impressions: int
    clicks: int
    conversions: int
    units_sold: int
    breakeven_units: float
    sales_lift: float
    recommendation_level: str
    recommendation_headline: str
    recommendation_detail: str
    recommendation_action: str
    recommendation_warnings: List[str]


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


class ConnectionStatus(BaseModel):
    shopify: bool
    meta: bool
    woocommerce: bool
    shopify_store: Optional[str] = None
    shopify_currency: Optional[str] = None
    meta_user: Optional[str] = None
    meta_ad_account: Optional[str] = None
    woo_url: Optional[str] = None
    errors: List[str] = []
