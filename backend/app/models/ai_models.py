# ── AI request/response models ─────────────────────────
from pydantic import BaseModel
from typing import Optional, List

class AIQueryResponse(BaseModel):
    answer:      str
    model_used:  Optional[str]
    cached:      bool = False

class RootCauseResponse(BaseModel):
    order_id:        str
    analysis:        str
    recommendations: List[str]
