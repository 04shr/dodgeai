# ── Order Pydantic models ──────────────────────────────
from pydantic import BaseModel
from typing import Optional
from datetime import date

class Order(BaseModel):
    sales_order_id:          str
    customer_id:             str
    customer_name:           Optional[str]
    lifecycle_stage:         str
    order_total_net_amount:  Optional[float]
    total_o2c_days:          Optional[float]
    max_issue_severity:      Optional[int]
    is_billing_cancelled:    Optional[bool]
    is_delivery_delayed:     Optional[bool]
    is_unpaid:               Optional[bool]
    missing_stage:           Optional[bool]
