from sqlalchemy import Column, Integer, String
from database.db import Base

class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    shop_domain = Column(String, unique=True, index=True)
    access_token = Column(String)
    shop_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    myshopify_domain = Column(String, nullable=True)