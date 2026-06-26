# ─────────────────────────────────────────────────────────────────────────────
# UPDATED worker.py — replace your existing worker.py with this
# Adds a heartbeat write to the DB every 60s so the dashboard
# can show worker Online/Offline status.
# ─────────────────────────────────────────────────────────────────────────────

import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.database import AsyncSessionLocal
from app.services.scraper_service import trigger_single_search
from app.models.search import Search
from app.models.worker_heartbeat import WorkerHeartbeat
from sqlalchemy import select, update

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

scheduler = AsyncIOScheduler()


async def write_heartbeat(jobs_count: int = 0):
    """Write / update a heartbeat row so the dashboard can see the worker is alive."""
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(
            select(WorkerHeartbeat).where(WorkerHeartbeat.worker_name == "main")
        )
        if existing:
            await db.execute(
                update(WorkerHeartbeat)
                .where(WorkerHeartbeat.worker_name == "main")
                .values(last_seen=datetime.utcnow(), jobs_scheduled=jobs_count)
            )
        else:
            db.add(WorkerHeartbeat(worker_name="main", last_seen=datetime.utcnow(), jobs_scheduled=jobs_count))
        await db.commit()
    logger.debug("Heartbeat geschrieben")


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
                replace_existing=True,
            )
            logger.info(f"Job geplant: {job_id} alle {search.interval_minutes} Min")

    logger.info(f"{len(searches)} Suchen geladen und geplant")
    await write_heartbeat(jobs_count=len(searches))


async def heartbeat_tick():
    """Called every 60s to keep the heartbeat fresh."""
    job_count = len(scheduler.get_jobs())
    await write_heartbeat(jobs_count=job_count)


async def main():
    await load_and_schedule()

    # Stündlich neu laden
    scheduler.add_job(load_and_schedule, "interval", hours=1, id="reload_searches", replace_existing=True)

    # Heartbeat every 60s
    scheduler.add_job(heartbeat_tick, "interval", seconds=60, id="heartbeat", replace_existing=True)

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
