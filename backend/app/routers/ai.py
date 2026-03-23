"""
AI Router — /api/ai
====================
Endpoints for natural language querying, root cause analysis,
system-wide insight generation, and query history.
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from app.ai.llm_router import route_query, parse_insights_json
from app.services.data_service import get_order_context, get_customer_by_id
from app.services.firebase_service import (
    save_query, save_insight, get_recent_queries, get_insights
)
from app.services.cache_service import cache

log = logging.getLogger("o2c.router.ai")
router = APIRouter()


# ── Request / Response models ─────────────────────────────
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    preferred_model: Optional[str] = Field(None, description="gemini | groq | openrouter")


class RootCauseRequest(BaseModel):
    order_id: str


class CustomerRiskRequest(BaseModel):
    customer_id: str


# ── NL Query ──────────────────────────────────────────────
@router.post("/query")
async def query_ai(req: QueryRequest):
    """
    Natural language query over the O2C dataset.
    Routes to best available LLM with automatic fallback.
    """
    cache_key = f"nlq:{req.question[:80]}"
    if (cached := cache.get(cache_key)):
        return {**cached, "cached": True}

    try:
        answer, model_used = await route_query(
            "nl_query",
            {"question": req.question},
            preferred_model=req.preferred_model,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    result = {"answer": answer, "model_used": model_used, "cached": False}
    cache.set(cache_key, result)

    # Persist to Firestore (non-blocking — failures don't affect response)
    await save_query(req.question, answer, model_used, use_case="nl_query")

    return result


# ── Root Cause Analysis ───────────────────────────────────
@router.post("/root-cause")
async def root_cause(req: RootCauseRequest):
    """
    Deep analysis of a specific order.
    Sends full order + items context to LLM for root cause diagnosis.
    """
    cache_key = f"rca:{req.order_id}"
    if (cached := cache.get(cache_key)):
        return {**cached, "cached": True}

    context = await get_order_context(req.order_id)
    if not context.get("order"):
        raise HTTPException(status_code=404, detail=f"Order {req.order_id} not found")

    try:
        raw, model_used = await route_query("root_cause", context)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Parse recommendations from numbered list in response
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    analysis = ""
    recommendations = []
    parsing_recs = False

    for line in lines:
        if any(line.startswith(str(i) + ".") for i in range(1, 6)):
            parsing_recs = True
            recommendations.append(line.lstrip("0123456789. "))
        elif not parsing_recs:
            analysis += (" " + line) if analysis else line

    result = {
        "order_id":        req.order_id,
        "analysis":        analysis.strip() or raw[:400],
        "recommendations": recommendations or ["Review order lifecycle for any incomplete stages."],
        "model_used":      model_used,
        "cached":          False,
    }
    cache.set(cache_key, result)
    await save_query(
        f"Root cause: order {req.order_id}",
        raw, model_used, use_case="root_cause", order_id=req.order_id,
    )
    return result


# ── System-wide Insights ──────────────────────────────────
@router.get("/insights")
async def get_ai_insights(refresh: bool = Query(False)):
    """
    Generate 3 system-wide insights about the O2C dataset.
    Results are cached and also stored in Firestore.
    """
    cache_key = "insights:system"
    if not refresh and (cached := cache.get(cache_key)):
        return {"insights": cached, "cached": True}

    # Check Firestore first (avoids repeated LLM calls)
    stored = await get_insights(limit=3)
    if stored and not refresh:
        cache.set(cache_key, stored)
        return {"insights": stored, "cached": True, "source": "firestore"}

    try:
        raw, model_used = await route_query("insights_summary", {})
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    insights = await parse_insights_json(raw)

    # Save each insight to Firestore
    for insight in insights:
        await save_insight({**insight, "model_used": model_used})

    cache.set(cache_key, insights)
    return {"insights": insights, "model_used": model_used, "cached": False}


# ── Customer Risk Assessment ──────────────────────────────
@router.post("/customer-risk")
async def customer_risk(req: CustomerRiskRequest):
    """AI risk assessment narrative for a specific customer."""
    cache_key = f"cust_risk:{req.customer_id}"
    if (cached := cache.get(cache_key)):
        return {**cached, "cached": True}

    customer = await get_customer_by_id(req.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {req.customer_id} not found")

    try:
        analysis, model_used = await route_query("customer_risk", {"customer": customer})
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    result = {"customer_id": req.customer_id, "analysis": analysis, "model_used": model_used, "cached": False}
    cache.set(cache_key, result)
    return result


# ── Query History ─────────────────────────────────────────
@router.get("/history")
async def query_history(limit: int = Query(20, ge=1, le=100)):
    """Recent AI query history from Firestore."""
    history = await get_recent_queries(limit=limit)
    return {"count": len(history), "history": history}
