from database.db import SessionLocal
from models.shop_model import Shop
from fastapi import HTTPException


def get_shop_data(shop: str):
    db = SessionLocal()
    data = db.query(Shop).filter(Shop.shop_domain == shop).first()
    db.close()

    if not data:
        raise HTTPException(404, "Shop not connected")

    return {
        "shop": data.shop_domain,
        "token": data.access_token
    }