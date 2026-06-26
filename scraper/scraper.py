import logging
import asyncio
import random
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from app.utils.url_generator import generate_search_url

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": "https://www.kleinanzeigen.de/",
}


def parse_ads(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    ads = []

    for item in soup.select("article.aditem"):
        try:
            title_tag = item.select_one(".ellipsis")
            price_tag = item.select_one(".aditem-main--middle--price-shipping--price")
            link_tag = item.select_one("a.ellipsis") or item.select_one(".aditem-main--middle a")
            location_tag = item.select_one(".aditem-main--top--left")
            date_tag = item.select_one(".aditem-main--top--right")
            img_tag = item.select_one("img.imagebox-thumbnail")
            desc_tag = item.select_one(".aditem-main--middle--description")
            ad_id = item.get("data-adid", "")

            title = title_tag.get_text(strip=True) if title_tag else None
            if not title:
                continue

            raw_link = link_tag.get("href", "") if link_tag else ""
            full_link = f"https://www.kleinanzeigen.de{raw_link}" if raw_link.startswith("/") else raw_link

            price_raw = price_tag.get_text(strip=True) if price_tag else ""
            price_num = None
            if price_raw:
                digits = "".join(c for c in price_raw if c.isdigit())
                price_num = int(digits) if digits else None

            ads.append({
                "ad_id": ad_id,
                "title": title,
                "price_raw": price_raw,
                "price": price_num,
                "link": full_link,
                "location": location_tag.get_text(strip=True) if location_tag else None,
                "date": date_tag.get_text(strip=True) if date_tag else None,
                "description": desc_tag.get_text(strip=True) if desc_tag else None,
                "image_url": img_tag.get("src", "") if img_tag else None,
            })
        except Exception as e:
            logger.debug(f"Parse-Fehler bei Anzeige: {e}")
            continue

    return ads


async def scrape_page(url: str, client: httpx.AsyncClient, delay_range=(1.5, 4.0)) -> List[Dict[str, Any]]:
    delay = random.uniform(*delay_range)
    await asyncio.sleep(delay)

    try:
        resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=30.0)
        resp.raise_for_status()
        return parse_ads(resp.text)
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP {e.response.status_code} für {url}")
        return []
    except Exception as e:
        logger.error(f"Scrape-Fehler: {e}")
        return []


async def get_filtered_search_result(
    search_config,
    filter_config=None,
    store=None,
    config=None,
    proxy_info=None,
) -> List[Dict[str, Any]]:
    keyword = search_config.keyword if hasattr(search_config, "keyword") else str(search_config)
    location = getattr(search_config, "location", None)
    price_min = getattr(search_config, "price_min", None)
    price_max = getattr(search_config, "price_max", None)
    category = getattr(search_config, "category", None)
    sort = getattr(search_config, "sort", "date") or "date"

    url = generate_search_url(
        keyword=keyword,
        location=location,
        price_min=price_min,
        price_max=price_max,
        category=category,
        sort=sort
    )

    logger.info(f"Scrape gestartet: {url}")

    # Build client with proxy if available
    client_kwargs = {}
    if proxy_info:
        from scraper.proxy_manager import build_proxy_url
        proxy_url = build_proxy_url(proxy_info)
        client_kwargs["proxies"] = proxy_url
        logger.info(f"Using proxy: {proxy_info['url']} {{proxy_info.get('country', '')}}")

    async with httpx.AsyncClient(**client_kwargs) as client:
        ads = await scrape_page(url, client)

    # Preisfilter (falls config vorhanden)
    if filter_config:
        min_p = getattr(filter_config, "price_min", None)
        max_p = getattr(filter_config, "price_max", None)
        if min_p is not None:
            ads = [a for a in ads if a["price"] is not None and a["price"] >= min_p]
        if max_p is not None:
            ads = [a for a in ads if a["price"] is not None and a["price"] <= max_p]

    logger.info(f"Scrape fertig: {len(ads)} Anzeigen gefunden")
    return ads
