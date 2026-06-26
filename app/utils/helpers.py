from datetime import datetime

def now_iso():
    """Aktuelles Datum im ISO-Format"""
    return datetime.utcnow().isoformat()

def calculate_estimated_cost(interval_minutes: int) -> int:
    """Beispiel: Kosten je nach Intervall schätzen"""
    if interval_minutes <= 15:
        return 2
    elif interval_minutes <= 60:
        return 1
    return 1
