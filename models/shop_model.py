from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from database.db import Base


class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    shop_domain = Column(String, unique=True, index=True)
    platform = Column(String, default='shopify')
    access_token = Column(String, nullable=True)
    api_secret = Column(String, nullable=True)
    shop_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    myshopify_domain = Column(String, nullable=True)


class ImportedOrder(Base):
    __tablename__ = "imported_orders"

    id = Column(Integer, primary_key=True, index=True)
    shop_domain = Column(String, index=True)
    order_name = Column(String)
    created_at = Column(String)
    financial_status = Column(String)
    currency = Column(String, default="INR")
    total_price = Column(Float, default=0.0)
    line_items_json = Column(Text, default="[]")
    imported_at = Column(DateTime, default=datetime.utcnow)


class ImportedProduct(Base):
    __tablename__ = "imported_products"

    id = Column(Integer, primary_key=True, index=True)
    shop_domain = Column(String, index=True)
    handle = Column(String)
    title = Column(String)
    vendor = Column(String, nullable=True)
    product_type = Column(String, nullable=True)
    sku = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    cost_per_item = Column(Float, nullable=True)
    inventory_qty = Column(Integer, nullable=True)
    imported_at = Column(DateTime, default=datetime.utcnow)


class CSVImportLog(Base):
    __tablename__ = "csv_import_logs"

    id = Column(Integer, primary_key=True, index=True)
    shop_domain = Column(String, index=True)
    import_type = Column(String)
    file_name = Column(String)
    total_rows = Column(Integer, default=0)
    success_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    status = Column(String)
    imported_at = Column(DateTime, default=datetime.utcnow)