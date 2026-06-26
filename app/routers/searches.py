from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.search import Search
from app.services.scraper_service import trigger_single_search
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class SearchCreate(BaseModel):
    keyword: str
    location: Optional[str] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    category: Optional[str] = None
    name: Optional[str] = None
    interval_minutes: int = 15
    callback_url: Optional[str] = None

@router.post("/searches")
async def create_search(
    data: SearchCreate,
    user_id: str = Header(..., alias="X-User-ID"),
    db: AsyncSession = Depends(get_db)
):
    search = Search(
        user_id=user_id,
        name=data.name or data.keyword,
        keyword=data.keyword,
        location=data.location,
        price_min=data.price_min,
        price_max=data.price_max,
        category=data.category,
        interval_minutes=data.interval_minutes,
        callback_url=data.callback_url,
        enabled=True
    )
    db.add(search)
    await db.commit()
    await db.refresh(search)

    return {"search_id": search.id, "status": "created"}
