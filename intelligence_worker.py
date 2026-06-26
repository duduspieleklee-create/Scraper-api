"""
Intelligence Worker — Aggregiert Cross-User-Marktdaten.

Läuft als separater Prozess (via Docker Compose) und berechnet
alle 10 Minuten:
  1. Deal-Score-Baselines pro Keyword + Location
  2. Nachfrage-Heatmap (wie viele User suchen was?)
  3. Smart-Interval-Empfehlungen

Schreibt stündlich Snapshots in market_stats_snapshots für Zeitreihen.

Diese Daten fließen in market_stats und werden vom Notification-Layer
sowie der Market-API (GET /market/heatmap) gelesen.
"""

import asyncio
import logging
import re
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, text, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.seen_ad import SeenAd
from app.models.search import Search
from app.models.market_stats import MarketStats
from app.models.market_stats_snapshot import MarketStatsSnapshot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger("intelligence")

def normalize_keyword(title: str) -> str:
    if not title:
        return "unknown"
    cleaned = re.sub(r"[^a-zA-ZäöüßÄÖÜ0-9 ]", "", title.lower())
    words = cleaned.split()[:4]
    return " ".join(words) if words else "unknown"

def normalize_location(location_str: str) -> str | None:
    if not location_str:
        return None
    cleaned = re.sub(r"[^a-zA-ZäöüßÄÖÜ0-9 \-]", "", location_str.lower().strip())
    parts = re.split(r"[\-/,]", cleaned)
    return parts[0].strip() if parts[0].strip() else None

_last_snapshot_hour: int | None = None

def should_write_snapshot() -> bool:
    global _last_snapshot_hour
    current_hour = datetime.now(timezone.utc).hour
    if _last_snapshot_hour != current_hour:
        _last_snapshot_hour = current_hour
        return True
    return False

async def _calculate_trend(db: AsyncSession, keyword: str, location: str | None) -> str:
    now = datetime.now(timezone.utc)
    recent = now - timedelta(days=7)
    older = now - timedelta(days=14)
    recent_avg = await db.scalar(
        select(func.avg(SeenAd.price)).where(
            SeenAd.first_seen >= recent, SeenAd.price > 0,
            SeenAd.title.ilike(f"%{keyword}%"),
        )
    )
    older_avg = await db.scalar(
        select(func.avg(SeenAd.price)).where(
            SeenAd.first_seen.between(older, recent), SeenAd.price > 0,
            SeenAd.title.ilike(f"%{keyword}%"),
        )
    )
    if not recent_avg or not older_avg or older_avg == 0:
        return "stable"
    change_pct = (recent_avg - older_avg) / older_avg * 100
    if change_pct < -5:
        return "falling"
    elif change_pct > 5:
        return "rising"
    return "stable"

async def recalculate_market_stats():
    async with AsyncSessionLocal() as db:
        t0 = datetime.now(timezone.utc)
        logger.info("📊 Marktstatistik-Berechnung gestartet...")
        rows = await db.execute(text("""
            WITH ad_data AS (
                SELECT title, price, first_seen
                FROM seen_ads
                WHERE price > 0 AND title IS NOT NULL
            )
            SELECT
                LOWER(REGEXP_REPLACE(
                    SPLIT_PART(title, ' ', 1) || ' ' ||
                    COALESCE(SPLIT_PART(title, ' ', 2), '') || ' ' ||
                    COALESCE(SPLIT_PART(title, ' ', 3), ''),
                    '[^a-zA-ZäöüßÄÖÜ0-9 ]', '', 'g'
                )) AS kw_group,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE first_seen > NOW() - INTERVAL '24 hours') AS recent_24h,
                AVG(price)::FLOAT AS avg_price,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) AS median_price,
                MIN(price)::FLOAT AS min_price,
                MAX(price)::FLOAT AS max_price
            FROM ad_data
            GROUP BY kw_group
            HAVING COUNT(*) >= 3
        """))
        kw_data = {}
        for row in rows:
            kw_data[row.kw_group] = {
                "total": row.total, "recent_24h": row.recent_24h,
                "avg_price": row.avg_price, "median_price": row.median_price,
                "min_price": row.min_price, "max_price": row.max_price,
            }
        search_rows = await db.execute(text("""
            SELECT LOWER(keyword) AS kw, LOWER(COALESCE(location, '')) AS loc,
                   COUNT(DISTINCT user_id) AS searchers
            FROM searches WHERE enabled = TRUE
            GROUP BY LOWER(keyword), LOWER(COALESCE(location, ''))
        """))
        search_map = {}
        kw_total_search_map = {}
        for row in search_rows:
            loc = normalize_location(row.loc)
            key = (row.kw, loc)
            search_map[key] = row.searchers
            kw_total_search_map[row.kw] = kw_total_search_map.get(row.kw, 0) + row.searchers
        trend_map = {}
        for kw in list(kw_data.keys())[:50]:
            trend = await _calculate_trend(db, kw, None)
            trend_map[kw] = trend
        await db.execute(delete(MarketStats))
        written = 0
        for kw, data in kw_data.items():
            locations_to_write = set()
            for (skw, sloc), cnt in search_map.items():
                if skw == kw:
                    locations_to_write.add(sloc)
            if not locations_to_write:
                locations_to_write.add(None)
            for loc in locations_to_write:
                key = (kw, loc)
                searchers = search_map.get(key, 0)
                stats = MarketStats(
                    keyword_group=kw, location_group=loc,
                    avg_price=round(data["avg_price"], 2) if data["avg_price"] else None,
                    median_price=round(data["median_price"], 2) if data["median_price"] else None,
                    min_price=round(data["min_price"], 2) if data["min_price"] else None,
                    max_price=round(data["max_price"], 2) if data["max_price"] else None,
                    total_ads=data["total"], ads_last_24h=data["recent_24h"],
                    active_searches=searchers, price_trend=trend_map.get(kw, "stable"),
                )
                db.add(stats)
                written += 1
        await db.commit()
        elapsed = (datetime.now(timezone.utc) - t0).total_seconds()
        logger.info("✅ Marktstatistik fertig: %d Einträge in %.1fs", written, elapsed)
        if should_write_snapshot():
            await write_hourly_snapshot(db)

async def write_hourly_snapshot(db: AsyncSession):
    result = await db.execute(select(MarketStats))
    rows = result.scalars().all()
    now = datetime.now(timezone.utc)
    written = 0
    for row in rows:
        snap = MarketStatsSnapshot(
            keyword_group=row.keyword_group, location_group=row.location_group,
            avg_price=row.avg_price, median_price=row.median_price,
            total_ads=row.total_ads, ads_last_24h=row.ads_last_24h,
            active_searches=row.active_searches, price_trend=row.price_trend,
            snapshot_hour=now.replace(minute=0, second=0, microsecond=0),
        )
        db.add(snap)
        written += 1
    await db.commit()
    logger.info("📸 Snapshot geschrieben: %d Zeilen für %s", written, now.isoformat())

async def main():
    logger.info("🧠 Intelligence Worker gestartet — alle 10 Min, Snapshots stündlich")
    while True:
        try:
            await recalculate_market_stats()
        except Exception as exc:
            logger.error("Fehler bei Marktstatistik: %s", exc, exc_info=True)
        await asyncio.sleep(600)

if __name__ == "__main__":
    asyncio.run(main())
