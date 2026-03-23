"""KPI Router — /api/kpis"""
from fastapi import APIRouter, Query, HTTPException
from app.services.kpi_service import get_kpi_summary, get_customer_kpis
from app.services.issue_service import get_issue_summary

router = APIRouter()


@router.get("/summary")
async def kpi_summary(
    customer: str = Query(None, description="Filter by customer_id"),
    stage:    str = Query(None, description="Filter by lifecycle_stage"),
):
    """Top-level KPI summary. Optionally filtered by customer or lifecycle stage."""
    return await get_kpi_summary(customer=customer, stage=stage)


@router.get("/customers")
async def customer_kpis():
    """Per-customer KPI breakdown, pre-sorted by risk score."""
    return await get_customer_kpis()


@router.get("/issues/summary")
async def issue_counts():
    """Quick count of flagged orders by issue type — for badge/alert display."""
    return await get_issue_summary()
