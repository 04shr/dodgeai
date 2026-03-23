"""Customers Router — /api/customers"""
from fastapi import APIRouter, HTTPException
from app.services.data_service import get_customers, get_customer_by_id, get_customer_orders

router = APIRouter()


@router.get("/")
async def list_customers():
    """All customers with KPI summaries, sorted by risk score."""
    return await get_customers()


@router.get("/{customer_id}")
async def get_customer(customer_id: str):
    """Single customer profile with risk metrics."""
    cust = await get_customer_by_id(customer_id)
    if not cust:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return cust


@router.get("/{customer_id}/orders")
async def customer_orders(customer_id: str):
    """All orders for a specific customer."""
    orders = await get_customer_orders(customer_id)
    if not orders:
        raise HTTPException(status_code=404, detail=f"No orders for customer {customer_id}")
    return {"customer_id": customer_id, "count": len(orders), "orders": orders}
