"""
Tests: AI layer (prompt building + router logic)
These tests do NOT call real LLM APIs — they test prompt construction
and the routing/fallback logic with mock clients.
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.data_service import DataService
from app.ai.prompts import build_prompt
from app.ai.llm_router import parse_insights_json


@pytest.fixture(autouse=True)
def load_data():
    DataService.load()


def test_nl_query_prompt_contains_question():
    prompt = build_prompt("nl_query", {"question": "What is the cancellation rate?"})
    assert "cancellation rate" in prompt.lower()
    assert "O2C" in prompt


def test_root_cause_prompt_contains_order():
    prompt = build_prompt("root_cause", {"order": {"sales_order_id": "740506"}, "items": []})
    assert "740506" in prompt
    assert "root cause" in prompt.lower()


def test_insights_prompt_requests_json():
    prompt = build_prompt("insights_summary", {})
    assert "JSON" in prompt
    assert "title" in prompt


def test_dataset_context_injected():
    prompt = build_prompt("nl_query", {"question": "test"})
    # Should contain real stats from the dataset
    assert "100" in prompt   # total orders
    assert "INR" in prompt


@pytest.mark.asyncio
async def test_parse_insights_valid_json():
    raw = '[{"title":"T","summary":"S","recommendation":"R","severity":"info"}]'
    result = await parse_insights_json(raw)
    assert len(result) == 1
    assert result[0]["title"] == "T"


@pytest.mark.asyncio
async def test_parse_insights_markdown_fenced():
    raw = '```json\n[{"title":"T","summary":"S","recommendation":"R","severity":"warning"}]\n```'
    result = await parse_insights_json(raw)
    assert result[0]["severity"] == "warning"


@pytest.mark.asyncio
async def test_parse_insights_malformed_fallback():
    raw = "This is not JSON at all"
    result = await parse_insights_json(raw)
    assert isinstance(result, list)
    assert len(result) == 1
    assert "AI Insight" in result[0]["title"]

@pytest.mark.asyncio
async def test_router_raises_when_no_keys(monkeypatch):
    """With no API keys, route_query should raise RuntimeError."""
    import app.ai.llm_router as router

    async def fake_fail(prompt):
        raise Exception("no key")

    monkeypatch.setitem(router.CLIENTS, "gemini",     fake_fail)
    monkeypatch.setitem(router.CLIENTS, "groq",       fake_fail)
    monkeypatch.setitem(router.CLIENTS, "openrouter", fake_fail)

    with pytest.raises(RuntimeError, match="All providers failed"):
        await router.route_query("nl_query", {"question": "test"})