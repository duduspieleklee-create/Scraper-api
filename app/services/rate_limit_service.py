from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.models.search_execution_log import SearchExecutionLog

import logging
logger = logging.getLogger(__name__)

max_executions_per_minute = 5   # From app.config or hardcoded below will override in settings

async def check_rate_limit(
    db: AsyncSession,
    user_id: str,
) -> bool:
    """
    Check if the user has exceeded the execution limit in the last minute.
    Returns True if under the limit, False if rate-limited.
    """
    # Check how many executions in the last minute
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
    """Log an execution for rate limiting purposes."""
    stmt = SearchExecutionLog(user_id=user_id, search_id=search_id)
    db.add(stmt)
    await db.commit()