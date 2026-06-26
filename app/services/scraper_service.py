import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.database import AsyncSessionLocal
from app.models.search import Search
from app.models.seen_ad import SeenAd
from app.services.token_service import deduct_tokens_with_rollback, refund_tokens
from app.services.webhook_service import send_webhook
from app.services.rate_limit_service import check_rate_limit, log_execution
from app.utils.url_generator import generate_search_url
from app.config import settings
from scraper.scraper import get_filtered_search_result

logger = logging.getLogger(__name__)


async def filter_new_ads(db: AsyncSession, search_id: int, ads: list) -> list:
    """Gibt nur Anzeigen zurueck, die noch nicht gesehen wurden."""
    if not ads:
        return []

    ad_ids = [a["ad_id"] for a in ads if a.get("ad_id")]
    if not ad_ids:
        return ads  # Kein ad_id -> kein Dedup moeglich

    result = await db.execute(
        select(SeenAd.ad_id).where(
            SeenAd.search_id == search_id,
            SeenAd.ad_id.in_(ad_ids)
        )
    )
    already_seen = {row[0] for row in result.fetchall()}

    new_ads = [a for a in ads if a.get("ad_id") not in already_seen]
    logger.info(f"Dedup: {len(ads)} gefunden, {len(new_ads)} neu, {len(already_seen)} bereits gesehen")
    return new_ads


async def mark_ads_as_seen(db: AsyncSession, search_id: int, ads: list):
    """Speichert neue Anzeigen in seen_ads."""
    for ad in ads:
        if not ad.get("ad_id"):
            continue
        stmt = pg_insert(SeenAd).values(
            search_id=search_id,
            ad_id=ad["ad_id"],
            title=ad.get("title"),
            price=ad.get("price"),
            link=ad.get("link"),
        ).on_conflict_do_nothing(constraint="uq_seen_ad")
        await db.execute(stmt)
    await db.commit()
