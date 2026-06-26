"""
Market Intelligence Model — aggregierte Marktdaten aus allen User-Suchen.

Diese Tabelle wird vom Intelligence Worker (intelligence_worker.py)
alle 10 Minuten neu berechnet und dient als Read-Cache für:
  - Deal-Score pro Notification
  - Smart-Interval-Empfehlungen
  - Nachfrage-Heatmap
  - Timing-Intelligenz (später)
"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class MarketStats(Base):
    __tablename__ = "market_stats"

    id = Column(Integer, primary_key=True, index=True)
    keyword_group = Column(String, nullable=False, index=True)
    location_group = Column(String, nullable=True, index=True)
    avg_price = Column(Float, nullable=True)
    median_price = Column(Float, nullable=True)
    min_price = Column(Float, nullable=True)
    max_price = Column(Float, nullable=True)
    total_ads = Column(Integer, default=0)
    ads_last_24h = Column(Integer, default=0)
    active_searches = Column(Integer, default=0)
    price_trend = Column(String, nullable=True)  # "falling", "rising", "stable"
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
