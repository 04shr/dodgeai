# ── Issue Pydantic models ──────────────────────────────
from pydantic import BaseModel
from typing import Optional, List

class Issue(BaseModel):
    order_id:     str
    customer_id:  str
    issue_type:   str   # delayed | cancelled | unpaid | missing
    severity:     int
    description:  Optional[str]
