from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn
import httpx
from bs4 import BeautifulSoup

app = FastAPI(
    title="Scraper API",
    description="Kleinanzeigen & General Web Scraper",
    version="1.0.0"
)

# ====================== DASHBOARD ======================
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Scraper API Dashboard</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f0f2f5; }
        h1 { color: #1a73e8; }
        .card { background: white; padding: 25px; margin: 20px 0; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        input { width: 100%; padding: 12px; font-size: 16px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
        button { padding: 14px 28px; background: #1a73e8; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; }
        button:hover { background: #1557b0; }
        pre { background: #f8f9fa; padding: 15px; border-radius: 8px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>🛠️ Scraper API Dashboard</h1>
    
    <div class="card">
        <h2>Test the Scraper</h2>
        <form action="/scrape" method="get" target="_blank">
            <input type="text" name="url" placeholder="Paste full URL here (Kleinanzeigen, etc.)" required />
            <br><br>
            <button type="submit">🚀 Scrape Now</button>
        </form>
    </div>

    <div class="card">
        <h2>Quick Links</h2>
        <p><a href="/">Home</a> | <a href="/health">Health Check</a> | <a href="/docs">API Docs</a></p>
    </div>

    <div class="card">
        <h2>Example</h2>
        <pre>https://scraper-api-syx8.onrender.com/scrape?url=https://www.kleinanzeigen.de/s-immobilien/saarland/haus/k0c195l285</pre>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)

# ====================== OTHER ROUTES ======================
@app.get("/")
async def root():
    return {
        "message": "✅ Scraper API is running!",
        "dashboard": "/dashboard",
        "scrape": "/scrape?url=..."
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/scrape")
async def scrape(
    url: str = Query(..., description="URL to scrape")
):
    if not url.startswith(("http://", "https://")):
        return JSONResponse(status_code=400, content={"detail": "Invalid URL"})

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=headers, follow_redirects=True)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        title_tag = soup.find("h1") or soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None

        price = None
        for text in soup.find_all(string=True):
            if "€" in text and len(text.strip()) < 50:
                price = text.strip()
                break

        description = None
        desc_tag = soup.find("div", class_=lambda x: x and "description" in str(x).lower()) or soup.find("p")
        if desc_tag:
            description = desc_tag.get_text(strip=True)[:600]

        images = [img.get("src") or img.get("data-src") for img in soup.find_all("img")[:8] if img.get("src") or img.get("data-src")]

        return {
            "success": True,
            "url": url,
            "title": title,
            "price": price,
            "short_description": description,
            "images": images,
            "status_code": resp.status_code
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Error: {str(e)}"})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
