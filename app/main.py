import logging
import psutil
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Scraper API is running"}

@app.get("/scrape")
def scrape(url: str):
    # your scraping code here
    return {"url": url, "status": "scraped"}



from app.routers import searches
from app.core.database import engine, Base, get_db
from app.config import settings

app = FastAPI(
    title="Kleinanzeigen Notifier API",
    description="API für automatisierte Kleinanzeigen-Suchen mit Token-System",
    version="1.0.0"
)




# Router einbinden
app.include_router(searches.router, prefix="/api/v1", tags=["searches"])

# Dashboard Setup
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

logger = logging.getLogger(__name__)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/dashboard", include_in_schema=False)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT * FROM searches"))
        searches_list = [dict(row._mapping) for row in result]
        
        # Server-Status
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        active_searches = len([s for s in searches_list if s.get('enabled', False)])
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "searches": searches_list,
            "active_searches": active_searches,
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "error": None
        })
    except Exception as e:
        logger.error(f"Dashboard Error: {e}")
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "searches": [],
            "active_searches": 0,
            "cpu": 0,
            "memory": 0,
            "disk": 0,
            "error": str(e)
        })

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("🚀 API gestartet - Dashboard unter /dashboard")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
