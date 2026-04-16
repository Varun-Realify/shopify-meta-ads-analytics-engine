import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # SHOPIFY
    SHOPIFY_STORE_NAME   = os.getenv("SHOPIFY_STORE_NAME")
    SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
    SHOPIFY_API_VERSION  = os.getenv("SHOPIFY_API_VERSION", "2024-01")

    # META
    META_APP_ID          = os.getenv("META_APP_ID")
    META_APP_SECRET      = os.getenv("META_APP_SECRET")
    META_ACCESS_TOKEN    = os.getenv("META_ACCESS_TOKEN")
    META_AD_ACCOUNT_ID   = os.getenv("META_AD_ACCOUNT_ID")

    # ANALYSIS
    ANALYSIS_WINDOW_DAYS = 30
    TARGET_PROFIT_MARGIN = 20.0
    print("REDIRECT:", os.getenv("SHOPIFY_REDIRECT_URI"))

    SHOPIFY_REDIRECT_URI = os.getenv("SHOPIFY_REDIRECT_URI")
