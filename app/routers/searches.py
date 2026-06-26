from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.core.auth import get_current_user, TokenData
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


class SearchResponse(BaseModel):
    id: int
    name: str
    keyword: str
    location: Optional[str]
    price_min: Optional[int]
    price_max: Optional[int]
    category: Optional[str]
    interval_minutes: int
    callback_url: Optional[str]
    enabled: bool

    class Config:
        from_attributes = True


@router.post("/searches", response_model=dict)
async def create_search(
    data: SearchCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    search = Search(
        user_id=current_user.user_id,
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
    return {"search_id": search.id, "name": search.name, "status": "created"}


@router.get("/searches", response_model=List[SearchResponse])
async def list_searches(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Search).where(Search.user_id == current_user.user_id).order_by(Search.created_at.desc())
    )
    return result.scalars().all()


@router.get("/searches/{search_id}", response_model=SearchResponse)
async def get_search(
    search_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    search = await db.get(Search, search_id)
    if not search:
        raise HTTPException(status_code=404, detail="Suche nicht gefunden")
    if search.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff")
    return search


@router.post("/searches/{search_id}/pause")
async def pause_search(
    search_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    search = await db.get(Search, search_id)
    if not search:
        raise HTTPException(status_code=404, detail="Suche nicht gefunden")
    if search.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff")
    search.enabled = False
    await db.commit()
    return {"status": "paused"}


@router.post("/searches/{search_id}/resume")
async def resume_search(
    search_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    search = await db.get(Search, search_id)
    if not search:
        raise HTTPException(status_code=404, detail="Suche nicht gefunden")
    if search.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff")
    search.enabled = True
    await db.commit()
    return {"status": "resumed"}


@router.delete("/searches/{search_id}")
async def delete_search(
    search_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    search = await db.get(Search, search_id)
    if not search:
        raise HTTPException(status_code=404, detail="Suche nicht gefunden")
    if search.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff")
    await db.delete(search)
    await db.commit()
    return {"status": "deleted"}
