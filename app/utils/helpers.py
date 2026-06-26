# app/utils/helpers.py
"""
Hilfsfunktionen für die Scraper API
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import DeclarativeBase


def model_to_dict(obj: Any) -> Optional[Dict]:
    """Konvertiert ein SQLAlchemy-Modell in ein einfaches Dictionary."""
    if obj is None:
        return None
    
    if isinstance(obj, list):
        return [model_to_dict(item) for item in obj]
    
    # SQLAlchemy Model
    if hasattr(obj, "__table__"):
        return {
            column.name: getattr(obj, column.name)
            for column in obj.__table__.columns
        }
    
    # Für Tuples wie (Model, count)
    if isinstance(obj, tuple) and len(obj) == 2:
        model, count = obj
        data = model_to_dict(model)
        if data is not None:
            data["ad_count"] = int(count or 0)
        return data
    
    # Fallback für andere Objekte
    try:
        return dict(obj)
    except (TypeError, ValueError):
        return {"value": str(obj)}


def models_to_list(models: List[Any]) -> List[Dict]:
    """Konvertiert eine Liste von SQLAlchemy-Modellen in eine Liste von Dicts."""
    return [model_to_dict(model) for model in models if model is not None]


def safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    """Sicheres Abrufen von Attributen (verhindert Errors bei None)."""
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default
