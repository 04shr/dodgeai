"""Tests: Orders endpoints"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.data_service import DataService, get_orders, get_order_by_id, get_order_items


@pytest.fixture(autouse=True)
def load_data():
    DataService.load()


@pytest.mark.asyncio
async def test_list_orders_total():
    result = await get_orders()
    assert result["total"] == 100
    assert len(result["data"]) == 100


@pytest.mark.asyncio
async def test_filter_by_stage_cancelled():
    result = await get_orders(stage="cancelled")
    assert result["total"] > 0
    assert all(o["lifecycle_stage"] == "cancelled" for o in result["data"])


@pytest.mark.asyncio
async def test_filter_by_issue_type():
    result = await get_orders(issue_type="cancelled")
    assert result["total"] > 0
    assert all(o["is_billing_cancelled"] is True for o in result["data"])


@pytest.mark.asyncio
async def test_pagination():
    result = await get_orders(limit=10, offset=0)
    assert len(result["data"]) == 10
    result2 = await get_orders(limit=10, offset=10)
    ids1 = {o["sales_order_id"] for o in result["data"]}
    ids2 = {o["sales_order_id"] for o in result2["data"]}
    assert ids1.isdisjoint(ids2), "Paginated pages overlap"


@pytest.mark.asyncio
async def test_get_order_by_id():
    all_orders = await get_orders(limit=1)
    sample_id = str(all_orders["data"][0]["sales_order_id"])
    order = await get_order_by_id(sample_id)
    assert order is not None
    assert str(order["sales_order_id"]) == sample_id


@pytest.mark.asyncio
async def test_get_order_not_found():
    result = await get_order_by_id("DOES_NOT_EXIST")
    assert result is None


@pytest.mark.asyncio
async def test_get_order_items():
    all_orders = await get_orders(limit=1)
    sample_id = str(all_orders["data"][0]["sales_order_id"])
    items = await get_order_items(sample_id)
    assert isinstance(items, list)
    assert len(items) >= 1
