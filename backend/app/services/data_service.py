"""
Data Service
============
Loads all processed CSVs and JSONs into memory once at startup.
All query methods operate on in-memory DataFrames — no per-request I/O.

Design notes:
  - _orders_df : one row per sales order (aggregated)
  - _items_df  : one row per order item  (full grain)
  - _customers : list[dict] from customer_kpis.json
  - _kpis      : dict from kpi_summary.json
"""
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

from app.config import DATA_DIR

log = logging.getLogger("o2c.data")

# ── Module-level singletons ────────────────────────────────
_orders_df:   Optional[pd.DataFrame] = None
_items_df:    Optional[pd.DataFrame] = None
_customers:   Optional[list]         = None
_kpis:        Optional[dict]         = None


class DataService:
    """Static wrapper so routers can call DataService.load() cleanly."""

    @staticmethod
    def load() -> None:
        global _orders_df, _items_df, _customers, _kpis
        log.info(f"Loading data from: {DATA_DIR}")
        _orders_df = _read_csv("unified_o2c_orders.csv")
        _items_df  = _read_csv("unified_o2c.csv")
        _customers = _read_json("customer_kpis.json")
        _kpis      = _read_json("kpi_summary.json")
        log.info(f"Loaded: {len(_orders_df)} orders | {len(_items_df)} items | {len(_customers)} customers")

    @staticmethod
    def is_loaded() -> bool:
        return _orders_df is not None

    @staticmethod
    def order_count() -> int:
        return len(_orders_df) if _orders_df is not None else 0


# ── Internal readers ───────────────────────────────────────
def _read_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    df = pd.read_csv(path, low_memory=False)
    # Normalise bool columns that CSV stores as string "True"/"False"
    bool_cols = [c for c in df.columns if c.startswith("is_") or c == "missing_stage"]
    for col in bool_cols:
        if df[col].dtype == object:
            df[col] = df[col].map({"True": True, "False": False, True: True, False: False}).fillna(False)
    return df


def _read_json(name: str) -> dict | list:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    with open(path) as f:
        return json.load(f)


def _ensure_loaded():
    if _orders_df is None:
        DataService.load()


def _clean(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to JSON-safe list of dicts."""
    return df.replace({np.nan: None, float("inf"): None, float("-inf"): None}).to_dict(orient="records")


# ── Orders ─────────────────────────────────────────────────
async def get_orders(
    customer: str = None,
    stage:    str = None,
    issue_type: str = None,
    min_severity: int = None,
    sort_by:  str = "order_created_date",
    sort_dir: str = "desc",
    limit:    int = 100,
    offset:   int = 0,
) -> dict:
    _ensure_loaded()
    df = _orders_df.copy()

    if customer:     df = df[df["customer_id"].astype(str) == str(customer)]
    if stage:        df = df[df["lifecycle_stage"] == stage]
    if min_severity: df = df[df["max_issue_severity"].fillna(0) >= min_severity]
    if issue_type:
        flag_map = {
            "delayed":   "is_delivery_delayed",
            "cancelled": "is_billing_cancelled",
            "unpaid":    "is_unpaid",
            "missing":   "missing_stage",
        }
        col = flag_map.get(issue_type)
        if col and col in df.columns:
            df = df[df[col] == True]  # noqa: E712

    # Sort
    if sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=(sort_dir == "asc"), na_position="last")

    total = len(df)
    page  = df.iloc[offset : offset + limit]
    return {"total": total, "offset": offset, "limit": limit, "data": _clean(page)}


async def get_order_by_id(order_id: str) -> dict:
    _ensure_loaded()
    row = _orders_df[_orders_df["sales_order_id"].astype(str) == str(order_id)]
    if row.empty:
        return None
    return _clean(row)[0]


async def get_order_items(order_id: str) -> list[dict]:
    """Full item-level rows for a single order — used by AI root cause."""
    _ensure_loaded()
    items = _items_df[_items_df["sales_order_id"].astype(str) == str(order_id)]
    return _clean(items)


async def get_order_context(order_id: str) -> dict:
    """Combined order header + items dict for AI prompts."""
    header = await get_order_by_id(order_id)
    items  = await get_order_items(order_id)
    return {"order": header, "items": items}


# ── Customers ───────────────────────────────────────────────
async def get_customers() -> list[dict]:
    _ensure_loaded()
    return _customers


async def get_customer_by_id(customer_id: str) -> dict | None:
    _ensure_loaded()
    matches = [c for c in _customers if str(c["customer_id"]) == str(customer_id)]
    return matches[0] if matches else None


async def get_customer_orders(customer_id: str) -> list[dict]:
    _ensure_loaded()
    df = _orders_df[_orders_df["customer_id"].astype(str) == str(customer_id)]
    return _clean(df)


# ── Analytics snapshots ─────────────────────────────────────
async def get_stage_breakdown() -> dict:
    _ensure_loaded()
    return _orders_df["lifecycle_stage"].value_counts().to_dict()


async def get_issue_counts() -> dict:
    _ensure_loaded()
    df = _orders_df
    return {
        "delayed":   int(df["is_delivery_delayed"].sum()),
        "cancelled": int(df["is_billing_cancelled"].sum()),
        "unpaid":    int(df["is_unpaid"].sum()),
        "missing":   int(df["missing_stage"].sum()),
    }
