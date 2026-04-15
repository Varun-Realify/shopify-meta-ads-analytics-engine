# � Business Intelligence Dashboard: Shopify × Meta Ads

This is a real-time analytics application built to help e-commerce owners understand the **true impact** of their advertising by linking Shopify sales to Meta Ads performance.
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
META_CATALOG_ID=your_catalog_id # Required for sync feature
```
## 📢 Meta Ads Integration
This application integrates deeply with the **Meta Graph API** to provide:
- **Campaign Insights**: Real-time Spend, CPC, CTR, and Reach.
- **Conversion Tracking**: Automated purchase conversion mapping.
- **Incrementality**: Calculates "Sales Lift" by comparing Shopify data against Ad start dates.
- **Catalog Sync**: Automated product pushing to Meta Commerce Manager.

## 🛍️ Competitor Analysis
The backend now exposes multi-store Shopify competitor tracking under `/api/v1/competitors/track`.
- Track multiple public Shopify stores side by side.
- Compare catalog size, average price, discounts, categories, and best-seller signals.
- Paste comma-separated store URLs and get a unified summary.

## 🛠️ Tech Stack
-   **Backend**: FastAPI (Python) — Handles data ingestion, security, and complex analysis.
-   **Frontend**: React (Vite) + Recharts — A responsive, high-performance dashboard for business visualization.
-   **APIs**: Connected directly to **Shopify Admin API** and **Meta Graph API**.

## 🚀 How it Works (Real Data Flow)
1.  **Ingestion**: The backend connects to your live Shopify store (Orders/Products) and Meta Ad Account (Spend/Clicks).
2.  **Processing**: No manual data entry. The system automatically calculates:
    -   **Net Profit**: Revenue minus (Product Cost + Ad Spend).
    -   **Sales Lift**: Compares organic sales *before* an ad started to sales *during* the ad.
3.  **Visualization**: React renders this filtered data into clean, interactive charts and tables.

---
**Focus**: Professional Business Intelligence & Verified Growth Tracking.
**Date**: April 11, 2026
