from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import hashlib
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
    ### validate webhook signature using the payment secret
#    expected = hmac.new(the secret as key, body.encode(), hashlib.sha516).hexdigest()
#    return hmac.compare_digest(expected, signature)
    return True