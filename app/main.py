from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import uvicorn
import httpx
from bs4 import BeautifulSoup
import asyncio

app = FastAPI(
    title="Scraper API",
    description="Web Scraper for Kleinanzeigen and others",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "message": "✅ Scraper API is running!",
        "endpoints": {
            "scrape": "/scrape?url=https://www.kleinanzeigen.de/..."
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/dashboard")
async def dashboard():
    return {"status": "ok", "message": "Scraper Dashboard"}

@app.get("/scrape")
async def scrape(
    url: str = Query(..., description="Full URL to scrape")
):
    """
    Scrape a webpage using BeautifulSoup + httpx
    """
    if not url.startswith(("http://", "https://")):
        return JSONResponse(status_code=400, content={"detail": "Invalid URL"})

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract common data (customize for Kleinanzeigen)
        title = soup.find('h1') or soup.find('title')
        title_text = title.get_text(strip=True) if title else None

        price = None
        price_tag = soup.find(string=lambda text: text and '€' in text)
        if price_tag:
            price = price_tag.strip()

        # Kleinanzeigen specific selectors
        description = None
        desc_tag = soup.find('div', {'class': lambda x: x and 'description' in x.lower()}) or \
                   soup.find('p', class_='description')
        if desc_tag:
            description = desc_tag.get_text(strip=True)[:500]

        images = [img['src'] for img in soup.find_all('img', src=True)[:5]]

        return {
            "success": True,
            "url": url,
            "status_code": response.status_code,
            "title": title_text,
            "price": price,
            "description": description,
            "images": images,
            "scraped_at": asyncio.get_event_loop().time()
        }

    except httpx.RequestError as e:
        return JSONResponse(status_code=500, content={"detail": f"Request failed: {str(e)}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Scraping error: {str(e)}"})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
