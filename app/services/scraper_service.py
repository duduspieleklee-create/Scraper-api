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
from app.services.deal_scorer import (
    calculate_deal_score,
    get_urgency_label,
    get_freshness_label,
    get_competition_count,
)
from app.utils.url_generator import generate_search_url
from app.config import settings
from scraper.scraper import get_filtered_search_result

logger = logging.getLogger(__name__)


async def filter_new_ads(db: AsyncSession, search_id: int, ads: list) -> list:
    if not ads:
        return []
    ad_ids = [a["ad_id"] for a in ads if a.get("ad_id")]
    if not ad_ids:
        return ads
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


async def get_price_for_search(search: Search) -> int:
    pricing = settings.INTERVAL_PRICING
    interval = search.interval_minutes
    if interval in pricing:
        return pricing[interval]
    return settings.TOKEN_COST_PER_RUN


async def trigger_single_search(search_id: int, user_id: str):
    async with AsyncSessionLocal() as db:
        search = await db.get(Search, search_id)
        if not search or not search.enabled:
            return
        is_first_run = search.last_run is None
        cost = await get_price_for_search(search)
        try:
            proxy_info = None
            try:
                from scraper.proxy_manager import get_random_proxy, mark_proxy_success, mark_proxy_fail
                proxy_info = await get_random_proxy(db)
            except Exception:
                pass
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
                config=None,
                proxy_info=proxy_info,
            )
            if proxy_info:
                try:
                    await mark_proxy_success(db, proxy_info["id"])
                except Exception:
                    pass
            if is_first_run:
                new_ads = all_ads[:10]
            else:
                new_ads = await filter_new_ads(db, search_id, all_ads)
            if new_ads:
                if not await check_rate_limit(db, user_id):
                    logger.warning(f"Suche {search_id} skipped fuer User {user_id} - Rate Limit")
                    search.last_run = func.now()
                    await db.commit()
                    return
                deduct_result = await deduct_tokens_with_rollback(
                    db=db, user_id=user_id, amount=cost, search_id=str(search_id)
                )
                if not deduct_result["success"]:
                    search.enabled = False
                    search.last_run = func.now()
                    await db.commit()
                    logger.warning(f"Suche {search_id} pausiert - nicht genug Tokens")
                    return
                await log_execution(db, user_id, search_id)
                await mark_ads_as_seen(db, search_id, new_ads)

                # ── INTELLIGENCE-LAYER: Deal-Score + Anreicherung ──
                enriched_ads = []
                for ad in new_ads[:10]:
                    score = await calculate_deal_score(
                        db, ad,
                        keyword=search.keyword,
                        location=search.location,
                    )
                    competition = await get_competition_count(db, search.keyword)
                    enriched_ads.append({
                        **ad,
                        "deal_score": score,
                        "urgency": get_urgency_label(score),
                        "freshness": get_freshness_label(ad.get("first_seen")),
                        "competition": competition,
                    })

                # Sortiere nach Deal-Score (höchster zuerst)
                enriched_ads.sort(key=lambda x: x["deal_score"], reverse=True)

                if search.callback_url:
                    await send_webhook(search.callback_url, {
                        "search_id": search.id,
                        "name": search.name,
                        "keyword": search.keyword,
                        "new_ads_count": len(new_ads),
                        "ads": enriched_ads,
                        "top_deal": enriched_ads[0] if enriched_ads else None,
                    })
                logger.info(
                    f"Suche {search_id} fertig - {len(new_ads)} neue Anzeigen "
                    f"({cost} Tokens) | Top-Score: {enriched_ads[0]['deal_score'] if enriched_ads else '—'}"
                )
            else:
                logger.info(f"Suche {search_id}: 0 neue Anzeigen - keine Token faellig")
        except Exception as e:
            if proxy_info:
                try:
                    await mark_proxy_fail(db, proxy_info["id"])
                except Exception:
                    pass
            logger.error(f"Fehler bei Suche {search_id}: {e}")
        finally:
            search.last_run = func.now()
            await db.commit()
