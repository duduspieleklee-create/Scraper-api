from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.scraper_service import trigger_single_search
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

async def schedule_search(search):
    """Eine einzelne Suche planen"""
    job_id = f"search_{search.id}"
    
    scheduler.add_job(
        trigger_single_search,
        trigger='interval',
        minutes=search.interval_minutes,
        args=[search.id, search.user_id],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=120,
        max_instances=1
    )
    logger.info(f"Suche {search.id} eingeplant (alle {search.interval_minutes} Minuten)")

async def reload_all_schedules(db: AsyncSession):
    """Alle aktiven Suchen neu laden"""
    result = await db.execute("SELECT * FROM searches WHERE enabled = true")
    searches = result.fetchall()
    
    for search in searches:
        await schedule_search(search)

    logger.info(f"{len(searches)} Suchen geladen und geplant")
