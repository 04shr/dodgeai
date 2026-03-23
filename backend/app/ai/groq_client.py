"""Groq Client — OpenAI-compatible API (ultra-fast inference)"""
import logging
from app.config import GROQ_API_KEY

log = logging.getLogger("o2c.ai.groq")

GROQ_URL      = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.1-8b-instant"
TIMEOUT_SECS  = 20          # Groq is fast; shorter timeout


async def groq_complete(prompt: str, *, model: str = DEFAULT_MODEL) -> str:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not configured")
    try:
        import httpx
    except ImportError:
        raise RuntimeError("httpx not installed — run: pip install httpx")

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature":  0.3,
        "max_tokens":   1024,
        "stream":       False,
    }

    async with httpx.AsyncClient(timeout=TIMEOUT_SECS) as client:
        resp = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json=payload,
        )

    if resp.status_code == 429:
        raise RuntimeError("Groq rate limited")
    if resp.status_code != 200:
        raise RuntimeError(f"Groq error {resp.status_code}: {resp.text[:200]}")

    text = resp.json()["choices"][0]["message"]["content"]
    log.info(f"Groq ({model}) OK — {len(text)} chars")
    return text.strip()
