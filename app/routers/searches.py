from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from sqlalchemy.sql import expression
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import asyncio
from app.core.database import get_db
from app.models.search import Search
from app.models.seen_ad import SeenAd
from app.models.user import User
from app.services.scraper_service import trigger_single_search, get_price_for_search
from app.core.auth import get_current_active_user

router = APIRouter(prefix="/searches", tags=["searches"])

class SearchCreateRequest(BaseModel):
    keyword: str
    name: Optional[str] = None
    location: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    category: Optional[str] = None
    sort: Optional[str] = "date"
    interval_minutes: Optional[int] = 30
    callback_url: Optional[str] = None

class SearchResponse(BaseModel):
    id: int
    keyword: str
    name: Optional[str]
    location: Optional[str]
    price_min: Optional[float]
    price_max: Optional[float]
    category: Optional[str]
    sort: Optional[str]
    interval_minutes: Optional[int]
    enabled: bool
    last_run: Optional[datetime]
    callback_url: Optional[str]
    created_at: Optional[datetime]
    user_id: Optional[str]
    class Config:
        from_attributes = True

class SearchStatusResponse(BaseModel):
    id: int
    name: str
    keyword: str
    last_run: Optional[datetime]
    enabled: bool
    interval_minutes: int
    ad_count: int
    token_cost: int
    class Config:
        from_attributes = True

async def get_ad_count(db, search_id):
    result = await db.execute(select(func.count(SeenAd.id)).where(SeenAd.search_id == search_id))
    return result.scalar_one_or_none() or 0

@router.get("")
async def list_searches(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    result = await db.execute(select(Search).where(Search.user_id == user.id).order_by(Search.created_at.desc()))
    searches = result.scalars().all()
    responses = []
    for s in searches:
        ad_count = await get_ad_count(db, s.id)
        token_cost = await get_price_for_search(s)
        responses.append(SearchStatusResponse(
            id=s.id, name=s.name or s.keyword, keyword=s.keyword,
            last_run=s.last_run, enabled=s.enabled, interval_minutes=s.interval_minutes,
            ad_count=ad_count, token_cost=token_cost,
        ))
    return responses

@router.post("")
async def create_search(data: SearchCreateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    search = Search(
        keyword=data.keyword, name=data.name or data.keyword, user_id=user.id,
        location=data.location, price_min=data.price_min, price_max=data.price_max,
        category=data.category, sort=data.sort, interval_minutes=data.interval_minutes,
        callback_url=data.callback_url,
    )
    db.add(search)
    await db.commit()
    await db.refresh(search)
    return search

@router.get("/{search_id}")
async def get_search(search_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    result = await db.execute(select(Search).where(Search.id == search_id, Search.user_id == user.id))
    search = result.scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    return search

@router.post("/{search_id}/trigger")
async def trigger_search(search_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    result = await db.execute(select(Search).where(Search.id == search_id, Search.user_id == user.id))
    search = result.scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    background_tasks.add_task(trigger_single_search, search_id, user.id)
    return {"status": "triggered"}

@router.delete("/{search_id}")
async def delete_search(search_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    result = await db.execute(select(Search).where(Search.id == search_id, Search.user_id == user.id))
    search = result.scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    await db.delete(search)
    await db.commit()
    return {"status": "deleted"}

@router.patch("/{search_id}")
async def update_search(search_id: int, data: SearchCreateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    result = await db.execute(select(Search).where(Search.id == search_id, Search.user_id == user.id))
    search = result.scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    if data.name is not None:
        search.name = data.name
    search.enabled = not search.enabled
    await db.commit()
    return {"status": "updated", "enabled": search.enabled}