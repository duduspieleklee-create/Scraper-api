"""
Intelligence Worker — Aggregiert Cross-User-Marktdaten.

Läuft als separater Prozess (via Docker Compose) und berechnet
alle 10 Minuten:
  1. Deal-Score-Baselines pro Keyword (+Location)
  2. Nachfrage-Heatmap (wie viele User suchen was?)
  3. Smart-Interval-Empfehlungen

Diese Daten fließen in market_stats und werden vom Notification-Layer
gelesen, um jede Benachrichtigung mit Kontext anzureichern.
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger("intelligence")


# ── Hilfsfunktion: Keyword normalisieren ──────────────────────
def normalize_keyword(title: str) -> str:
    """Extrahiere ein normalisiertes Keyword aus einem Anzeigentitel."""
    if not title:
        return "unknown"
    cleaned = re.sub(r"[^a-zA-ZäöüßÄÖÜ0-9 ]", "", title.lower())
    words = cleaned.split()[:4]
    return " ".join(words) if words else "unknown"


async def recalculate_market_stats():
    """Alle 10 Minuten: Komplette Marktstatistik neu berechnen."""
    async with AsyncSessionLocal() as db:
        t0 = datetime.now(timezone.utc)
        logger.info("📊 Marktstatistik-Berechnung gestartet...")

        rows = await db.execute(text("""
            WITH ad_stats AS (
                SELECT
                    LOWER(title) AS raw_title,
                    price,
                    first_seen
                FROM seen_ads
                WHERE price > 0
                  AND title IS NOT NULL
            )
            SELECT
                raw_title,
                COUNT(*)                    AS total,
                COUNT(*) FILTER (
                    WHERE first_seen > NOW() - INTERVAL '24 hours'
                )                            AS recent_24h,
                AVG(price)::FLOAT            AS avg_price,
                PERCENTILE_CONT(0.5)
                    WITHIN GROUP (ORDER BY price) AS median_price,
                MIN(price)::FLOAT            AS min_price,
                MAX(price)::FLOAT            AS max_price
            FROM ad_stats
            GROUP BY raw_title
            HAVING COUNT(*) >= 3
        """))

        search_rows = await db.execute(text("""
            SELECT
                LOWER(keyword) AS kw,
                COUNT(DISTINCT user_id) AS searchers
            FROM searches
            WHERE enabled = TRUE
            GROUP BY LOWER(keyword)
        """))

        search_map = {}
        for row in search_rows:
            search_map[row.kw] = row.searchers

        now = datetime.now(timezone.utc)
        recent = now - timedelta(days=7)
        older = now - timedelta(days=14)

        trend_rows = await db.execute(text("""
            WITH recent_avg AS (
                SELECT
                    LOWER(title) AS kw,
                    AVG(price) AS avg_r
                FROM seen_ads
                WHERE price > 0
                  AND first_seen >= :recent
                GROUP BY LOWER(title)
            ),
            older_avg AS (
                SELECT
                    LOWER(title) AS kw,
                    AVG(price) AS avg_o
                FROM seen_ads
                WHERE price > 0
                  AND first_seen BETWEEN :older_start AND :older_end
                GROUP BY LOWER(title)
            )
            SELECT
                r.kw,
                r.avg_r,
                o.avg_o
            FROM recent_avg r
            LEFT JOIN older_avg o ON r.kw = o.kw
        """), {"recent": recent, "older_start": older, "older_end": recent})

        trend_map = {}
        for row in trend_rows:
            if row.avg_o and row.avg_o > 0:
                change = (row.avg_r - row.avg_o) / row.avg_o * 100
                if change < -5:
                    trend_map[row.kw] = "falling"
                elif change > 5:
                    trend_map[row.kw] = "rising"
                else:
                    trend_map[row.kw] = "stable"
            else:
                trend_map[row.kw] = "stable"

        await db.execute(delete(MarketStats))
        written = 0

        for row in rows:
            kw = normalize_keyword(row.raw_title)
            stats = MarketStats(
                keyword_group=kw,
                location_group=None,
                avg_price=round(row.avg_price, 2) if row.avg_price else None,
                median_price=round(row.median_price, 2) if row.median_price else None,
                min_price=round(row.min_price, 2) if row.min_price else None,
                max_price=round(row.max_price, 2) if row.max_price else None,
                total_ads=row.total,
                ads_last_24h=row.recent_24h,
                active_searches=search_map.get(kw, 0),
                price_trend=trend_map.get(kw, "stable"),
            )
            db.add(stats)
            written += 1

        await db.commit()
        elapsed = (datetime.now(timezone.utc) - t0).total_seconds()
        logger.info(
            "✅ Marktstatistik fertig: %d Keywords in %.1fs",
            written, elapsed,
        )


async def main():
    logger.info("🧠 Intelligence Worker gestartet — läuft alle 10 Minuten")
    while True:
        try:
            await recalculate_market_stats()
        except Exception as exc:
            logger.error("Fehler bei Marktstatistik: %s", exc, exc_info=True)
        await asyncio.sleep(600)


if __name__ == "__main__":
    asyncio.run(main())
