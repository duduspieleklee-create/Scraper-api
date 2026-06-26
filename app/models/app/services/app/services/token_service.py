from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from app.models.user import User  # Falls du ein User-Modell hast
from app.models.token_transaction import TokenTransaction
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def get_user_balance(db: AsyncSession, user_id: str) -> int:
    result = await db.execute(
        select(User.balance).where(User.id == user_id)
    )
    balance = result.scalar_one_or_none()
    return balance or 0


async def deduct_tokens_with_rollback(
    db: AsyncSession,
    user_id: str,
    amount: int,
    search_id: str,
    reason: str = "scrape_trigger"
) -> dict:
    """Token abbuchen mit Transaktion"""
    if amount <= 0:
        return {"success": True, "transaction_id": None}

    current_balance = await get_user_balance(db, user_id)

    if current_balance < amount:
        logger.warning(f"User {user_id} hat nicht genug Tokens ({current_balance} < {amount})")
        return {"success": False, "reason": "insufficient_funds"}

    # Abbuchung
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(balance=User.balance - amount)
    )

    transaction = TokenTransaction(
        user_id=user_id,
        search_id=search_id,
        amount=-amount,
        reason=reason,
        created_at=datetime.utcnow()
    )
    db.add(transaction)
    await db.flush()

    await db.commit()

    logger.info(f"{amount} Tokens von User {user_id} abgebucht (Suche {search_id})")
    return {"success": True, "transaction_id": transaction.id}


async def refund_tokens(
    db: AsyncSession,
    user_id: str,
    amount: int,
    search_id: str,
    reason: str = "scrape_error"
):
    """Rückerstattung bei Fehlern"""
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(balance=User.balance + amount)
    )

    transaction = TokenTransaction(
        user_id=user_id,
        search_id=search_id,
        amount=+amount,
        reason=f"refund_{reason}",
        created_at=datetime.utcnow()
    )
    db.add(transaction)

    await db.commit()
    logger.info(f"{amount} Tokens an User {user_id} zurückerstattet (Grund: {reason})")
