from sqlalchemy import Column, Integer, String
from database.db import Base

class UserStore(Base):
    __tablename__ = "user_stores"

    id = Column(Integer, primary_key=True, index=True)
    shop = Column(String, unique=True)
    shopify_token = Column(String)
    meta_token = Column(String)
    ad_account_id = Column(String)