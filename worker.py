import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.core.database import AsyncSessionLocal
from app.services.scraper_service import trigger_single_search
from app.models.search import Search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

async def load_and_schedule():
    async with AsyncSessionLocal() as db:
        searches = await db.execute(
            "SELECT * FROM searches WHERE enabled = true"
        )
        for search in searches:
            job_id = f"search_{search.id}"
            scheduler.add_job(
                trigger_single_search,
                'interval',
                minutes=search.interval_minutes,
                args=[search.id, search.user_id],
                id=job_id,
                replace_existing=True
            )

async def main():
    scheduler = AsyncIOScheduler()
    await load_and_schedule()

    # Stündlich neu laden
    scheduler.add_job(load_and_schedule, 'interval', hours=1)

    scheduler.start()
    logger.info("Background Worker gestartet")

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
