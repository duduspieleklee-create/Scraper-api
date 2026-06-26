import json
from pathlib import Path
from typing import List, Dict, Any

class AdItem:
    def __init__(self, ad_id: str, title: str, price: int, link: str, **kwargs):
        self.id = ad_id
        self.title = title
        self.price = price
        self.link = link
        self.data = kwargs

class DataStore:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.seen_ads = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.seen_ads, f, ensure_ascii=False, indent=2)

    def is_new(self, ad_id: str) -> bool:
        return ad_id not in self.seen_ads

    def mark_seen(self, ad_id: str, ad_data: Dict):
        self.seen_ads[ad_id] = ad_data
        self._save()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._save()
