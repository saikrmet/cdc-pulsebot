from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Optional
from datetime import datetime, timedelta
from aiocache import caches

from search_model import query_dashboard_data
from schemas.dashboard import DashboardData


app = FastAPI(
    title="CDC Tweets Analysis App",
    description="Track how the public reacts to the CDC on Twitter using enrichment and vector search.",
)
templates = Jinja2Templates(directory="templates")

caches.set_config(
    {
        "default": {
            "cache": "aiocache.SimpleMemoryCache", 
            "serializer": {
                "class": "aiocache.serializers.JsonSerializer"
            }, 
            "ttl": 300
        }
    }
)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD")
):
    today = datetime.now().date()
    start = start_date or (today - timedelta(days=7)).isoformat()
    end = end_date or today.isoformat()

    data: DashboardData = await query_dashboard_data(start, end)

    return templates.TemplateResponse("dashboard.html",
                                      {
                                          "request": request, 
                                          "start_date": start, 
                                          "end_date": end, 
                                          "data": data
                                      })


