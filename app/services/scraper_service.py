import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.search import Search
from app.services.token_service import deduct_tokens_with_rollback, refund_tokens
from app.services.webhook_service import send_webhook
from app.utils.url_generator import generate_search_url
from scraper.scraper import get_filtered_search_result   # Dein Scraper aus dem Repo
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

async def trigger_single_search(search_id: int, user_id: str):
    """Vollständige Logik: Token prüfen → Scraper ausführen → Callback + Status-Update"""
    async with AsyncSessionLocal() as db:
        search = await db.get(Search, search_id)
        if not search or not search.enabled:
            return

        cost = getattr(search, 'estimated_cost_per_run', 1)

        # 1. Token abbuchen
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

        success = False
        try:
            # 2. Such-URL generieren
            search_url = generate_search_url(
                keyword=search.keyword,
                location=search.location,
                price_min=search.price_min,
                price_max=search.price_max,
                category=search.category,
                sort=search.sort or "date"
            )

            # 3. Scraper ausführen
            new_ads = await get_filtered_search_result(
                search_config=search,
                filter_config=getattr(search, 'filter_config', None),
                store=None,
                config=None
            )

            # 4. Bei neuen Anzeigen → Webhook senden
            if new_ads and search.callback_url:
                await send_webhook(search.callback_url, {
                    "search_id": search.id,
                    "name": search.name,
                    "new_ads_count": len(new_ads),
                    "timestamp": func.now().isoformat(),
                    "ads": new_ads[:10]  # Begrenzung
                })

            success = True
            logger.info(f"Suche {search_id} erfolgreich – {len(new_ads)} neue Anzeigen")

        except Exception as e:
            logger.error(f"Fehler bei Suche {search_id}: {e}")
            await refund_tokens(db, user_id, cost, str(search_id), reason="scrape_error")
        finally:
            # 5. Status aktualisieren
            search.last_run = func.now()
            await db.commit()
