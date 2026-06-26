import aiohttp
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def send_webhook(callback_url: str, payload: Dict[str, Any]):
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(callback_url, json=payload) as resp:
                if 200 <= resp.status < 300:
                    logger.info(f"Webhook erfolgreich: {callback_url}")
                    return True
                else:
                    logger.error(f"Webhook Fehler {resp.status}: {await resp.text()}")
                    return False
    except Exception as e:
        logger.error(f"Webhook Exception: {e}")
        return False
