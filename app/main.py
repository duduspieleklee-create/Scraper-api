import logging
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.routers import searches
from app.core.database import engine, Base, get_db, AsyncSessionLocal
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
        searches_list = []
        for row in result:
            searches_list.append({
                "name": row.name,
                "keyword": row.keyword,
                "interval_minutes": row.interval_minutes,
                "enabled": row.enabled,
                "last_run": str(row.last_run) if row.last_run else "Nie"
            })
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "searches": searches_list
        })
    except Exception as e:
        return {"error": str(e)}

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as db:
        # Default Data
        result = await db.execute(text("SELECT COUNT(*) FROM users"))
        if result.scalar() == 0:
            await db.execute(text("INSERT INTO users (id, balance) VALUES ('default-user', 20)"))
            logger.info("Default User erstellt")

    logger.info("🚀 API gestartet - Dashboard unter /dashboard")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
