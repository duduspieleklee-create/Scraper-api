from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import uvicorn
import httpx
import asyncio
from typing import Optional

app = FastAPI(
    title="Scraper API",
    description="Simple web scraper API",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "message": "Scraper API is running! 🚀",
        "endpoints": {
            "scrape": "/scrape?url=https://example.com",
            "dashboard": "/dashboard",
            "health": "/health"
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
    url: str = Query(..., description="URL to scrape"),
    timeout: int = Query(30, description="Request timeout in seconds")
):
    """
    Scrape a webpage and return basic information.
    """
    if not url.startswith("http"):
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid URL. Must start with http:// or https://"}
        )
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            return {
                "success": True,
                "url": url,
                "status_code": response.status_code,
                "title": response.text.split("<title>")[1].split("</title>")[0] if "<title>" in response.text else None,
                "content_length": len(response.text),
                "scraped_at": asyncio.get_event_loop().time()  # placeholder
            }
            
    except httpx.RequestError as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to scrape: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error: {str(e)}"}
        )

# Run with: uvicorn main:app --reload --port 10000
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
