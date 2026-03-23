"""Response formatting helpers."""
from typing import Any


def paginate(items: list, offset: int, limit: int) -> dict:
    return {
        "total":  len(items),
        "offset": offset,
        "limit":  limit,
        "data":   items[offset : offset + limit],
    }


def currency_inr(value: Any) -> str:
    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return "—"


def pct(value: Any, decimals: int = 1) -> str:
    try:
        return f"{float(value):.{decimals}f}%"
    except (TypeError, ValueError):
        return "—"
