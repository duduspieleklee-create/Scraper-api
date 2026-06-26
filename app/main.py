from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(
    title="Scraper API",
    description="Web Scraper API for Kleinanzeigen and others",
    version="1.0.0"
)

# ====================== ROUTES ======================

@app.get("/")
async def root():
    return {
        "message": "✅ Scraper API is running!",
        "endpoints": {
            "root": "/",
            "health": "/health",
            "dashboard": "/dashboard",
            "scrape": "/scrape?url=https://example.com"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "scraper-api"}

@app.get("/dashboard")
async def dashboard():
    return {
        "status": "ok",
        "message": "Welcome to Scraper API Dashboard",
        "version": "1.0.0"
    }

@app.get("/scrape")
async def scrape(
    url: str = Query(..., description="Full URL to scrape (e.g. Kleinanzeigen)")
):
    """
    Scrape a webpage.
    Currently a placeholder - add real scraping logic below.
    """
    if not url.startswith(("http://", "https://")):
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid URL. Must start with http:// or https://"}
        )

    # === PLACEHOLDER - Replace with real scraping later ===
    return {
        "success": True,
        "message": "✅ Scrape request received (placeholder)",
        "url": url,
        "note": "Add BeautifulSoup + httpx here for real data extraction",
        "example_data": {
            "title": "Example Property Title",
            "price": "€ 250.000",
            "location": "Saarland"
        }
    }


# ====================== RUN ======================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=False)
