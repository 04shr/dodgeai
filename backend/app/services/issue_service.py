"""
Issue Service
=============
Filters and enriches flagged orders.
Adds human-readable issue descriptions and severity context.
"""
import logging
from typing import Optional
import app.services.data_service as _ds
from app.services.cache_service import cache

log = logging.getLogger("o2c.issues")

FLAG_COLS = {
    "delayed":   ("is_delivery_delayed",  "Delivery delayed beyond threshold"),
    "cancelled": ("is_billing_cancelled", "Billing document cancelled"),
    "unpaid":    ("is_unpaid",            "Invoice raised but no payment received"),
    "missing":   ("missing_stage",        "Incomplete lifecycle — missing stage"),
}


async def get_issues(
    issue_type:   Optional[str] = None,
    min_severity: Optional[int] = None,
    customer:     Optional[str] = None,
    stage:        Optional[str] = None,
    limit:        int = 200,
    offset:       int = 0,
) -> dict:
    cache_key = f"issues:{issue_type}:{min_severity}:{customer}:{stage}"
    if (cached := cache.get(cache_key)):
        return cached

    _ds._ensure_loaded()
    df = _ds._orders_df.copy()

    # Filters
    if customer:     df = df[df["customer_id"].astype(str) == str(customer)]
    if stage:        df = df[df["lifecycle_stage"] == stage]
    if min_severity: df = df[df["max_issue_severity"].fillna(0) >= min_severity]

    if issue_type and issue_type in FLAG_COLS:
        col, _ = FLAG_COLS[issue_type]
        df = df[df[col] == True]  # noqa: E712
    else:
        # Default: any issue
        any_issue = (
            df["is_delivery_delayed"].fillna(False) |
            df["is_billing_cancelled"].fillna(False) |
            df["is_unpaid"].fillna(False) |
            df["missing_stage"].fillna(False)
        )
        df = df[any_issue]

    df = df.sort_values("max_issue_severity", ascending=False, na_position="last")

    total = len(df)
    page  = df.iloc[offset : offset + limit]
    rows  = _ds._clean(page)

    # Annotate each row with a list of active issue labels
    for row in rows:
        row["issue_labels"] = [
            desc for key, (col, desc) in FLAG_COLS.items()
            if row.get(col) is True
        ]

    result = {
        "total": total, "offset": offset, "limit": limit,
        "issue_type_filter": issue_type,
        "data": rows,
    }
    cache.set(cache_key, result)
    return result


async def get_issue_summary() -> dict:
    """Quick counts per issue type — used by dashboard."""
    _ds._ensure_loaded()
    df = _ds._orders_df
    return {
        "total_flagged": int(
            (df["is_delivery_delayed"].fillna(False) |
             df["is_billing_cancelled"].fillna(False) |
             df["is_unpaid"].fillna(False) |
             df["missing_stage"].fillna(False)).sum()
        ),
        "by_type": {
            key: int(df[col].fillna(False).sum())
            for key, (col, _) in FLAG_COLS.items()
        },
        "by_severity": df["max_issue_severity"].fillna(0).astype(int).value_counts().sort_index().to_dict(),
    }
