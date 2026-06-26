"""
Deal-Scoring & Markt-Intelligenz.

Jedes neue Ad bekommt einen Deal-Score (0-100), basierend auf:
  1. Preis vs. Marktdurchschnitt (aus market_stats)
  2. Alter der Anzeige (je frischer, desto höher)
  3. Wettbewerb (wie viele andere User suchen das gleiche)

Je höher der Score, desto dringender sollte der User reagieren.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.market_stats import MarketStats

logger = logging.getLogger(__name__)


# ── Score-Gewichte ──────────────────────────────────────────────
PRICE_DISCOUNT_WEIGHT = 0.45   # Preis unter Marktdurchschnitt
FRESHNESS_WEIGHT = 0.35        # Anzeigenalter
COMPETITION_WEIGHT = 0.20      # Wettbewerbsintensität


async def get_market_stats(
    db: AsyncSession, keyword: str, location: Optional[str] = None
) -> Optional[MarketStats]:
    """Hole aggregierte Marktdaten für ein Keyword (ggf. + Location)."""
    # 1. Exakter Match: Keyword + Location
    if location:
        result = await db.execute(
            select(MarketStats).where(
                MarketStats.keyword_group == keyword.lower().strip(),
                MarketStats.location_group == location.lower().strip(),
            )
        )
        stat = result.scalar_one_or_none()
        if stat:
            return stat

    # 2. Fallback: Nur Keyword
    result = await db.execute(
        select(MarketStats).where(
            MarketStats.keyword_group == keyword.lower().strip()
        )
    )
    stat = result.scalar_one_or_none()
    if stat:
        return stat

    # 3. Broad fallback: keyword contains
    result = await db.execute(
        select(MarketStats).where(
            MarketStats.keyword_group.contains(keyword.lower().strip())
        )
    )
    return result.scalar_one_or_none()


async def calculate_deal_score(
    db: AsyncSession,
    ad: dict,
    keyword: str,
    location: Optional[str] = None,
) -> int:
    """
    Berechne Deal-Score (0-100) für eine einzelne Anzeige.

    Rückgabe:
        90-100: 🔥🔥🔥 Sofort handeln
        70-89:  🔥🔥  Guter Deal
        50-69:  🔥    Interessant
        0-49:   Keine Eile
    """
    score = 50  # Basis-Score (neutral)
    details = []

    # ── 1. Preis vs. Markt ──────────────────────────────────
    stats = await get_market_stats(db, keyword, location)
    price = ad.get("price")

    if stats and stats.avg_price and price:
        discount_pct = (1 - price / stats.avg_price) * 100

        if discount_pct >= 30:
            score += int(PRICE_DISCOUNT_WEIGHT * 100)
            details.append(f"{discount_pct:.0f}% UNTER Marktdurchschnitt")
        elif discount_pct >= 20:
            score += int(PRICE_DISCOUNT_WEIGHT * 80)
            details.append(f"{discount_pct:.0f}% unter Durchschnitt")
        elif discount_pct >= 10:
            score += int(PRICE_DISCOUNT_WEIGHT * 50)
            details.append(f"{discount_pct:.0f}% unter Durchschnitt")
        elif discount_pct >= 0:
            score += int(PRICE_DISCOUNT_WEIGHT * 20)
        else:
            # Über Durchschnitt → leichter Abzug
            score -= min(int(PRICE_DISCOUNT_WEIGHT * 20), 10)
    elif not stats:
        score -= 10  # Keine Marktdaten → konservativ
        details.append("Noch keine Vergleichsdaten")

    # ── 2. Frische der Anzeige ──────────────────────────────
    first_seen = ad.get("first_seen")
    if isinstance(first_seen, str):
        try:
            first_seen = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            first_seen = datetime.now(timezone.utc)

    if first_seen:
        age_seconds = (datetime.now(timezone.utc) - first_seen).total_seconds()

        if age_seconds < 120:       # < 2 Minuten
            score += int(FRESHNESS_WEIGHT * 100)
            details.append("Gerade eingestellt")
        elif age_seconds < 600:     # < 10 Minuten
            score += int(FRESHNESS_WEIGHT * 80)
            details.append(f"Vor {int(age_seconds/60)} Min")
        elif age_seconds < 1800:    # < 30 Minuten
            score += int(FRESHNESS_WEIGHT * 50)
            details.append(f"Vor {int(age_seconds/60)} Min")
        elif age_seconds < 7200:    # < 2 Stunden
            score += int(FRESHNESS_WEIGHT * 20)
        else:
            score -= 5  # Älter als 2h → leichter Abzug

    # ── 3. Wettbewerbs-Druck ────────────────────────────────
    if stats and stats.active_searches:
        competitors = stats.active_searches

        if competitors >= 20:
            score += int(COMPETITION_WEIGHT * 100)
            details.append(f"{competitors} andere suchen das auch")
        elif competitors >= 10:
            score += int(COMPETITION_WEIGHT * 70)
            details.append(f"{competitors} Mit-Suchende")
        elif competitors >= 3:
            score += int(COMPETITION_WEIGHT * 30)
        # Wenige Sucher = weniger Druck, neutraler Score

    score = max(0, min(100, score))
    return score


def get_urgency_label(score: int) -> str:
    if score >= 90:
        return "🔥🔥🔥"
    elif score >= 70:
        return "🔥🔥"
    elif score >= 50:
        return "🔥"
    return ""


def get_freshness_label(first_seen) -> str:
    """Menschlich lesbare Zeitangabe."""
    if not first_seen:
        return ""
    if isinstance(first_seen, str):
        try:
            first_seen = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return ""

    age_seconds = (datetime.now(timezone.utc) - first_seen).total_seconds()

    if age_seconds < 60:
        return "gerade eben"
    elif age_seconds < 120:
        return "vor 1 Minute"
    elif age_seconds < 600:
        return f"vor {int(age_seconds / 60)} Minuten"
    elif age_seconds < 3600:
        return f"vor {int(age_seconds / 60)} Minuten"
    elif age_seconds < 7200:
        return "vor 1 Stunde"
    else:
        return f"vor {int(age_seconds / 3600)} Stunden"


async def get_competition_count(db: AsyncSession, keyword: str) -> int:
    """Wie viele andere User suchen aktuell nach diesem Keyword?"""
    stats = await get_market_stats(db, keyword)
    if stats and stats.active_searches:
        return max(0, stats.active_searches - 1)  # Minus 1 für den User selbst
    return 0
