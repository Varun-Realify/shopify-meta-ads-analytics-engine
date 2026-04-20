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

    # GOOGLE MERCHANT CENTER
    GOOGLE_MERCHANT_ID   = os.getenv("GOOGLE_MERCHANT_ID")
    GOOGLE_SERVICE_ACCOUNT_JSON_PATH = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_PATH")

    # WOOCOMMERCE
    WOO_URL              = os.getenv("WOO_URL")
    WOO_CONSUMER_KEY     = os.getenv("WOO_CONSUMER_KEY")
    WOO_CONSUMER_SECRET  = os.getenv("WOO_CONSUMER_SECRET")

    # COMPETITOR CONFIG
    COMPETITOR_URLS      = os.getenv("COMPETITOR_URLS", "").split(",")

    # ANALYSIS
    ANALYSIS_WINDOW_DAYS = 30
    TARGET_PROFIT_MARGIN = 20.0
