import os
import time
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

class CacheBackend:
    """Abstract base class for cache backends."""
    def get(self, key: str) -> Any | None:
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl: int) -> None:
        raise NotImplementedError

class InMemoryCache(CacheBackend):
    """Simple in-memory cache using a dictionary."""
    def __init__(self):
        self._store: dict[str, tuple] = {}

    def get(self, key: str) -> Any | None:
        if key in self._store:
            val, expiry = self._store[key]
            if time.time() < expiry:
                return val
            else:
                del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl: int) -> None:
        self._store[key] = (value, time.time() + ttl)
        logger.debug(f"Cached key {key} in memory (TTL: {ttl}s)")

class RedisCache(CacheBackend):
    """Redis cache backend."""
    def __init__(self, redis_url: str):
        try:
            import redis
            self.client = redis.from_url(redis_url)
            # Test connection
            self.client.ping()
        except ImportError:
            raise ImportError("redis package is not installed")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    def get(self, key: str) -> Any | None:
        try:
            val = self.client.get(key)
            return json.loads(val) if val else None
        except Exception as e:
            logger.warning(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int) -> None:
        try:
            self.client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning(f"Redis set error: {e}")

# Singleton instance
_cache_instance: CacheBackend | None = None

def get_cache() -> CacheBackend:
    """Factory to get the configured cache backend."""
    global _cache_instance
    if _cache_instance:
        return _cache_instance
    
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            _cache_instance = RedisCache(redis_url)
            logger.info("Initialized RedisCache")
            return _cache_instance
        except Exception as e:
            logger.warning(f"Could not initialize RedisCache: {e}. Falling back to InMemoryCache.")
    
    _cache_instance = InMemoryCache()
    logger.info("Initialized InMemoryCache")
    return _cache_instance

def reset_cache_instance():
    """Reset the global cache instance (useful for testing)."""
    global _cache_instance
    _cache_instance = None
