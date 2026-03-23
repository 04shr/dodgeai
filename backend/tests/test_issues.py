"""Tests: Issues endpoint"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.data_service import DataService
from app.services.issue_service import get_issues, get_issue_summary


@pytest.fixture(autouse=True)
def load_data():
    DataService.load()


@pytest.mark.asyncio
async def test_all_issues():
    result = await get_issues()
    assert result["total"] > 0
    assert all("issue_labels" in row for row in result["data"])


@pytest.mark.asyncio
async def test_filter_cancelled():
    result = await get_issues(issue_type="cancelled")
    assert result["total"] > 0
    assert all("Billing document cancelled" in row["issue_labels"] for row in result["data"])


@pytest.mark.asyncio
async def test_filter_unpaid():
    result = await get_issues(issue_type="unpaid")
    assert result["total"] > 0
    assert all(row["is_unpaid"] is True for row in result["data"])


@pytest.mark.asyncio
async def test_issue_summary_counts():
    s = await get_issue_summary()
    assert s["by_type"]["cancelled"] == 56
    assert s["by_type"]["unpaid"]    == 22
    assert s["by_type"]["missing"]   == 17
    assert s["by_type"]["delayed"]   == 9
