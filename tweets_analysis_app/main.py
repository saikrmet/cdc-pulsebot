from fastapi import FastAPI, Request, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
from datetime import datetime, timedelta
from aiocache import caches
from contextlib import asynccontextmanager
import logging
from pathlib import Path
from tweets_analysis_app.clients import AzureClients, set_azure_clients
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("aiocache").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


from tweets_analysis_app.services.dashboard_service import get_dashboard_data
from tweets_analysis_app.models.dashboard import DashboardData

@asynccontextmanager
async def lifespan(app: FastAPI):
    azure_clients = AzureClients()
    await azure_clients.init_clients()
    set_azure_clients(azure_clients)
    logger.info("Initiated Azure clients")
    yield
    await azure_clients.close()

app = FastAPI(
    title="CDC Tweets Analysis App",
    description="Track how the public reacts to the CDC on Twitter using enrichment and vector search.",
    lifespan=lifespan
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    
    
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


@app.get("/")
async def home():
    logger.info("Redirect to dashboard")
    return RedirectResponse(url="/dashboard")


def get_azure_clients() -> AzureClients:
    return app.state.azure_clients

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD")
):
    print("Inside dashboard func")
    logger.info("inside dashboard func in main")
    today = datetime.now().date()
    start = start_date or (today - timedelta(days=7)).isoformat()
    end = end_date or today.isoformat()
    logger.info("Start: {}".format(start))
    logger.info("End: {}".format(end))

    logger.info("Called query dashboard")
    data: DashboardData = await get_dashboard_data(start, end)

    logger.info("Returned query dashboard")
    return templates.TemplateResponse("dashboard.html",
                                      {
                                          "request": request, 
                                          "start_date": start, 
                                          "end_date": end, 
                                          "data": data
                                      })


