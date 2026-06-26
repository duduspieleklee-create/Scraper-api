import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.database import AsyncSessionLocal
from app.services.scraper_service import trigger_single_search
from app.models.search import Search
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

scheduler = AsyncIOScheduler()


async def load_and_schedule():
    """Lädt aktive Suchen aus der DB und plant sie im Scheduler ein."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Search).where(Search.enabled == True)
        )
        searches = result.scalars().all()

        for search in searches:
            job_id = f"search_{search.id}"
            scheduler.add_job(
                trigger_single_search,
                "interval",
                minutes=search.interval_minutes,
                args=[search.id, search.user_id],
                id=job_id,
                replace_existing=True
            )
            logger.info(f"Job geplant: {job_id} alle {search.interval_minutes} Min")

    logger.info(f"{len(searches)} Suchen geladen und geplant")


async def main():
    await load_and_schedule()

    # Stündlich neu laden (neue Suchen aufnehmen)
    scheduler.add_job(load_and_schedule, "interval", hours=1, id="reload_searches", replace_existing=True)

    scheduler.start()
    logger.info("Background Worker gestartet")

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Worker beendet")


if __name__ == "__main__":
    asyncio.run(main())
