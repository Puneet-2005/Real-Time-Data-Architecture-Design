"""
price_cache.py — simulates Redis in-memory price store.
In production this would be actual Redis (redis-py client).
Here we use a Python dict + threading lock for thread safety.
"""
import threading
import time
from datetime import datetime

_lock  = threading.Lock()
_cache = {}          # route_key -> price_record
_stats = {
    "hits": 0,
    "writes": 0,
    "last_write": None,
}


def set_price(route_key: str, price_record: dict):
    """Write a price record into the cache."""
    with _lock:
        _cache[route_key] = {
            **price_record,
            "_cached_at": datetime.now().isoformat(),
        }
        _stats["writes"] += 1
        _stats["last_write"] = datetime.now().strftime("%H:%M:%S")


def get_price(route_key: str) -> dict | None:
    """Read a price from the cache. Returns None on miss."""
    with _lock:
        record = _cache.get(route_key)
        if record:
            _stats["hits"] += 1
        return record


def get_all() -> dict:
    """Return a snapshot of all cached prices."""
    with _lock:
        return dict(_cache)


def bulk_set(prices: dict):
    """Write multiple prices at once (used after full recompute)."""
    with _lock:
        for key, record in prices.items():
            _cache[key] = {
                **record,
                "_cached_at": datetime.now().isoformat(),
            }
        _stats["writes"] += len(prices)
        _stats["last_write"] = datetime.now().strftime("%H:%M:%S")


def cache_stats() -> dict:
    with _lock:
        return {
            **_stats,
            "keys_stored": len(_cache),
        }
