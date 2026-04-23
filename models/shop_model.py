from sqlalchemy import Column, Integer, String
from database.db import Base

class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    shop_domain = Column(String, unique=True, index=True)
    platform = Column(String, default='shopify')  # 'shopify' or 'woocommerce'
    access_token = Column(String)  # For Shopify: OAuth token, For WooCommerce: Consumer Key
    api_secret = Column(String, nullable=True) # For WooCommerce: Consumer Secret
    shop_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    myshopify_domain = Column(String, nullable=True)