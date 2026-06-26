from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.core.database import get_db
from app.models.proxy import Proxy

router = APIRouter(prefix="/dashboard/proxy", tags=["dashboard-proxy"])

@router.post("/add")
async def dashboard_add_proxy(
    request: Request,
    url: str = Form(...),
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    protocol: str = Form("http"),
    country: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.scalar(select(Proxy).where(Proxy.url == url).limit(1))
    if existing:
        return RedirectResponse(url="/dashboard?error=Proxy+URL+already+exists", status_code=303)
    proxy = Proxy(url=url, username=username, password=password, protocol=protocol, country=country)
    db.add(proxy)
    await db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

@router.post("/{proxy_id}/toggle")
async def dashboard_toggle_proxy(proxy_id: int, db: AsyncSession = Depends(get_db)):
    proxy = await db.get(Proxy, proxy_id)
    if proxy:
        proxy.status = "disabled" if proxy.status == "active" else "active"
        await db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

@router.post("/{proxy_id}/delete")
async def dashboard_delete_proxy(proxy_id: int, db: AsyncSession = Depends(get_db)):
    proxy = await db.get(Proxy, proxy_id)
    if proxy:
        await db.delete(proxy)
        await db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)