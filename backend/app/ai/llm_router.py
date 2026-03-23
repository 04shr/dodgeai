"""
LLM Router
==========
Dynamically routes AI requests to the best available provider.

Routing table (from config.AI_ROUTING):
  nl_query         → Gemini → Groq → OpenRouter
  root_cause       → OpenRouter → Gemini → Groq
  insights_summary → Groq → Gemini → OpenRouter
  recommendations  → Gemini → OpenRouter → Groq

If the first provider fails (rate limit, no key, timeout), the next
in the chain is tried automatically. All attempts are logged.
"""
# At top of file — this is the problem
from app.config import GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY
import json
import logging
import re
from typing import Optional

from app.ai.gemini_client     import gemini_complete
from app.ai.openrouter_client import openrouter_complete
from app.ai.groq_client       import groq_complete
from app.ai.prompts           import build_prompt
from app.config               import AI_ROUTING

log = logging.getLogger("o2c.ai.router")

CLIENTS = {
    "gemini":     gemini_complete,
    "openrouter": openrouter_complete,
    "groq":       groq_complete,
}


async def route_query(
    use_case: str,
    context:  dict,
    *,
    preferred_model: Optional[str] = None,
) -> tuple[str, str]:
    """
    Route a query through the provider chain.

    Returns:
        (response_text, model_name_used)
    Raises:
        RuntimeError if all providers fail.
    """
    prompt = build_prompt(use_case, context)
    chain  = ([preferred_model] if preferred_model else []) + AI_ROUTING.get(use_case, ["gemini", "groq", "openrouter"])

    errors = []
    for model_name in chain:
        client = CLIENTS.get(model_name)
        if not client:
            continue
        try:
            log.info(f"[{use_case}] Trying {model_name}…")
            response = await client(prompt)
            log.info(f"[{use_case}] {model_name} succeeded ({len(response)} chars)")
            return response, model_name
        except Exception as e:
            log.warning(f"[{use_case}] {model_name} failed: {e}")
            errors.append(f"{model_name}: {e}")

    raise RuntimeError(
        f"All providers failed for use_case='{use_case}'. Errors: {' | '.join(errors)}"
    )


async def parse_insights_json(raw: str) -> list[dict]:
    """
    Safely parse the JSON array returned by insights_summary.
    Falls back to a single insight dict if JSON is malformed.
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()

    # Find first [ ... ] block
    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Try the whole string
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return [parsed]
    except json.JSONDecodeError:
        pass

    # Last resort: return raw text wrapped as one insight
    return [{
        "title":          "AI Insight",
        "summary":        raw[:300],
        "recommendation": "See full response for details.",
        "severity":       "info",
    }]
