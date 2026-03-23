"""Orders Router — /api/orders"""
from fastapi import APIRouter, Query, HTTPException
from app.services.data_service import get_orders, get_order_by_id, get_order_items

router = APIRouter()


@router.get("/")
async def list_orders(
    customer:     str = Query(None,  description="Filter by customer_id"),
    stage:        str = Query(None,  description="Filter by lifecycle_stage"),
    issue_type:   str = Query(None,  description="delayed | cancelled | unpaid | missing"),
    min_severity: int = Query(None,  ge=1, le=5, description="Minimum issue severity (1–5)"),
    sort_by:      str = Query("order_created_date", description="Column to sort by"),
    sort_dir:     str = Query("desc", description="asc or desc"),
    limit:        int = Query(100, ge=1, le=500),
    offset:       int = Query(0,   ge=0),
):
    """List orders with filters, sorting, and pagination."""
    return await get_orders(
        customer=customer, stage=stage,
        issue_type=issue_type, min_severity=min_severity,
        sort_by=sort_by, sort_dir=sort_dir,
        limit=limit, offset=offset,
    )


@router.get("/{order_id}")
async def get_order(order_id: str):
    """Single order header with computed KPIs and issue flags."""
    order = await get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return order


@router.get("/{order_id}/items")
async def get_order_items_endpoint(order_id: str):
    """All line items for a specific order."""
    items = await get_order_items(order_id)
    if not items:
        raise HTTPException(status_code=404, detail=f"No items found for order {order_id}")
    return {"order_id": order_id, "count": len(items), "items": items}
