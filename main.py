import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import health, shopify, meta, analytics, woocommerce, localwp, plaid, stripe
from routers.charts import router as charts_router
from routers import quickbooks
# from routers.merchant_router import router as merchant_router

app = FastAPI(
    title       = "WooCommerce Analytics API",
    description = """
## 📊 WooCommerce Analytics Engine

Analyze your WooCommerce store performance.

### Features
- ✅ **Real eCommerce Data** — WooCommerce Products, Orders, Revenue
- ✅ **Analytics Overview** — Performance report
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
# app.include_router(shopify.router, prefix="/api/v1")
# app.include_router(meta.router, prefix="/api/v1")
app.include_router(woocommerce.router, prefix="/api/v1")
app.include_router(localwp.router, prefix="/api/v1")
app.include_router(plaid.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(charts_router, prefix="/api/v1/charts")
app.include_router(quickbooks.router, prefix="/api/v1")
app.include_router(stripe.router, prefix="/api/v1")
# app.include_router(merchant_router, prefix="/api")


@app.get("/", tags=["Root"])
def root():
    return {
        "message":  "🚀 WooCommerce Analytics API",
        "version":  "1.0.0",
        "docs":     "/docs",
        "redoc":    "/redoc",
        "endpoints": {
            "health":           "/api/v1/health",
            "woocommerce_products": "/api/v1/woocommerce/products",
            "analytics_overview":   "/api/v1/analytics/overview",
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
