from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ProductVariant(BaseModel):
    title: str
    price: float
    compare_at_price: Optional[float] = None
    discount_pct: float
    available: bool
    sku: str


class CompetitorProduct(BaseModel):
    id: int
    title: str
    handle: str
    product_type: str
    vendor: str
    tags: list[str]
    variants: list[ProductVariant]
    lowest_price: float
    highest_price: float
    avg_price: float
    total_variants: int
    in_stock: bool
    available_variants: int
    image_count: int
    created_at: str
    updated_at: str


class CompetitorStore(BaseModel):
    store_url: str
    store_name: str
    total_products: int
    total_variants: int
    in_stock_products: int
    out_of_stock_products: int
    price_range_min: float
    price_range_max: float
    avg_product_price: float
    products_with_discount: int
    avg_discount_pct: float
    top_product_types: list[str]
    top_vendors: list[str]
    top_tags: list[str]
    best_selling_estimate: list[str]
    scraped_at: str


class PriceComparison(BaseModel):
    product_title: str
    your_price: float
    competitor_price: float
    price_difference: float
    price_difference_pct: float
    you_are_cheaper: bool
    recommendation: str


class CompetitorAnalysisResult(BaseModel):
    your_store: CompetitorStore
    competitor_store: CompetitorStore
    price_comparisons: list[PriceComparison]
    matched_products: int
    insights: list[str]
    recommendations: list[str]


class CompetitorTrackRequest(BaseModel):
    competitor_urls: list[str] = Field(default_factory=list)
