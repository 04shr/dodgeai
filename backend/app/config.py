"""
O2C Intelligence — Centralised Configuration
=============================================
All env vars loaded here. Import from app.config everywhere else.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────
# Resolved relative to the backend/ directory at runtime
_BASE = Path(__file__).resolve().parent.parent          # → backend/
DATA_DIR = Path(os.getenv("DATA_DIR", str(_BASE / ".." / "data" / "processed"))).resolve()

# ── Server ─────────────────────────────────────────────────
PORT           = int(os.getenv("FASTAPI_PORT", 8000))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8080")

# ── Cache ──────────────────────────────────────────────────
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", 300))

# ── AI Provider Keys ───────────────────────────────────────
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GROQ_API_KEY       = os.getenv("GROQ_API_KEY", "")

# ── AI Routing ─────────────────────────────────────────────
# Which providers to try per use-case (first available wins)
AI_ROUTING: dict[str, list[str]] = {
    "nl_query":         ["gemini", "groq", "openrouter"],
    "root_cause":       ["openrouter", "gemini", "groq"],
    "insights_summary": ["groq", "gemini", "openrouter"],
    "recommendations":  ["gemini", "openrouter", "groq"],
}

# ── Firebase ───────────────────────────────────────────────
FIREBASE_CREDENTIALS = os.getenv(
    "FIREBASE_CREDENTIALS_PATH",
    str(_BASE / "firebase-service-account.json"),
)
FIREBASE_ENABLED = os.path.exists(FIREBASE_CREDENTIALS)

# ── Issue Detection Thresholds ─────────────────────────────
DELIVERY_DELAY_DAYS  = int(os.getenv("DELIVERY_DELAY_DAYS",  3))
PAYMENT_OVERDUE_DAYS = int(os.getenv("PAYMENT_OVERDUE_DAYS", 30))

PAYMENT_TERM_DAYS: dict[str, int] = {
    "Z001": 30,
    "Z009": 0,
}
DEFAULT_PAYMENT_DAYS = 30
