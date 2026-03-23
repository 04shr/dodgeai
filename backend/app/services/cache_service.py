"""
Cache Service
=============
Simple in-memory TTL cache. Swappable for Redis in production.
Falls back gracefully if cachetools not installed.
"""
import logging
import time
from typing import Any, Optional

log = logging.getLogger("o2c.cache")

try:
    from cachetools import TTLCache
    from app.config import CACHE_TTL
    _store = TTLCache(maxsize=512, ttl=CACHE_TTL)
    _backend = "cachetools"
except ImportError:
    # Lightweight fallback: dict with manual expiry
    _store = {}
    _backend = "dict"
    from app.config import CACHE_TTL

log.info(f"Cache backend: {_backend} (TTL={CACHE_TTL}s)")


class _DictCache:
    """Minimal TTL dict cache used when cachetools is unavailable."""
    def __init__(self):
        self._data: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._data.get(key)
        if not entry:
            return None
        val, expires = entry
        if time.time() > expires:
            del self._data[key]
            return None
        return val

    def set(self, key: str, value: Any) -> None:
        self._data[key] = (value, time.time() + CACHE_TTL)

    def invalidate(self, prefix: str = "") -> int:
        if not prefix:
            count = len(self._data)
            self._data.clear()
            return count
        keys = [k for k in self._data if k.startswith(prefix)]
        for k in keys:
            del self._data[k]
        return len(keys)


class _CachetoolsAdapter:
    def __init__(self, store):
        self._s = store

    def get(self, key: str) -> Optional[Any]:
        return self._s.get(key)

    def set(self, key: str, value: Any) -> None:
        self._s[key] = value

    def invalidate(self, prefix: str = "") -> int:
        if not prefix:
            count = len(self._s)
            self._s.clear()
            return count
        keys = [k for k in list(self._s.keys()) if k.startswith(prefix)]
        for k in keys:
            del self._s[k]
        return len(keys)


if _backend == "cachetools":
    cache = _CachetoolsAdapter(_store)
else:
    cache = _DictCache()
