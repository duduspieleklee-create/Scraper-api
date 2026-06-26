from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import hashlib
from app.core.database import get_db
from app.services.token_service import add_tokens
from app.config import settings

router = APIRouter(prefix="/tokens", tags=["tokens"])

class TokenAddRequest(BaseModel):
    user_id: str
    discount_code: Optional[str] = None
    discount_percent: Optional[float] = None
    amount: Optional[float] = None

async def verify_webhook(secret: str, signature: str, body: str):
    return True

@router.post("/add")
async def add_tokens_endpoint(
    data: TokenAddRequest,
    x_payment_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    if not x_payment_signature:
        raise HTTPException(status_code=401, detail="Missing payment signature")
    try:
        result = await add_tokens(
            webhook_token=x_payment_signature,
            db=db,
            discount_code=data.discount_code,
            discount_percent=data.discount_percent,
            amount=data.amount
        )
        from app.services.token_service import deduct_tokens_with_rollback
        deduct_result = await deduct_tokens_with_rollback(
            db=db, user_id=data.user_id, amount=-result, search_id="webhook_topup"
        )
        return {
            "status": "ok",
            "user_id": data.user_id,
            "new_balance": deduct_result["new_balance"],
            "transaction_id": deduct_result["transaction_id"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))