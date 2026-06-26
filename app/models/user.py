from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)  # Google User ID
    email = Column(String, unique=True, index=True, nullable=True)
    balance = Column(Integer, default=20)  # Startguthaben: 20 Tokens
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Beziehung zu Suchen (optional)
    # searches = relationship("Search", back_populates="user")
