from pydantic import BaseModel
from typing import List

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
