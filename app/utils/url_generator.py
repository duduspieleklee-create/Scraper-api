from typing import Optional

def generate_search_url(
    keyword: str,
    location: Optional[str] = None,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
    category: Optional[str] = None,
    sort: str = "date"
) -> str:
    base = "https://www.kleinanzeigen.de/s-"
    
    if location:
        path = f"{location}/{keyword}/k0"
    else:
        path = f"{keyword}/k0"
    
    if category:
        path = f"{category}/{path}"
    
    url = base + path
    
    params = {}
    if price_min is not None or price_max is not None:
        min_p = price_min or ""
        max_p = price_max or ""
        params["price"] = f"{min_p}:{max_p}"
    
    sort_map = {
        "date": "DATE",
        "price_asc": "PRICE_ASC",
        "price_desc": "PRICE_DESC",
        "distance": "DISTANCE",
    }
    if sort in sort_map:
        params["sort"] = sort_map[sort]
    
    if params:
        import urllib.parse
        url += "?" + urllib.parse.urlencode(params)
    
    return url
