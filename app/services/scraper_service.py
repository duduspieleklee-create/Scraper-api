import logging
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.core.database import AsyncSessionLocal
from app.models.search import Search
from app.services.token_service import deduct_tokens_with_rollback, refund_tokens
from app.services.webhook_service import send_webhook
from app.utils.url_generator import generate_search_url
from scraper.scraper import get_filtered_search_result

logger = logging.getLogger(__name__)

# ... Rest der Funktion wie zuvor ...
