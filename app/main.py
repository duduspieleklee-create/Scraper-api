from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict

from app.routers import searches
from app.routers import auth as auth_router
from app.core.database import engine, Base
from app.models import search, user, token_transaction, seen_ad  # alle Modelle registrieren

app = FastAPI(
    title="Kleinanzeigen Notifier API",
    description="Automatische Benachrichtigungs-App fuer kleinanzeigen.de",
    version="2.0.0"
)

# Router einbinden
app.include_router(searches.router)
app.include_router(auth_router.router)

# In-memory storage fuer Dashboard (temporaer)
recent_scrapes: List[Dict] = []


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/")
async def root():
    return {"message": "Kleinanzeigen Notifier API", "docs": "/docs", "dashboard": "/dashboard"}


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    scrapes_html = ""
    for scrape in recent_scrapes[-10:]:
        scrapes_html += f"""
        <div class="scrape-item">
            <strong>{scrape["title"] or "No Title"}</strong><br>
            Preis: {scrape.get("price", "N/A")}<br>
            <small>{scrape["url"][:80]}... | {scrape["timestamp"]}</small>
        </div><hr>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Scraper Dashboard</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f0f2f5; }}
        h1 {{ color: #1a73e8; }}
        .card {{ background: white; padding: 25px; margin: 20px 0; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        input {{ width: 100%; padding: 12px; font-size: 16px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }}
        button {{ padding: 14px 28px; background: #1a73e8; color: white; border: none; border-radius: 8px; cursor: pointer; }}
        .scrape-item {{ margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 6px; }}
    </style>
</head>
<body>
    <h1>Kleinanzeigen Notifier Dashboard</h1>
    <div class="card">
        <h2>Test Scraper</h2>
        <form action="/scrape" method="get" target="_blank">
            <input type="text" name="url" placeholder="Kleinanzeigen URL einfuegen..." required />
            <br><br>
            <button type="submit">Scrape starten</button>
        </form>
    </div>
    <div class="card">
        <h2>Letzte Scrapes ({len(recent_scrapes)})</h2>
        {scrapes_html if scrapes_html else "<p>Noch keine Scrapes.</p>"}
    </div>
    <div class="card">
        <p><a href="/docs">API Docs</a> | <a href="/health">Health</a></p>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.get("/scrape")
async def scrape(url: str = Query(..., description="URL zum Scrapen")):
    if not url.startswith(("http://", "https://")):
        return JSONResponse(status_code=400, content={"detail": "Ungueltige URL"})

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=headers, follow_redirects=True)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else "Kein Titel"

        result = {
            "url": url,
            "title": title_text,
            "status": resp.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
        recent_scrapes.append({**result, "price": None})
        return result

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
