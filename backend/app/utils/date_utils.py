"""Date utilities for the O2C backend."""
from datetime import datetime, timezone
from typing import Optional


def parse_date(s) -> Optional[datetime]:
    if not s or str(s) in ("nan", "None", ""):
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def days_diff(a, b) -> Optional[int]:
    da, db = parse_date(a), parse_date(b)
    if not da or not db:
        return None
    return (db - da).days


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
