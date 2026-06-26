from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List

from app.core.database import get_db
from app.models.proxy import Proxy

router = APIRouter(prefix="/proxies", tags=["proxies"])


class ProxyCreateRequest(BaseModel):
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    country: Optional[str] = None

class ProxyResponse(BaseModel):
    id: int
    url: str
    username: Optional[str]
    protocol: str
    country: Optional[str]
    status: str
    fail_count: int
    success_count: int
    last_used: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[ProxyResponse])
async def list_proxies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proxy).order_by(Proxy.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=ProxyResponse)
async def add_proxy(data: ProxyCreateRequest, db: AsyncSession = Depends(get_db)):
    # Check if already exists
    existing = await db.execute(select(Proxy).where(Proxy.url == data.url))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Proxy with this URL already exists")

    proxy = Proxy(
        url=data.url,
        username=data.username,
        password=data.password,
        protocol=data.protocol,
        country=data.country,
    )
    db.add(proxy)
    await db.commit()
    await db.refresh(proxy)
    return proxy


@router.delete("/{proxy_id}")
async def delete_proxy(proxy_id: int, db: AsyncSession = Depends(get_db)):
    proxy = await db.get(Proxy, proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    await db.delete(proxy)
    await db.commit()
    return {"status": "deleted"}


@router.post("/{proxy_id}/test")
async def test_proxy(proxy_id: int, db: AsyncSession = Depends(get_db)):
    proxy = await db.get(Proxy, proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")

    import httpx
    proxy_url = f"{proxy.protocol}://{proxy.url}"
    if proxy.username and proxy.password:
        proxy_url = f"{proxy.protocol}://{proxy.username}:{proxy.password}@{proxy.url}"
    try:
        async with httpx.AsyncClient(timeout=15.0, proxies=proxy_url) as client:
            resp = await client.get(
                "https://httpbin.org/ip",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code == 200:
                # Update success on test pass
                proxy.status = "active"
                proxy.fail_count = 0
                proxy.last_used = func.now()
                await db.commit()
                return {"status": "ok", "ip": resp.json().get("origin", "unknown")}
            else:
                return {"status": "fail", "detail": f"Status {resp.status_code}"}
    except Exception as e:
        proxy.fail_count = proxy.fail_count + 1
        await db.commit()
        return {"status": "fail", "detail": str(e)}