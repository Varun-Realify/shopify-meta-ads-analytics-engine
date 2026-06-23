import os
import re
import json
import base64
import requests
import logging
import urllib.parse
import uuid
import time
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
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
SHOPIFY_SCOPES = "read_products,read_orders,read_inventory,read_customers,read_analytics"

class ShopifyBeginRequest(BaseModel):
    shop: str
    api_key: str
    api_secret: str


def _encode_state(api_key: str, api_secret: str) -> str:
    """Pack credentials into a URL-safe base64 string used as the OAuth state."""
    payload = json.dumps({"k": api_key, "s": api_secret})
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def _decode_state(state: str):
    """Unpack credentials from the state string returned by Shopify's callback."""
    try:
        # Restore stripped base64 padding
        padded = state + "=" * (-len(state) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode())
        return payload.get("k"), payload.get("s")
    except Exception:
        return None, None


@router.post("/auth/shopify/begin")
async def begin_shopify_auth(body: ShopifyBeginRequest):
    """
    Encodes the user's api_key + api_secret directly into the OAuth state
    parameter so no server-side storage is needed.  Server restarts and
    multiple concurrent users are handled transparently.
    """
    shop = re.sub(r"^https?://", "", body.shop.strip()).split("/")[0]
    if "." not in shop:
        shop = f"{shop}.myshopify.com"
    elif shop.endswith(".myshopify"):
        shop = f"{shop}.com"

    api_key = body.api_key.strip()
    api_secret = body.api_secret.strip()

    if not api_key or not api_secret:
        raise HTTPException(status_code=400, detail="api_key and api_secret are required")

    state = _encode_state(api_key, api_secret)

    oauth_url = (
        f"https://{shop}/admin/oauth/authorize"
        f"?client_id={api_key}"
        f"&scope={SHOPIFY_SCOPES}"
        f"&redirect_uri={SHOPIFY_REDIRECT_URI}"
        f"&state={state}"
    )

    logger.info(f"OAuth begin for shop={shop}")
    return {"oauth_url": oauth_url}


@router.get("/auth/shopify/callback")
async def auth_shopify_callback(shop: str, code: str, state: str = ""):
    # Decode credentials from state; fall back to .env if state is missing/invalid
    api_key, api_secret = _decode_state(state) if state else (None, None)
    if not api_key:
        api_key = SHOPIFY_API_KEY
    if not api_secret:
        api_secret = SHOPIFY_API_SECRET

    if not api_key or not api_secret:
        raise HTTPException(status_code=400, detail="No Shopify credentials found — please reconnect")

    token_url = f"https://{shop}/admin/oauth/access_token"
    payload = {"client_id": api_key, "client_secret": api_secret, "code": code}

    response = requests.post(token_url, json=payload)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve access token from Shopify")

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
                shop_name=shop.split(".")[0],
            )
            db.add(new_shop)
        db.commit()
        logger.info(f"OAuth complete for shop={shop}")
    finally:
        db.close()

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").strip().rstrip("/")
    return RedirectResponse(url=f"{frontend_url}/sales?shop={shop}&status=connected&platform=shopify")


# ═══════════════════════════════════════════════════════════════════════
# SHOPIFY MANUAL TOKEN (temporary until Partner App is approved)
# ═══════════════════════════════════════════════════════════════════════

class ManualTokenRequest(BaseModel):
    shop: str
    access_token: str

@router.post("/auth/shopify/manual")
async def shopify_manual_connect(body: ManualTokenRequest):
    shop = body.shop.strip().replace("https://", "").replace("http://", "").strip("/")
    token = body.access_token.strip()

    # Validate token against Shopify
    shop_info_url = f"https://{shop}/admin/api/2024-01/shop.json"
    resp = requests.get(shop_info_url, headers={"X-Shopify-Access-Token": token})

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid token or store URL. Check the Admin API access token.")

    shop_data = resp.json().get("shop", {})
    shop_name = shop_data.get("name", shop.split('.')[0])
    email = shop_data.get("email")
    currency = shop_data.get("currency")

    db = SessionLocal()
    try:
        existing = db.query(Shop).filter(Shop.shop_domain == shop).first()
        if existing:
            existing.access_token = token
            existing.shop_name = shop_name
            existing.platform = "shopify"
        else:
            new_shop = Shop(
                shop_domain=shop,
                access_token=token,
                platform="shopify",
                shop_name=shop_name
            )
            db.add(new_shop)
        db.commit()
        logger.info(f"Manual token connected: {shop}")
    except Exception as e:
        db.rollback()
        logger.error(f"DB error during manual connect: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

    return {"shop": shop, "shop_name": shop_name, "status": "connected"}


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

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").strip().rstrip("/")
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000").strip().rstrip("/")

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
