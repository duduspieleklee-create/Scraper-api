import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.search import Search
from app.services.token_service import deduct_tokens_with_rollback, refund_tokens
from app.utils.url_generator import generate_search_url
from scraper.scraper import get_filtered_search_result   # Dein Scraper

logger = logging.getLogger(__name__)

async def trigger_single_search(search_id: int, user_id: str):
    async with AsyncSessionLocal() as db:
        search = await db.get(Search, search_id)
        if not search or not search.enabled:
            return

        cost = search.estimated_cost_per_run or 1

        # Token abbuchen
        deduct_result = await deduct_tokens_with_rollback(db, user_id, cost, str(search_id))
        if not deduct_result["success"]:
            search.enabled = False
            await db.commit()
            return

        success = False
        try:
            search_url = generate_search_url(
                keyword=search.keyword,
                location=search.location,
                price_min=search.price_min,
                price_max=search.price_max,
                category=search.category,
                sort=search.sort
            )

            new_ads = await get_filtered_search_result(search, db)

            if new_ads and search.callback_url:
                await send_webhook(search.callback_url, {
                    "search_id": search.id,
                    "new_ads_count": len(new_ads),
                    "ads": new_ads[:5]  # Begrenzt
                })

            success = True
            logger.info(f"Suche {search_id} erfolgreich: {len(new_ads)} neue Anzeigen")

        except Exception as e:
            logger.error(f"Fehler bei Suche {search_id}: {e}")
            await refund_tokens(db, user_id, cost, str(search_id), "scrape_error")
        finally:
            search.last_run = func.now()
            await db.commit()
