import aiohttp
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def send_webhook(callback_url: str, payload: Dict[str, Any]):
    """
    Ergebnisse per Webhook an die Android-App oder einen anderen Service senden.
    """
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(callback_url, json=payload) as response:
                if response.status >= 200 and response.status < 300:
                    logger.info(f"Webhook erfolgreich an {callback_url} gesendet")
                    return True
                else:
                    text = await response.text()
                    logger.error(f"Webhook-Fehler {response.status}: {text}")
                    return False
    except Exception as e:
        logger.error(f"Webhook-Fehler bei {callback_url}: {e}")
        return False
