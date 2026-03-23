# ── KPI Pydantic models ────────────────────────────────
from pydantic import BaseModel
from typing import Optional

class KPISummary(BaseModel):
    total_orders:             int
    total_revenue_inr:        float
    revenue_leakage_inr:      float
    cancellation_rate_pct:    float
    avg_total_o2c_days:       Optional[float]
    orders_unpaid:            int
