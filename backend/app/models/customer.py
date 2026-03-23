# ── Customer Pydantic models ───────────────────────────
from pydantic import BaseModel
from typing import Optional

class CustomerKPI(BaseModel):
    customer_id:        str
    customer_name:      Optional[str]
    total_orders:       int
    total_revenue_inr:  float
    total_paid_inr:     float
    avg_o2c_days:       Optional[float]
    cancelled_orders:   int
    unpaid_orders:      int
    risk_score:         int
