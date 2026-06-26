from pydantic import BaseModel
from typing import List, Optional

class SearchConfig(BaseModel):
    name: str
    url: str
    recursive: bool = True

class FilterConfig(BaseModel):
    exclude_topads: bool = True
    exclude_patterns: List[str] = []

class Config(BaseModel):
    searches: List[SearchConfig] = []
    filter: FilterConfig = FilterConfig()
