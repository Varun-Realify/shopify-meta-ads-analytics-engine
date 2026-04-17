from pydantic import BaseModel
from typing import List

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
