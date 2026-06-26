from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

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

# Dashboard
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/dashboard", include_in_schema=False)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute("SELECT * FROM searches")
    searches_list = result.fetchall()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "searches": searches_list
    })

@app.on_event("startup")
async def startup_event():
    # Tabellen erstellen (nur für Entwicklung)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("🚀 API gestartet - Dashboard unter /dashboard")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
