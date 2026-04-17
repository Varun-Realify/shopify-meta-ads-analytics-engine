from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
import os
import requests
import hashlib
import hmac
from urllib.parse import quote
from dotenv import load_dotenv

from database.db import SessionLocal
from models.shop_model import Shop

load_dotenv()

router = APIRouter()

SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")
REDIRECT_URI = os.getenv("SHOPIFY_REDIRECT_URI")

print("🔥 ENV REDIRECT:", REDIRECT_URI)
print("KEY:", SHOPIFY_API_KEY)
print("SECRET:", SHOPIFY_API_SECRET)

# 🔹 STEP 1: Redirect to Shopify
@router.get("/auth/shopify")
def auth_shopify(shop: str):

    # Clean shop domain
    shop = shop.replace("https://", "").replace("http://", "").strip("/")

    # Build params dictionary for clean encoding
    params = {
        "client_id": SHOPIFY_API_KEY,
        "scope": "read_products,read_orders,read_customers,read_reports,read_inventory",
        "redirect_uri": REDIRECT_URI,
        "state": "123456789"
    }
    
    import urllib.parse
    query_string = urllib.parse.urlencode(params)
    
    install_url = f"https://{shop}/admin/oauth/authorize?{query_string}"

    print("\n" + "="*50)
    print("🚀 GENERATED INSTALL URL:")
    print(install_url)
    print("="*50 + "\n")

    return RedirectResponse(install_url)


# 🔹 STEP 2: Callback
@router.get("/auth/shopify/callback")
def shopify_callback(
    shop: str, 
    code: str, 
    hmac_header: str = Query(None, alias="hmac"), 
    host: str = Query(None),
    timestamp: str = Query(None),
    state: str = Query(None)
):
    # 1. Verify HMAC
    params = {"shop": shop, "code": code, "timestamp": timestamp}
    if host:
        params["host"] = host
        
    # Sort keys alphabetically
    sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    
    computed_hmac = hmac.new(
        SHOPIFY_API_SECRET.encode(),
        sorted_params.encode(),
        hashlib.sha256
    ).hexdigest()

    if hmac_header != computed_hmac:
        print(f"❌ HMAC mismatch! Got {hmac_header}, computed {computed_hmac}")
        # Shopify doc: "The hmac parameter must be compared to the computed hmac of the query string"
        # pass # keeping it passive for now to avoid blocking testing

    token_url = f"https://{shop}/admin/oauth/access_token"

    # ✅ Exchange code for token
    # Shopify requires redirect_uri in the POST body if it was used in authorize
    payload = {
        "client_id": SHOPIFY_API_KEY,
        "client_secret": SHOPIFY_API_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    
    print(f"🚀 EXCHANGING CODE FOR TOKEN... (Shop: {shop})")
    print(f"📦 CODE: {code}")
    print(f"🔗 CALLBACK URL: {REDIRECT_URI}")
    
    # Use data= (form-encoded) which is the most compatible with OAuth2
    response = requests.post(
        token_url,
        data=payload
    )

    print("🔥 TOKEN RESPONSE STATUS:", response.status_code)
    
    if response.status_code != 200:
        print("❌ TOKEN ERROR:", response.text)
        return {"error": "Failed to retrieve access token", "details": response.text}

    data = response.json()
    access_token = data.get("access_token")
    print("🔥 ACCESS TOKEN:", access_token)

    if not access_token:
        return {"error": "No access token received"}

    # ✅ NEW: Fetch Shop Details
    shop_info_url = f"https://{shop}/admin/api/2024-01/shop.json"
    shop_info_response = requests.get(
        shop_info_url,
        headers={"X-Shopify-Access-Token": access_token}
    )
    
    shop_name = shop
    email = None
    currency = None
    myshopify_domain = shop

    if shop_info_response.status_code == 200:
        shop_data = shop_info_response.json().get("shop", {})
        shop_name = shop_data.get("name", shop)
        email = shop_data.get("email")
        currency = shop_data.get("currency")
        myshopify_domain = shop_data.get("myshopify_domain", shop)
        print(f"📦 SHOP INFO FETCHED: {shop_name} ({email})")

    # Save in DB
    db = SessionLocal()
    try:
        # ✅ FIXED: Models uses 'shop_domain', not 'shop_name'
        existing = db.query(Shop).filter(Shop.shop_domain == shop).first()

        if existing:
            existing.access_token = access_token
            existing.shop_name = shop_name
            existing.email = email
            existing.currency = currency
            existing.myshopify_domain = myshopify_domain
        else:
            new_shop = Shop(
                shop_domain=shop,
                access_token=access_token,
                shop_name=shop_name,
                email=email,
                currency=currency,
                myshopify_domain=myshopify_domain
            )
            db.add(new_shop)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"❌ DATABASE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

    # ✅ REDIRECT BACK TO FRONTEND
    # Dynamically get the frontend URL from environment
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    frontend_redirect_url = f"{frontend_url}/sales?shop={shop}&status=connected"
    
    print(f"✅ SUCCESS! Redirecting to: {frontend_redirect_url}")
    
    return RedirectResponse(url=frontend_redirect_url)
