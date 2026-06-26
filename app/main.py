from fastapi import FastAPI
from app.routers import searches
from app.core.database import engine, Base
import asyncio

app = FastAPI(
    title="Kleinanzeigen Notifier API",
    description="API für automatisierte Kleinanzeigen-Suchen",
    version="1.0.0"
)

# Router einbinden
app.include_router(searches.router, prefix="/api/v1", tags=["searches"])

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    # Tabellen erstellen (bei Entwicklung)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
