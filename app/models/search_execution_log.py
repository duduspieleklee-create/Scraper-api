from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class SearchExecutionLog(Base):
    __tablename__ = "search_execution_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    search_id = Column(Integer, ForeignKey("searches.id"), nullable=False)
    executed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
