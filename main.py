import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import health, shopify, meta, analytics, woocommerce, localwp, plaid
from routers.charts import router as charts_router
# from routers.merchant_router import router as merchant_router

app = FastAPI(
    title       = "Shopify × Meta Ads Analytics API",
    description = """
## 📊 Shopify × Meta Ads Analytics Engine

Analyze your Shopify and WooCommerce store performance against Meta ad campaigns.

### Features
- ✅ **Real eCommerce Data** — Shopify & WooCommerce Products, Orders, Revenue
- ✅ **Real Meta Ads Data** — Campaigns, Spend, Impressions, CTR
- ✅ **Before vs After Analysis** — Sales impact of ad campaigns
- ✅ **Profit & ROAS Calculations** — True ROI per campaign
- ✅ **AI Recommendations** — STOP / OPTIMIZE / SCALE decisions

### Quick Start
1. `GET /connections` — Verify all APIs are connected
2. `GET /shopify/products` or `GET /woocommerce/products` — See your products
3. `GET /shopify/orders` or `GET /woocommerce/orders` — See your orders
4. `GET /meta/campaigns` — See your ad campaigns
5. `GET /analytics/overview` — Full performance report
    """,
    version     = "1.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(shopify.router, prefix="/api/v1")
app.include_router(meta.router, prefix="/api/v1")
app.include_router(woocommerce.router, prefix="/api/v1")
app.include_router(localwp.router, prefix="/api/v1")
app.include_router(plaid.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(charts_router, prefix="/api/v1/charts")
# app.include_router(merchant_router, prefix="/api")


@app.get("/", tags=["Root"])
def root():
    return {
        "message":  "🚀 Shopify × Meta Ads Analytics API",
        "version":  "1.0.0",
        "docs":     "/docs",
        "redoc":    "/redoc",
        "endpoints": {
            "health":           "/api/v1/health",
            # "connections":      "/api/v1/connections",
            "products":         "/api/v1/shopify/products",
            "orders":           "/api/v1/shopify/orders",
            "sales":            "/api/v1/shopify/sales",
            "campaigns":        "/api/v1/meta/campaigns",
            "analytics":        "/api/v1/analytics/overview",
            "competitor_track": "/api/v1/competitors/track",
            "before_after":     "/api/v1/analytics/before-after/{product_id}",
            "custom_metrics":   "/api/v1/analytics/metrics",
            "dashboard_image":  "/api/v1/charts/dashboard.png",
            "woo_products": "/api/v1/woocommerce/products",
            "woo_orders": "/api/v1/woocommerce/orders",
            "plaid_transactions": "/api/v1/plaid/transactions",
            "plaid_accounts": "/api/v1/plaid/accounts",
            "plaid_status": "/api/v1/plaid/status",
            "analytics_overview": "/api/v1/analytics/overview"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
