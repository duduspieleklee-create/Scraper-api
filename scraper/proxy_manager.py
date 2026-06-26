import logging
import random
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from app.models.proxy import Proxy

logger = logging.getLogger(__name__)

MAX_FAILS_BEFORE_BAN = 5
COOLDOWN_MINUTES = 30


async def get_random_proxy(db: AsyncSession) -> Optional[dict]:
    """Get a random active proxy, avoiding recently banned ones."""
    result = await db.execute(
        select(Proxy).where(
            Proxy.status == "active",
            Proxy.fail_count < MAX_FAILS_BEFORE_BAN,
        )
    )
    proxies = result.scalars().all()

    # Recover banned proxies if cooldown passed
    banned_result = await db.execute(
        select(Proxy).where(
            Proxy.status == "banned",
            Proxy.last_used < datetime.utcnow() - timedelta(minutes=COOLDOWN_MINUTES),
        )
    )
    for p in banned_result.scalars().all():
        p.status = "active"
        p.fail_count = 0
        proxies.append(p)
    if banned_result.scalars().all():
        await db.commit()

    if not proxies:
        logger.warning("No active proxies available")
        return None

    proxy = random.choice(proxies)
    return {
        "url": proxy.url,
        "username": proxy.username,
        "password": proxy.password,
        "protocol": proxy.protocol,
        "id": proxy.id,
    }


async def mark_proxy_success(db: AsyncSession, proxy_id: int):
    await db.execute(
        update(Proxy)
        .where(Proxy.id == proxy_id)
        .values(success_count=Proxy.success_count + 1, last_used=func.now())
    )
    await db.commit()


async def mark_proxy_fail(db: AsyncSession, proxy_id: int):
    # Check current fail count
    result = await db.execute(select(Proxy.fail_count).where(Proxy.id == proxy_id))
    current_fails = result.scalar_one_or_none() or 0
    new_fails = current_fails + 1

    if new_fails >= MAX_FAILS_BEFORE_BAN:
        await db.execute(
            update(Proxy)
            .where(Proxy.id == proxy_id)
            .values(fail_count=new_fails, last_used=func.now(), status="banned")
        )
        logger.warning(f"Proxy {proxy_id} banned after {new_fails} failures")
    else:
        await db.execute(
            update(Proxy)
            .where(Proxy.id == proxy_id)
            .values(fail_count=new_fails, last_used=func.now())
        )
    await db.commit()


def build_proxy_url(proxy_info: dict) -> str:
    """Build a full proxy URL with auth if provided."""
    proto = proxy_info.get("protocol", "http")
    url = proxy_info["url"]
    if proxy_info.get("username") and proxy_info.get("password"):
        return f"{proto}://{proxy_info['username']}:{proxy_info['password']}@{url}"
    return f"{proto}://{url}"