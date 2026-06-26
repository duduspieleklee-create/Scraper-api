"""
Market Intelligence Service — Business-Logik für Heatmap & Marktdaten.

Liest aus market_stats (Live-Aggregation, alle 10 Min erneuert) und
market_stats_snapshots (stündliche Snapshots für Zeitreihen).
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, desc

from app.models.market_stats import MarketStats
from app.models.market_stats_snapshot import MarketStatsSnapshot
from app.models.search import Search
from app.models.seen_ad import SeenAd

logger = logging.getLogger(__name__)

# ── Heatmap ─────────────────────────────────────────────────
async def get_heatmap(
    db: AsyncSession,
    days: int = 7,
    location: Optional[str] = None,
    limit: int = 50,
    min_ads: int = 3,
) -> dict:
    """
    Markt-Heatmap: alle Keywords mit Preisdaten, Nachfrage, Trend.

    Args:
        days:       Zeitfenster in Tagen (beeinflusst nur Zusatz-Aggregationen)
        location:   Optionaler Location-Filter
        limit:      Maximale Anzahl Keywords
        min_ads:    Mindestanzahl Anzeigen für Aufnahme
    """
    query = select(MarketStats).where(MarketStats.total_ads >= min_ads)

    if location:
        query = query.where(MarketStats.location_group == location.lower().strip())

    query = query.order_by(desc(MarketStats.active_searches)).limit(limit)
    result = await db.execute(query)
    rows = result.scalars().all()

    # Zusätzlich: aktive Searches live zählen (als Cross-Check)
    search_query = select(
        func.lower(Search.keyword).label("kw"),
        func.count(func.distinct(Search.user_id)).label("cnt")
    ).where(Search.enabled == True).group_by(func.lower(Search.keyword))
    search_result = await db.execute(search_query)
    live_searches = {row.kw: row.cnt for row in search_result}

    data = []
    for row in rows:
        kw = row.keyword_group
        live_cnt = live_searches.get(kw, row.active_searches or 0)
        urgency = _classify_urgency(row.ads_last_24h or 0, live_cnt)

        data.append({
            "keyword": kw,
            "location": row.location_group,
            "avg_price": _safe_round(row.avg_price),
            "median_price": _safe_round(row.median_price),
            "min_price": _safe_round(row.min_price),
            "max_price": _safe_round(row.max_price),
            "total_ads": row.total_ads,
            "ads_last_24h": row.ads_last_24h or 0,
            "ads_per_day": _safe_round((row.ads_last_24h or 0) / 1, 1) if days <= 1 else None,
            "active_searches": live_cnt,
            "price_trend": row.price_trend or "stable",
            "urgency_level": urgency,
        })

    return {
        "data": data,
        "meta": {
            "total_keywords": len(data),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "time_window_days": days,
            "location_filter": location,
        }
    }


# ── Keyword-Detail ──────────────────────────────────────────
async def get_keyword_detail(
    db: AsyncSession,
    keyword: str,
    days: int = 30,
    location: Optional[str] = None,
) -> Optional[dict]:
    """Detaillierte Marktdaten für EIN Keyword — inkl. Location-Split und Historie."""

    kw = keyword.lower().strip()

    # 1. Aktuelle Marktdaten pro Location
    loc_query = select(MarketStats).where(
        MarketStats.keyword_group == kw
    )
    if location:
        loc_query = loc_query.where(MarketStats.location_group == location.lower().strip())
    loc_query = loc_query.order_by(desc(MarketStats.total_ads))
    loc_result = await db.execute(loc_query)
    loc_rows = loc_result.scalars().all()

    if not loc_rows:
        # Fallback: LIKE-Suche
        like_query = select(MarketStats).where(
            MarketStats.keyword_group.contains(kw)
        ).order_by(desc(MarketStats.total_ads)).limit(5)
        like_result = await db.execute(like_query)
        loc_rows = like_result.scalars().all()

    if not loc_rows:
        return None

    locations = []
    for row in loc_rows:
        locations.append({
            "location": row.location_group or "alle",
            "avg_price": _safe_round(row.avg_price),
            "median_price": _safe_round(row.median_price),
            "min_price": _safe_round(row.min_price),
            "max_price": _safe_round(row.max_price),
            "total_ads": row.total_ads,
            "ads_last_24h": row.ads_last_24h or 0,
            "active_searches": row.active_searches or 0,
            "trend": row.price_trend or "stable",
        })

    # 2. Preis-Historie aus Snapshots
    since = datetime.now(timezone.utc) - timedelta(days=days)
    snap_query = (
        select(MarketStatsSnapshot)
        .where(
            MarketStatsSnapshot.keyword_group == kw,
            MarketStatsSnapshot.snapshot_hour >= since,
        )
        .order_by(MarketStatsSnapshot.snapshot_hour.asc())
    )
    snap_result = await db.execute(snap_query)
    snap_rows = snap_result.scalars().all()

    price_history = []
    for snap in snap_rows:
        price_history.append({
            "hour": snap.snapshot_hour.isoformat(),
            "avg_price": _safe_round(snap.avg_price),
            "total_ads": snap.total_ads,
            "active_searches": snap.active_searches,
        })

    # 3. Tag-der-Woche Analyse aus SeenAd
    weekday_query = await db.execute(text("""
        SELECT
            EXTRACT(DOW FROM first_seen)::int AS dow,
            AVG(price)::FLOAT AS avg_price,
            COUNT(*)::int AS cnt
        FROM seen_ads
        WHERE price > 0
          AND title ILIKE :kw_pattern
          AND first_seen >= :since
        GROUP BY dow
        ORDER BY dow
    """), {"kw_pattern": f"%{kw}%", "since": since})
    day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    day_of_week = []
    for row in weekday_query:
        day_of_week.append({
            "day": day_names[row.dow] if 0 <= row.dow <= 6 else str(row.dow),
            "avg_price": _safe_round(row.avg_price),
            "avg_count": row.cnt,
        })

    # 4. Wettbewerb
    total_competition = sum(loc["active_searches"] for loc in locations)
    competition_level = "intense" if total_competition >= 20 else \
                        "high" if total_competition >= 10 else \
                        "moderate" if total_competition >= 3 else "low"

    return {
        "keyword": kw,
        "locations": locations,
        "price_history": price_history,
        "day_of_week": day_of_week,
        "competition": {
            "active_searches": total_competition,
            "level": competition_level,
        },
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "time_window_days": days,
        },
    }


# ── Competition Heatmap ─────────────────────────────────────
async def get_competition(
    db: AsyncSession,
    limit: int = 20,
) -> dict:
    """Nachfrage-Heatmap: welche Keywords werden am meisten gesucht?"""
    query = (
        select(MarketStats)
        .where(MarketStats.active_searches > 0)
        .order_by(desc(MarketStats.active_searches), desc(MarketStats.total_ads))
        .limit(limit)
    )
    result = await db.execute(query)
    rows = result.scalars().all()

    data = []
    for row in rows:
        level = "intense" if (row.active_searches or 0) >= 20 else \
                "high" if (row.active_searches or 0) >= 10 else \
                "moderate" if (row.active_searches or 0) >= 3 else "low"
        data.append({
            "keyword": row.keyword_group,
            "active_searches": row.active_searches,
            "total_ads": row.total_ads,
            "ads_last_24h": row.ads_last_24h or 0,
            "avg_price": _safe_round(row.avg_price),
            "level": level,
        })

    return {
        "data": data,
        "meta": {
            "total_keywords": len(data),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }


# ── Helfer ──────────────────────────────────────────────────
def _safe_round(value, decimals=2):
    if value is None:
        return None
    return round(float(value), decimals)


def _classify_urgency(ads_24h: int, active_searches: int) -> str:
    score = 0
    if ads_24h >= 20:
        score += 2
    elif ads_24h >= 5:
        score += 1
    if active_searches >= 20:
        score += 2
    elif active_searches >= 5:
        score += 1

    if score >= 4:
        return "intense"
    elif score >= 2:
        return "high"
    elif score >= 1:
        return "moderate"
    return "low"
