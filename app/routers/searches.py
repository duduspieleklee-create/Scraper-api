from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models.search import Search

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

    return {
        "search_id": search.id,
        "name": search.name,
        "status": "created"
    }

@router.get("/searches")
async def list_searches(
    user_id: str = Header(..., alias="X-User-ID"),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        "SELECT * FROM searches WHERE user_id = :user_id ORDER BY created_at DESC",
        {"user_id": user_id}
    )
    return result.fetchall()

@router.post("/searches/{search_id}/pause")
async def pause_search(search_id: int, db: AsyncSession = Depends(get_db)):
    search = await db.get(Search, search_id)
    if not search:
        raise HTTPException(status_code=404, detail="Suche nicht gefunden")
    search.enabled = False
    await db.commit()
    return {"status": "paused"}

@router.post("/searches/{search_id}/resume")
async def resume_search(search_id: int, db: AsyncSession = Depends(get_db)):
    search = await db.get(Search, search_id)
    if not search:
        raise HTTPException(status_code=404, detail="Suche nicht gefunden")
    search.enabled = True
    await db.commit()
    return {"status": "resumed"}
