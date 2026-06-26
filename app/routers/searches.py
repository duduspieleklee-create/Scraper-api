from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.search import Search
from app.services.scraper_service import trigger_single_search
from app.services.token_service import check_token_balance
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
    params: SearchCreate,
    user_id: str = Header(..., alias="X-User-ID"),  # oder aus JWT
    db: AsyncSession = Depends(get_db)
):
    # Token-Check + Validierung
    await check_token_balance(params, user_id)

    # Suche in DB speichern
    search = Search(
        user_id=user_id,
        name=params.name or params.keyword,
        keyword=params.keyword,
        location=params.location,
        price_min=params.price_min,
        price_max=params.price_max,
        category=params.category,
        interval_minutes=params.interval_minutes,
        callback_url=params.callback_url,
        enabled=True
    )
    db.add(search)
    await db.commit()
    await db.refresh(search)

    # Sofort planen
    # await schedule_search(search)  # Optional

    return {
        "search_id": search.id,
        "name": search.name,
        "status": "created"
    }

@router.get("/searches")
async def list_searches(user_id: str = Header(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        "SELECT * FROM searches WHERE user_id = :user_id",
        {"user_id": user_id}
    )
    return result.fetchall()
