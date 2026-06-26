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
from app.utils.url_generator import generate_search_url
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


async def trigger_single_search(search_id: int, user_id: str):
    async with AsyncSessionLocal() as db:
        search = await db.get(Search, search_id)
        if not search or not search.enabled:
            return

        cost = getattr(search, "estimated_cost_per_run", 1)

        deduct_result = await deduct_tokens_with_rollback(
            db=db,
            user_id=user_id,
            amount=cost,
            search_id=str(search_id)
        )

        if not deduct_result["success"]:
            search.enabled = False
            search.last_run = func.now()
            await db.commit()
            logger.warning(f"Suche {search_id} pausiert – nicht genug Tokens")
            return

        try:
            search_url = generate_search_url(
                keyword=search.keyword,
                location=search.location,
                price_min=search.price_min,
                price_max=search.price_max,
                category=search.category,
                sort=search.sort or "date"
            )

            all_ads = await get_filtered_search_result(
                search_config=search,
                filter_config=getattr(search, "filter_config", None),
                store=None,
                config=None
            )

            # Nur neue Anzeigen durchlassen
            new_ads = await filter_new_ads(db, search_id, all_ads)

            if new_ads:
                # Als gesehen markieren
                await mark_ads_as_seen(db, search_id, new_ads)

                if search.callback_url:
                    await send_webhook(search.callback_url, {
                        "search_id": search.id,
                        "name": search.name,
                        "new_ads_count": len(new_ads),
                        "ads": new_ads[:10]
                    })

            logger.info(f"Suche {search_id} fertig – {len(new_ads)} neue Anzeigen")

        except Exception as e:
            logger.error(f"Fehler bei Suche {search_id}: {e}")
            await refund_tokens(db, user_id, cost, str(search_id), reason="scrape_error")
        finally:
            search.last_run = func.now()
            await db.commit()
