"""
Market Stats Snapshot — stündliche Zeitreihen-Daten.

Wird vom Intelligence Worker einmal pro Stunde geschrieben,
damit das Frontend Preisverläufe über Tage/Wochen darstellen kann.
Im Gegensatz zu market_stats (Live-View, alle 10 Min überschrieben)
bleiben Snapshots dauerhaft erhalten.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class MarketStatsSnapshot(Base):
    __tablename__ = "market_stats_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    keyword_group = Column(String, nullable=False, index=True)
    location_group = Column(String, nullable=True, index=True)
    avg_price = Column(Float, nullable=True)
    median_price = Column(Float, nullable=True)
    total_ads = Column(Integer, default=0)
    ads_last_24h = Column(Integer, default=0)
    active_searches = Column(Integer, default=0)
    price_trend = Column(String, nullable=True)
    snapshot_hour = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=func.now(),
    )
