"""
Market Intelligence API — Heatmap, Keyword-Detail, Nachfrage-Analyse.

Endpoints:
  GET /market/heatmap       — Marktübersicht aller Keywords
  GET /market/keyword/{kw}  — Detail-Analyse für ein Keyword
  GET /market/competition   — Nachfrage-Heatmap
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.services.market_service import get_heatmap, get_keyword_detail, get_competition

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/heatmap")
async def market_heatmap(
    days: int = Query(7, ge=1, le=90, description="Zeitfenster in Tagen"),
    location: Optional[str] = Query(None, description="Nach Ort filtern (z.B. 'berlin')"),
    limit: int = Query(50, ge=1, le=200, description="Maximale Anzahl Keywords"),
    min_ads: int = Query(3, ge=1, le=100, description="Mindest-Anzahl Anzeigen"),
    db: AsyncSession = Depends(get_db),
):
    """
    Markt-Heatmap: Durchschnittspreis, Nachfrage, Trend pro Keyword.

    Liefert eine Liste aller Keywords mit aggregierten Marktdaten —
    sortiert nach Nachfrage (aktive Suchen) absteigend.

    **Query-Parameter:**
    - **days**: Zeitfenster in Tagen (Default 7)
    - **location**: Optional nach Ort filtern
    - **limit**: Ergebnisse begrenzen (Default 50)
    - **min_ads**: Keywords mit weniger Anzeigen ausblenden (Default 3)
    """
    return await get_heatmap(
        db, days=days, location=location, limit=limit, min_ads=min_ads,
    )


@router.get("/keyword/{keyword}")
async def market_keyword_detail(
    keyword: str,
    days: int = Query(30, ge=1, le=365, description="Zeitfenster in Tagen"),
    location: Optional[str] = Query(None, description="Nach Ort filtern"),
    db: AsyncSession = Depends(get_db),
):
    """
    Detaillierte Marktdaten für EIN Keyword.

    Enthält:
    - Preis-Statistiken pro Location
    - Preis-Historie (aus stündlichen Snapshots)
    - Tag-der-Woche-Analyse (bester Zeitpunkt zum Kaufen)
    - Wettbewerbs-Level

    **Path-Parameter:**
    - **keyword**: Das Keyword (z.B. 'golf-7', 'wohnung-berlin')
    """
    result = await get_keyword_detail(
        db, keyword=keyword, days=days, location=location,
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Keine Marktdaten für '{keyword}' gefunden. "
                    "Entweder gibt es noch keine Anzeigen für dieses Keyword, "
                    "oder die Daten werden gerade vom Intelligence Worker berechnet.",
        )
    return result


@router.get("/competition")
async def market_competition(
    limit: int = Query(20, ge=1, le=100, description="Maximale Ergebnisse"),
    db: AsyncSession = Depends(get_db),
):
    """
    Nachfrage-Heatmap: Welche Keywords werden aktuell am meisten gesucht?

    Sortiert nach Anzahl aktiver Suchen absteigend.
    """
    return await get_competition(db, limit=limit)
