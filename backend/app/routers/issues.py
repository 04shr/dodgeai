"""Issues Router — /api/issues"""
from fastapi import APIRouter, Query
from app.services.issue_service import get_issues, get_issue_summary

router = APIRouter()


@router.get("/")
async def list_issues(
    issue_type:   str = Query(None, description="delayed | cancelled | unpaid | missing"),
    min_severity: int = Query(None, ge=1, le=5),
    customer:     str = Query(None),
    stage:        str = Query(None),
    limit:        int = Query(200, ge=1, le=500),
    offset:       int = Query(0, ge=0),
):
    """All flagged orders with issue type annotations."""
    return await get_issues(
        issue_type=issue_type, min_severity=min_severity,
        customer=customer, stage=stage,
        limit=limit, offset=offset,
    )


@router.get("/summary")
async def issue_summary():
    """Counts by type and severity — for dashboard overview tiles."""
    return await get_issue_summary()
