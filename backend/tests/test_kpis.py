"""
Tests: KPI endpoints
Run: cd backend && pytest tests/ -v
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.data_service import DataService
from app.services.kpi_service import get_kpi_summary, get_customer_kpis
from app.services.issue_service import get_issue_summary


@pytest.fixture(autouse=True)
def load_data():
    DataService.load()


@pytest.mark.asyncio
async def test_kpi_summary_structure():
    result = await get_kpi_summary()
    assert "overview" in result
    assert "lifecycle_stages" in result
    assert "cycle_times" in result
    assert "issues" in result


@pytest.mark.asyncio
async def test_kpi_total_orders():
    result = await get_kpi_summary()
    assert result["overview"]["total_orders"] == 100


@pytest.mark.asyncio
async def test_kpi_cancellation_rate():
    result = await get_kpi_summary()
    rate = result["issues"]["cancellation_rate_pct"]
    assert 50 <= rate <= 60, f"Unexpected cancellation rate: {rate}"


@pytest.mark.asyncio
async def test_kpi_filtered_by_stage():
    result = await get_kpi_summary(stage="cancelled")
    assert result["overview"]["total_orders"] > 0
    assert "cancelled" in result["lifecycle_stages"]


@pytest.mark.asyncio
async def test_customer_kpis_count():
    customers = await get_customer_kpis()
    assert isinstance(customers, list)
    assert len(customers) == 8


@pytest.mark.asyncio
async def test_issue_summary_structure():
    result = await get_issue_summary()
    assert "total_flagged" in result
    assert "by_type" in result
    assert result["total_flagged"] > 0
