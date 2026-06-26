
from fastapi import FastAPI, Depends, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import psutil
import uvicorn
from typing import List, Dict

from app.routers import searches           # ← this line was missing
from app.routers import auth as auth_router  # ← keep this too
from app.core.database import engine, Base, get_db
from app.models import search, user, token_transaction, seen_ad
from app.models.search import Search
from app.models.seen_ad import SeenAd
from app.models.user import User
from app.models.token_transaction import TokenTransaction
app = FastAPI(
    title="Kleinanzeigen Notifier API",
    description="Automatische Benachrichtigungs-App fuer kleinanzeigen.de",
    version="2.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.globals["timedelta"] = timedelta

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


# ─────────────────────────────────────────────────────────────────────────────
# IMPROVED DASHBOARD ROUTE — copy these changes into app/main.py
# ─────────────────────────────────────────────────────────────────────────────
#
# 1. Add these imports at the top of app/main.py:
#
#    from fastapi import FastAPI, Depends, Request
#    from fastapi.templating import Jinja2Templates
#    from fastapi.staticfiles import StaticFiles
#    from sqlalchemy.ext.asyncio import AsyncSession
#    from sqlalchemy import select, func
#    from datetime import datetime, timedelta
#    import psutil
#
#    from app.core.database import get_db
#    from app.models.search import Search
#    from app.models.seen_ad import SeenAd
#    from app.models.user import User
#    from app.models.token_transaction import TokenTransaction
#
# 2. After creating the FastAPI app, mount static files and set up templates:
#
#    app.mount("/static", StaticFiles(directory="static"), name="static")
#    templates = Jinja2Templates(directory="templates")
#
#    # Expose timedelta in Jinja2 templates (needed for next-run calculation)
#    templates.env.globals["timedelta"] = timedelta
#
# 3. Replace the existing /dashboard route with the one below.
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        # ── Server metrics ────────────────────────────────────────────────
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        memory_percent = mem.percent
        memory_used_gb = round(mem.used / (1024 ** 3), 1)
        memory_total_gb = round(mem.total / (1024 ** 3), 1)
        disk_percent = disk.percent
        disk_used_gb = round(disk.used / (1024 ** 3), 1)
        disk_total_gb = round(disk.total / (1024 ** 3), 1)

        # ── DB: search counts ─────────────────────────────────────────────
        total_searches = await db.scalar(select(func.count(Search.id))) or 0
        active_searches = (
            await db.scalar(
                select(func.count(Search.id)).where(Search.enabled == True)
            )
            or 0
        )
        paused_searches = total_searches - active_searches

        # ── DB: ad counts ─────────────────────────────────────────────────
        total_ads = await db.scalar(select(func.count(SeenAd.id))) or 0
        yesterday = datetime.utcnow() - timedelta(hours=24)
        ads_24h = (
            await db.scalar(
                select(func.count(SeenAd.id)).where(SeenAd.first_seen >= yesterday)
            )
            or 0
        )

        # ── DB: user count ────────────────────────────────────────────────
        total_users = await db.scalar(select(func.count(User.id))) or 0

        # ── DB: tokens spent (sum of all negative transactions) ───────────
        tokens_spent_raw = await db.scalar(
            select(func.sum(TokenTransaction.amount)).where(
                TokenTransaction.amount < 0
            )
        )
        tokens_spent = abs(int(tokens_spent_raw or 0))

        # ── DB: searches with per-search ad counts ────────────────────────
        rows = await db.execute(
            select(Search, func.count(SeenAd.id).label("ad_count"))
            .outerjoin(SeenAd, Search.id == SeenAd.search_id)
            .group_by(Search.id)
            .order_by(Search.created_at.desc())
        )
        searches_with_counts = rows.all()  # list of (Search, int)

        # ── DB: recent ads (last 15) ──────────────────────────────────────
        recent_ads_result = await db.execute(
            select(SeenAd).order_by(SeenAd.first_seen.desc()).limit(15)
        )
        recent_ads = recent_ads_result.scalars().all()

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                # server
                "cpu": cpu,
                "memory_percent": memory_percent,
                "memory_used_gb": memory_used_gb,
                "memory_total_gb": memory_total_gb,
                "disk_percent": disk_percent,
                "disk_used_gb": disk_used_gb,
                "disk_total_gb": disk_total_gb,
                # searches
                "total_searches": total_searches,
                "active_searches": active_searches,
                "paused_searches": paused_searches,
                # ads
                "total_ads": total_ads,
                "ads_24h": ads_24h,
                # users & tokens
                "total_users": total_users,
                "tokens_spent": tokens_spent,
                # tables
                "searches_with_counts": searches_with_counts,
                "recent_ads": recent_ads,
                # time helpers
                "now": datetime.utcnow(),
                "error": None,
            },
        )

    except Exception as exc:
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "error": str(exc),
                # safe defaults so template doesn't crash
                "cpu": 0, "memory_percent": 0, "memory_used_gb": 0,
                "memory_total_gb": 0, "disk_percent": 0, "disk_used_gb": 0,
                "disk_total_gb": 0, "total_searches": 0, "active_searches": 0,
                "paused_searches": 0, "total_ads": 0, "ads_24h": 0,
                "total_users": 0, "tokens_spent": 0,
                "searches_with_counts": [], "recent_ads": [],
                "now": datetime.utcnow(),
            },
        )

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
