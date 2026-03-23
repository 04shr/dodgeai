"""
Firebase Firestore Service
===========================
Persists AI query history and generated insights to Firestore.
Silently disabled if credentials file is missing (dev mode).

Collections:
  ai_queries   — every NL query + response
  insights     — system-generated insight cards
  sessions     — per-session context
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from app.config import FIREBASE_CREDENTIALS, FIREBASE_ENABLED

log = logging.getLogger("o2c.firebase")

_db = None


def get_db():
    global _db
    if _db is not None:
        return _db
    if not FIREBASE_ENABLED:
        log.warning("Firebase credentials not found — persistence disabled (dev mode)")
        return None
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS)
            firebase_admin.initialize_app(cred)
        _db = firestore.client()
        log.info("Firebase connected ✓")
        return _db
    except Exception as e:
        log.error(f"Firebase init failed: {e}")
        return None


async def save_query(
    question:   str,
    answer:     str,
    model_used: str,
    use_case:   str = "nl_query",
    order_id:   Optional[str] = None,
) -> Optional[str]:
    """Save an AI query + response. Returns document ID or None."""
    db = get_db()
    if not db:
        return None
    try:
        from firebase_admin import firestore as fs
        doc_ref = db.collection("ai_queries").document()
        doc_ref.set({
            "question":   question,
            "answer":     answer,
            "model_used": model_used,
            "use_case":   use_case,
            "order_id":   order_id,
            "timestamp":  fs.SERVER_TIMESTAMP,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return doc_ref.id
    except Exception as e:
        log.warning(f"Failed to save query: {e}")
        return None


async def save_insight(insight: dict) -> Optional[str]:
    """Save a generated insight card."""
    db = get_db()
    if not db:
        return None
    try:
        from firebase_admin import firestore as fs
        doc_ref = db.collection("insights").document()
        doc_ref.set({**insight, "timestamp": fs.SERVER_TIMESTAMP})
        return doc_ref.id
    except Exception as e:
        log.warning(f"Failed to save insight: {e}")
        return None


async def get_recent_queries(limit: int = 20) -> list[dict]:
    """Fetch recent AI queries for history panel."""
    db = get_db()
    if not db:
        return []
    try:
        from firebase_admin import firestore as fs
        docs = (
            db.collection("ai_queries")
            .order_by("timestamp", direction=fs.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        return [{"id": d.id, **d.to_dict()} for d in docs]
    except Exception as e:
        log.warning(f"Failed to fetch queries: {e}")
        return []


async def get_insights(limit: int = 10) -> list[dict]:
    """Fetch stored insight cards."""
    db = get_db()
    if not db:
        return []
    try:
        from firebase_admin import firestore as fs
        docs = (
            db.collection("insights")
            .order_by("timestamp", direction=fs.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        return [{"id": d.id, **d.to_dict()} for d in docs]
    except Exception as e:
        log.warning(f"Failed to fetch insights: {e}")
        return []
