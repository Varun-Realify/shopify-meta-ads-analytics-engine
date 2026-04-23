import os
import requests
import logging
import urllib.parse
import uuid
import time
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.shop_model import Shop
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# SHOPIFY AUTH
# ═══════════════════════════════════════════════════════════════════════
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")
SHOPIFY_REDIRECT_URI = os.getenv("SHOPIFY_REDIRECT_URI")
SHOPIFY_SCOPES = "read_products,read_orders,read_inventory"

@router.get("/auth/shopify")
async def auth_shopify(shop: str):
    if not shop:
        raise HTTPException(status_code=400, detail="Missing shop parameter")
    
    auth_url = (
        f"https://{shop}/admin/oauth/authorize?"
        f"client_id={SHOPIFY_API_KEY}&"
        f"scope={SHOPIFY_SCOPES}&"
        f"redirect_uri={SHOPIFY_REDIRECT_URI}&"
        f"state=nonce"
    )
    return RedirectResponse(url=auth_url)

@router.get("/auth/shopify/callback")
async def auth_shopify_callback(shop: str, code: str):
    token_url = f"https://{shop}/admin/oauth/access_token"
    payload = {
        "client_id": SHOPIFY_API_KEY,
        "client_secret": SHOPIFY_API_SECRET,
        "code": code
    }
    
    response = requests.post(token_url, json=payload)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve access token")
    
    access_token = response.json().get("access_token")
    
    db = SessionLocal()
    try:
        existing_shop = db.query(Shop).filter(Shop.shop_domain == shop).first()
        if existing_shop:
            existing_shop.access_token = access_token
            existing_shop.platform = "shopify"
        else:
            new_shop = Shop(
                shop_domain=shop, 
                access_token=access_token, 
                platform="shopify",
                shop_name=shop.split('.')[0]
            )
            db.add(new_shop)
        db.commit()
    finally:
        db.close()
    
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    return RedirectResponse(url=f"{frontend_url}/sales?shop={shop}&status=connected&platform=shopify")


# ═══════════════════════════════════════════════════════════════════════
# WOOCOMMERCE AUTH
# ═══════════════════════════════════════════════════════════════════════

@router.get("/auth/woocommerce")
def auth_woocommerce(shop_url: str):
    """
    Redirects user to WooCommerce for authorization
    """
    shop_url = shop_url.strip("/")
    if not shop_url.startswith("http"):
        shop_url = f"https://{shop_url}"

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")

    # Standard Auth Endpoint params
    shop_domain = shop_url.replace('https://', '').replace('http://', '').strip("/")
    callback_url = f"{backend_url}/api/v1/auth/woocommerce/callback/"

    params = {
        "app_name": "Realify Analytics",
        "scope": "read_write",
        "user_id": shop_domain, # Using domain as user_id to identify the shop back
        "return_url": f"{frontend_url}/sales?shop={shop_domain}&status=connected&platform=woocommerce",
        "callback_url": callback_url
    }
    
    auth_url = f"{shop_url}/wc-auth/v1/authorize/?{urllib.parse.urlencode(params)}"
    print(f"\n🚀 INITIATING AUTO-AUTH FOR: {shop_domain}")
    return RedirectResponse(url=auth_url)


@router.api_route("/auth/woocommerce/callback/", methods=["GET", "POST"])
@router.api_route("/auth/woocommerce/callback", methods=["GET", "POST"])
async def woocommerce_callback(request: Request):
    """
    Handles WooCommerce key delivery with maximum robustness
    """
    print("\n" + "📥" * 20)
    print(f"CALLBACK RECEIVED FROM: {request.client.host}")
    
    if request.method == "GET":
        return {"status": "ok", "message": "Callback active"}

    data = {}
    try:
        data = await request.json()
    except:
        try:
            form_data = await request.form()
            data = dict(form_data)
        except:
            print("❌ Could not parse callback data")

    print(f"DATA: {data}")

    consumer_key = data.get("consumer_key")
    consumer_secret = data.get("consumer_secret")
    # Identify shop from store_url OR user_id (where we stored the domain)
    shop_domain = data.get("store_url", data.get("user_id"))
    
    if not all([consumer_key, consumer_secret, shop_domain]):
        print("❌ Missing required fields in callback")
        return {"status": "error", "message": "Missing credentials"}

    shop_domain = shop_domain.replace("https://", "").replace("http://", "").strip("/")
    print(f"🔑 Keys received for: {shop_domain}")

    db = SessionLocal()
    try:
        existing = db.query(Shop).filter(Shop.shop_domain == shop_domain).first()
        if existing:
            existing.access_token = consumer_key
            existing.api_secret = consumer_secret
            existing.platform = "woocommerce"
            print(f"✅ UPDATED KEYS FOR: {shop_domain}")
        else:
            new_shop = Shop(
                shop_domain=shop_domain,
                access_token=consumer_key,
                api_secret=consumer_secret,
                platform="woocommerce",
                shop_name=shop_domain
            )
            db.add(new_shop)
            print(f"✅ SAVED NEW KEYS FOR: {shop_domain}")
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"❌ DB ERROR: {str(e)}")
    finally:
        db.close()

    return {"status": "success"}
