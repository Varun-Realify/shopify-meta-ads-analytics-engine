from fastapi import APIRouter, HTTPException, Response
from datetime import date, timedelta
from services import chart_service
from routers.analytics import get_analytics_overview

router = APIRouter()

@router.get("/dashboard.png", tags=["Analytics Charts"], responses={200: {"content": {"image/png": {}}}})
def get_dashboard_chart(
    start_date: date = date.today() - timedelta(days=90),
    end_date:   date = date.today()
):
    """
    Returns a Matplotlib-generated dashboard image combining insights.
    """
    try:
        # Re-use the existing analytics function to fetch data directly
        # Since get_analytics_overview is async, we need to handle it or use service directly
        # For simplicity in this chart tool, we'll try to await it if needed, 
        # but better to call the service.
        import asyncio
        analytics_data = asyncio.run(get_analytics_overview(start_date, end_date))
        
        # Generate the PNG image output
        image_bytes = chart_service.generate_dashboard(analytics_data)
        
        return Response(content=image_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
