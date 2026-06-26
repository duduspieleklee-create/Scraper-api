# ─────────────────────────────────────────────────────────────────────────────
# NEW FILE — copy to: app/models/worker_heartbeat.py
# Then add to app/models/__init__.py:
#   from app.models import worker_heartbeat
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"

    id = Column(Integer, primary_key=True, index=True)
    worker_name = Column(String, default="main", nullable=False)
    last_seen = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())
    jobs_scheduled = Column(Integer, default=0)
