from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.models.search_execution_log import SearchExecutionLog
import logging
logger = logging.getLogger(__name__)

max_executions_per_minute = 5

async def check_rate_limit(db: AsyncSession, user_id: str) -> bool:
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
    result = await db.execute(
        select(func.count(SearchExecutionLog.id))
        .where(
            SearchExecutionLog.user_id == user_id,
            SearchExecutionLog.executed_at >= one_minute_ago,
        )
    )
    count = result.scalar_one_or_none() or 0
    return count < max_executions_per_minute

async def log_execution(db, user_id, search_id):
    log = SearchExecutionLog(
        user_id=user_id,
        search_id=search_id,
        executed_at=datetime.utcnow()
    )
    db.add(log)
    await db.flush()