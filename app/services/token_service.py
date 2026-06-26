from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql import func
from datetime import datetime
from app.models.user import User
from app.models.token_transaction import TokenTransaction
import logging
logger = logging.getLogger(__name__)

async def deduct_tokens_with_rollback(db, user_id, amount, search_id=""):
    user_result = await db.execute(select(User).where(User.id == user_id).limit(1))
    user = user_result.scalar_one_or_none()
    if not user:
        return {"success": False, "error": "User not found"}
    if user.token_balance < amount:
        return {"success": False, "error": "Insufficient tokens"}
    await db.execute(update(User).where(User.id == user_id).values(
        token_balance=User.token_balance - amount, updated_at=func.now()))
    transaction = TokenTransaction(user_id=user_id, amount=-abs(int(amount)), reason=f'search:{search_id}')
    db.add(transaction)
    await db.commit()
    return {"success": True, "new_balance": user.token_balance - amount, "transaction_id": transaction.id}

async def refund_tokens(db, user_id, amount, reason=""):
    user_result = await db.execute(select(User).where(User.id == user_id).limit(1))
    user = user_result.scalar_one_or_none()
    if not user:
        return {"success": False, "error": "User not found"}
    await db.execute(update(User).where(User.id == user_id).values(
        token_balance=User.token_balance + abs(int(amount)), updated_at=func.now()))
    transaction = TokenTransaction(user_id=user_id, amount=abs(int(amount)), reason=reason or "refund")
    db.add(transaction)
    await db.commit()
    return {"success": True, "new_balance": user.token_balance + abs(int(amount)), "transaction_id": transaction.id}

async def add_tokens(webhook_token: str, db: AsyncSession, discount_code=None, discount_percent=None, amount=None):
    tokens = 20
    if amount:
        tokens = int(amount)
    if discount_code and discount_percent:
        tokens = int(tokens * (1 + discount_percent / 100))
    return tokens