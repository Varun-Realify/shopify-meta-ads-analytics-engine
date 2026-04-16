import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.api import router
from routers.charts import router as charts_router
from routers.auth import router as auth_router

from database.db import Base, engine

# ✅ APP CREATE PEHLE
app = FastAPI(
    title="Shopify × Meta Ads Analytics API",
    version="1.0.0"
)

# ✅ DB TABLE CREATE
Base.metadata.create_all(bind=engine)

# ✅ MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ ROUTERS (AB USE KAR)
app.include_router(router, prefix="/api/v1")
app.include_router(charts_router, prefix="/api/v1/charts")
app.include_router(auth_router, prefix="/api/v1")   # 👈 IMPORTANT

# ROOT
@app.get("/")
def root():
    return {"message": "🚀 API Running"}

# RUN
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)