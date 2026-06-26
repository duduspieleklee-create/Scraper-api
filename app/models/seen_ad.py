from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class SeenAd(Base):
    __tablename__ = "seen_ads"

    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(Integer, nullable=False, index=True)
    ad_id = Column(String, nullable=False)
    title = Column(String, nullable=True)
    price = Column(Integer, nullable=True)
    link = Column(String, nullable=True)
    first_seen = Column(DateTime(timezone=True), server_default=func.now())

    # Eindeutig pro Suche + Anzeige
    __table_args__ = (
        UniqueConstraint("search_id", "ad_id", name="uq_seen_ad"),
    )
