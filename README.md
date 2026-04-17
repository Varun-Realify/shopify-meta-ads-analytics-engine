# 📊 Business Intelligence Dashboard: Shopify × Meta Ads × Google Ads

This is a real-time analytics application built to help e-commerce owners understand the **true impact** of their advertising by linking Shopify sales to Meta Ads performance and Google Merchant Center price benchmarks.

## 📁 Project Structure

```text
.
├── core/                # Core configuration and environment settings
├── frontend/            # React + Vite dashboard application
├── models/              # Pydantic data schemas for API validation
├── routers/             # FastAPI route handlers (API endpoints)
│   ├── api.py           # Core analytics and store endpoints
│   ├── charts.py        # Chart-specific data endpoints
│   └── merchant_router.py # Google Merchant Center integration
├── services/            # Business logic and external API integrations
│   ├── analytics_service.py # ROAS, Sales Lift, and Profit calculations
│   ├── chart_service.py   # Data formatting for Recharts
│   ├── google_merchant_service.py # Google Merchant API hooks
│   ├── meta_service.py    # Meta Graph API integration
│   └── shopify_service.py # Shopify Admin API integration
├── main.py              # Application entry point (FastAPI)
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables (Configuration)
```

## 🚀 Execution Guide (How to Run)

Follow these steps in order to start the full application:

### 1. Backend Setup (FastAPI)
Open a terminal in the root directory:
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
uvicorn main:app --reload --port 8000
```
*The API will be available at `http://localhost:8000`.*

### 2. Frontend Setup (React)
Open a **new** terminal:
```bash
# 1. Navigate to frontend folder
cd frontend

# 2. Install dependencies
npm install

# 3. Start the dashboard
npm run dev
```
*The dashboard will be available at `http://localhost:5173`.*

### 3. Environment Configuration
Ensure your `.env` file in the root directory is populated:
```env
# SHOPIFY CONFIG
SHOPIFY_STORE_NAME=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxx

# META ADS CONFIG
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
META_ACCESS_TOKEN=your_permanent_access_token
META_AD_ACCOUNT_ID=act_123456789

# GOOGLE MERCHANT CENTER CONFIG
GOOGLE_MERCHANT_ID=your_merchant_id
GOOGLE_SERVICE_ACCOUNT_JSON_PATH=path/to/service-account.json
```

## 📢 Key Integrations

### 🔵 Meta Ads Integration
- **Campaign Insights**: Real-time Spend, CPC, CTR, and Reach.
- **Conversion Tracking**: Automated purchase conversion mapping.
- **Incrementality**: Calculates "Sales Lift" by comparing Shopify data against Ad start dates.
- **Catalog Sync**: Automated product pushing to Meta Commerce Manager.

### 🟡 Google Merchant Center Integration
- **Market Benchmarks**: Compare your product prices against global market averages.
- **Price Competitiveness**: Identify products that are priced too high or too low.
- **Best Seller Analysis**: Track top-performing products in your category across Google Shopping.

## 🛍️ Competitor Analysis
The backend exposes multi-store Shopify competitor tracking under `/api/v1/competitors/track`.
- Track multiple public Shopify stores side by side.
- Compare catalog size, average price, discounts, categories, and best-seller signals.

## 🛠️ Tech Stack
-   **Backend**: FastAPI (Python) — Handles data ingestion, security, and complex analysis.
-   **Frontend**: React (Vite) + Recharts — A responsive, high-performance dashboard for business visualization.
-   **APIs**: Connected directly to **Shopify Admin API**, **Meta Graph API**, and **Google Content API for Shopping**.

## 🚀 How it Works (Real Data Flow)
1.  **Ingestion**: The backend connects to live Shopify data, Meta Ad accounts, and your Google Merchant Center.
2.  **Processing**: The system automatically calculates:
    -   **Net Profit**: Revenue minus (Product Cost + Ad Spend).
    -   **Sales Lift**: Compares organic sales *before* an ad started to sales *during* the ad.
    -   **Price Gap**: Difference between your store price and the Google market benchmark.
3.  **Visualization**: React renders this data into clean, interactive charts and tables.

---
**Focus**: Professional Business Intelligence & Verified Growth Tracking.
**Last Updated**: April 17, 2026

