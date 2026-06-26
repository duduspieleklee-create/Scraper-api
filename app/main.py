
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
import os
from app.models.worker_heartbeat import WorkerHeartbeat   # NEW — see worker_heartbeat_model.py
from app.routers import searches           # ← this line was missing
from app.routers import auth as auth_router  # ← keep this too
from app.routers import proxies
from app.routers.dashboard_proxy import router as dashboard_proxy_router
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
app.include_router(proxies.router)
app.include_router(dashboard_proxy_router)

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


# ──────────────────────────────────────────────────────────────────[...]
# IMPROVED DASHBOARD ROUTE — copy these changes into app/main.py
# ──────────────────────────────────────────────────────────────────[...]
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
# ──────────────────────────────────────────────────────────────────[...]

# ──────────────────────────────────────────────────────────────────[...]
# IMPROVED DASHBOARD ROUTE — copy these changes into app/main.py
# ──────────────────────────────────────────────────────────────────[...]
#
# 1. Add/update imports at the top of app/main.py:
#
#   from fastapi import FastAPI, Depends, Request, Query
#   from fastapi.responses import JSONResponse, HTMLResponse
#   from fastapi.templating import Jinja2Templates
#   from fastapi.staticfiles import StaticFiles
#   from sqlalchemy.ext.asyncio import AsyncSession
#   from sqlalchemy import select, func
#   from datetime import datetime, timedelta
#   import psutil, os
#
#   from app.core.database import get_db
#   from app.models.search import Search
#   from app.models.seen_ad import SeenAd
#   from app.models.user import User
#   from app.models.token_transaction import TokenTransaction
#   from app.models.worker_heartbeat import WorkerHeartbeat   # NEW — see worker_heartbeat_model.py
#
# 2. After app = FastAPI(...), add:
#
#   app.mount("/static", StaticFiles(directory="static"), name="static")
#   templates = Jinja2Templates(directory="templates")
#   templates.env.globals["timedelta"] = timedelta
#
# 3. Replace the /dashboard route with the one below.
#    NOTE: uses the new Starlette TemplateResponse keyword-argument style.
# ─────────────────────────────────────────────────────────────────[...]


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        now = datetime.utcnow()

        # ── Server metrics ────────────────────────────────────────────────
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        proc = psutil.Process(os.getpid())
        uptime_secs = int(now.timestamp() - proc.create_time())
        h, rem = divmod(uptime_secs, 3600)
        m, s = divmod(rem, 60)
        uptime_str = f"{h}h {m}m {s}s" if h else f"{m}m {s}s"
        pid = proc.pid

        # ── DB connectivity check ─────────────────────────────────────────
        try:
            await db.scalar(select(func.count(Search.id)))
            db_ok = True
        except Exception:
            db_ok = False

        # ── Worker heartbeat ──────────────────────────────────────────────
        worker_online = False
        worker_last_seen_str = None
        try:
            last_hb = await db.scalar(
                select(WorkerHeartbeat.last_seen)
                .order_by(WorkerHeartbeat.last_seen.desc())
                .limit(1)
            )
            if last_hb:
                age_secs = int((now - last_hb).total_seconds())
                if age_secs < 120:
                    worker_online = True
                    worker_last_seen_str = f"vor {age_secs}s"
                else:
                    mins = age_secs // 60
                    worker_last_seen_str = f"vor {mins} Min"
        except Exception:
            pass  # Table not yet created — shown as "no heartbeat"

        # ── Search counts ─────────────────────────────────────────────────
        total_searches = await db.scalar(select(func.count(Search.id))) or 0
        active_searches = (
            await db.scalar(select(func.count(Search.id)).where(Search.enabled == True)) or 0
        )
        paused_searches = total_searches - active_searches

        # ── Ad counts ─────────────────────────────────────────────────────
        total_ads = await db.scalar(select(func.count(SeenAd.id))) or 0
        yesterday = now - timedelta(hours=24)
        ads_24h = (
            await db.scalar(select(func.count(SeenAd.id)).where(SeenAd.first_seen >= yesterday)) or 0
        )

        # ── Users ─────────────────────────────────────────────────────────
        total_users = await db.scalar(select(func.count(User.id))) or 0

        # ── Token spend: total + last 24h ─────────────────────────────────
        tokens_spent_raw = await db.scalar(
            select(func.sum(TokenTransaction.amount)).where(TokenTransaction.amount < 0)
        )
        tokens_spent = abs(int(tokens_spent_raw or 0))

        tokens_24h_raw = await db.scalar(
            select(func.sum(TokenTransaction.amount)).where(
                TokenTransaction.amount < 0,
                TokenTransaction.created_at >= yesterday,
            )
        )
        tokens_24h = abs(int(tokens_24h_raw or 0))

        # ── Webhook stats (from token_transaction reason field) ───────────
        # Counts rows with reason containing "webhook" grouped by success/fail
        from sqlalchemy import case, literal_column
        wh_result = await db.execute(
            select(
                func.count(TokenTransaction.id).label("total"),
                func.sum(
                    case((TokenTransaction.reason.ilike("%webhook_ok%"), 1), else_=0)
                ).label("ok"),
                func.sum(
                    case((TokenTransaction.reason.ilike("%webhook_fail%"), 1), else_=0)
                ).label("fail"),
            )
        )
        wh_row = wh_result.first()
        webhook_ok = int(wh_row.ok or 0)
        webhook_fail = int(wh_row.fail or 0)

        # ── Ads per day — last 7 days ─────────────────────────────────────
        from sqlalchemy import cast, Date as SQLDate, text
        ads_per_day_raw = await db.execute(
            select(
                cast(SeenAd.first_seen, SQLDate).label("day"),
                func.count(SeenAd.id).label("cnt"),
            )
            .where(SeenAd.first_seen >= now - timedelta(days=7))
            .group_by("day")
            .order_by("day")
        )
        day_map = {str(row.day): row.cnt for row in ads_per_day_raw}
        ads_per_day = []
        for i in range(6, -1, -1):
            d = (now - timedelta(days=i)).date()
            label = d.strftime("%d.%m")
            ads_per_day.append((label, day_map.get(str(d), 0)))

        # ── Top searches by ad count ──────────────────────────────────────
        top_rows = await db.execute(
            select(Search, func.count(SeenAd.id).label("ad_count"))
            .outerjoin(SeenAd, Search.id == SeenAd.search_id)
            .group_by(Search.id)
            .order_by(func.count(SeenAd.id).desc())
            .limit(5)
        )
        top_searches = top_rows.all()

        # ── Price stats ───────────────────────────────────────────────────
        price_row = await db.execute(
            select(
                func.min(SeenAd.price).label("mn"),
                func.max(SeenAd.price).label("mx"),
                func.avg(SeenAd.price).label("av"),
                func.count(SeenAd.price).label("cnt"),
            ).where(SeenAd.price.isnot(None), SeenAd.price > 0)
        )
        pr = price_row.first()
        price_min = int(pr.mn) if pr.mn is not None else None
        price_max = int(pr.mx) if pr.mx is not None else None
        price_avg = round(float(pr.av), 2) if pr.av is not None else None
        price_count = int(pr.cnt) if pr.cnt else 0

        # ── Searches with per-search ad counts ───────────────────────────
        rows = await db.execute(
            select(Search, func.count(SeenAd.id).label("ad_count"))
            .outerjoin(SeenAd, Search.id == SeenAd.search_id)
            .group_by(Search.id)
            .order_by(Search.created_at.desc())
        )
        searches_with_counts = rows.all()

        # ── Recent ads ────────────────────────────────────────────────────
        recent_ads_result = await db.execute(
            select(SeenAd).order_by(SeenAd.first_seen.desc()).limit(15)
        )
        recent_ads = recent_ads_result.scalars().all()

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                # api status
                "uptime_str": uptime_str,
                "pid": pid,
                "db_ok": db_ok,
                # worker
                "worker_online": worker_online,
                "worker_last_seen_str": worker_last_seen_str,
                # server
                "cpu": cpu,
                "memory_percent": mem.percent,
                "memory_used_gb": round(mem.used / (1024 ** 3), 1),
                "memory_total_gb": round(mem.total / (1024 ** 3), 1),
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024 ** 3), 1),
                "disk_total_gb": round(disk.total / (1024 ** 3), 1),
                # searches
                "total_searches": total_searches,
                "active_searches": active_searches,
                "paused_searches": paused_searches,
                # ads
                "total_ads": total_ads,
                "ads_24h": ads_24h,
                "ads_per_day": ads_per_day,
                # users & tokens
                "total_users": total_users,
                "tokens_spent": tokens_spent,
                "tokens_24h": tokens_24h,
                # webhooks
                "webhook_ok": webhook_ok,
                "webhook_fail": webhook_fail,
                # top searches
                "top_searches": top_searches,
                # price stats
                "price_min": price_min,
                "price_max": price_max,
                "price_avg": price_avg,
                "price_count": price_count,
                # tables
                "searches_with_counts": searches_with_counts,
                "recent_ads": recent_ads,
                # time
                "now": now,
                "error": None,
            },
        )

    except Exception as exc:
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "error": str(exc),
                "uptime_str": "—", "pid": "—", "db_ok": False,
                "worker_online": False, "worker_last_seen_str": None,
                "cpu": 0, "memory_percent": 0, "memory_used_gb": 0,
                "memory_total_gb": 0, "disk_percent": 0, "disk_used_gb": 0,
                "disk_total_gb": 0, "total_searches": 0, "active_searches": 0,
                "paused_searches": 0, "total_ads": 0, "ads_24h": 0,
                "ads_per_day": [], "total_users": 0, "tokens_spent": 0,
                "tokens_24h": 0, "webhook_ok": 0, "webhook_fail": 0,
                "top_searches": [], "price_min": None, "price_max": None,
                "price_avg": None, "price_count": 0,
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
