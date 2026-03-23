"""
KPI Service
===========
Returns KPI summaries from pre-computed JSON (fast path)
or recomputes live from DataFrame for filtered views.
"""
import logging
import pandas as pd
import numpy as np
from typing import Optional

import app.services.data_service as _ds   # import module, not name — stays live after load()
from app.services.cache_service import cache

log = logging.getLogger("o2c.kpis")


async def get_kpi_summary(customer: str = None, stage: str = None) -> dict:
    cache_key = f"kpi:{customer}:{stage}"
    if (cached := cache.get(cache_key)):
        return cached

    _ds._ensure_loaded()

    # Unfiltered → return pre-computed JSON (instant)
    if not customer and not stage:
        result = _ds._kpis
        cache.set(cache_key, result)
        return result

    # Filtered → recompute live
    result = _compute_dynamic_kpis(customer=customer, stage=stage)
    cache.set(cache_key, result)
    return result


async def get_customer_kpis() -> list[dict]:
    _ds._ensure_loaded()
    return _ds._customers


def _compute_dynamic_kpis(customer: str = None, stage: str = None) -> dict:
    """Live KPI computation for filtered views."""
    _ds._ensure_loaded()
    df = _ds._orders_df.copy()
    if customer: df = df[df["customer_id"].astype(str) == str(customer)]
    if stage:    df = df[df["lifecycle_stage"] == stage]

    def safe_mean(s):
        v = s.dropna()
        return round(float(v.mean()), 2) if len(v) else None

    def safe_median(s):
        v = s.dropna()
        return round(float(v.median()), 2) if len(v) else None

    total_rev  = round(float(df["order_total_net_amount"].sum()), 2)
    total_paid = round(float(df["total_paid_amount"].fillna(0).sum()), 2)

    return {
        "generated_at": pd.Timestamp.now("UTC").isoformat(),
        "filters":      {"customer": customer, "stage": stage},
        "overview": {
            "total_orders":          len(df),
            "total_order_items":     int(df["total_items"].sum()),
            "unique_customers":      df["customer_id"].nunique(),
            "total_revenue_inr":     total_rev,
            "total_paid_inr":        total_paid,
            "revenue_leakage_inr":   round(total_rev - total_paid, 2),
            "payment_coverage_pct":  round(total_paid / total_rev * 100, 1) if total_rev else 0,
        },
        "lifecycle_stages": df["lifecycle_stage"].value_counts().to_dict(),
        "cycle_times": {
            "avg_order_to_delivery_days":    safe_mean(df["order_to_delivery_days"]),
            "median_order_to_delivery_days": safe_median(df["order_to_delivery_days"]),
            "avg_delivery_to_billing_days":  safe_mean(df["delivery_to_billing_days"]),
            "avg_billing_to_payment_days":   safe_mean(df["billing_to_payment_days"]),
            "avg_total_o2c_days":            safe_mean(df["total_o2c_days"]),
            "median_total_o2c_days":         safe_median(df["total_o2c_days"]),
        },
        "issues": {
            "orders_with_delivery_delay": int(df["is_delivery_delayed"].sum()),
            "orders_billing_cancelled":   int(df["is_billing_cancelled"].sum()),
            "orders_unpaid":              int(df["is_unpaid"].sum()),
            "orders_missing_stage":       int(df["missing_stage"].sum()),
            "cancellation_rate_pct":      round(df["is_billing_cancelled"].mean() * 100, 1),
            "delivery_delay_rate_pct":    round(df["is_delivery_delayed"].mean() * 100, 1),
        },
    }
