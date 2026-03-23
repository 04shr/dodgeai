"""Gemini Client — Google Generative Language API"""
import logging
from app.config import GEMINI_API_KEY

log = logging.getLogger("o2c.ai.gemini")

GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
GEMINI_PRO = "https://generativelanguage.googleapis.com/v1/models/gemini-pro-latest:generateContent"
TIMEOUT_SECS = 30


async def gemini_complete(prompt: str, *, pro: bool = False) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured")
    try:
        import httpx
    except ImportError:
        raise RuntimeError("httpx not installed — run: pip install httpx")

    url = GEMINI_PRO if pro else GEMINI_URL
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature":     0.3,
            "maxOutputTokens": 1024,
            "topK": 40,
            "topP": 0.95,
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH",       "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
    }

    async with httpx.AsyncClient(timeout=TIMEOUT_SECS) as client:
        resp = await client.post(f"{url}?key={GEMINI_API_KEY}", json=payload)

    if resp.status_code == 429:
        raise RuntimeError("Gemini rate limited")
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")

    text = candidates[0]["content"]["parts"][0]["text"]
    log.info(f"Gemini OK — {len(text)} chars")
    return text.strip()
