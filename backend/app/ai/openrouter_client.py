"""OpenRouter Client — multi-model gateway with fallback models"""
import logging
from app.config import OPENROUTER_API_KEY

log = logging.getLogger("o2c.ai.openrouter")

OPENROUTER_URL  = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL   = "anthropic/claude-3-haiku"
FALLBACK_MODEL  = "mistralai/mistral-7b-instruct"
TIMEOUT_SECS    = 30


async def openrouter_complete(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
) -> str:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not configured")
    try:
        import httpx
    except ImportError:
        raise RuntimeError("httpx not installed — run: pip install httpx")

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens":  1024,
    }

    headers = {
        "Authorization":  f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type":   "application/json",
        "HTTP-Referer":   "https://o2c-intelligence.app",
        "X-Title":        "O2C Intelligence",
    }

    async with httpx.AsyncClient(timeout=TIMEOUT_SECS) as client:
        resp = await client.post(OPENROUTER_URL, headers=headers, json=payload)

    if resp.status_code == 429:
        raise RuntimeError(f"OpenRouter rate limited (model={model})")
    if resp.status_code != 200:
        raise RuntimeError(f"OpenRouter error {resp.status_code}: {resp.text[:200]}")

    text = resp.json()["choices"][0]["message"]["content"]
    log.info(f"OpenRouter ({model}) OK — {len(text)} chars")
    return text.strip()
