import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


from fastapi import FastAPI
from app.routers import searches
from app.core.database import engine, Base

app = FastAPI(
    title="Kleinanzeigen Scraper API",
    version="1.0.0"
)

app.include_router(searches.router, prefix="/api/v1", tags=["searches"])

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
