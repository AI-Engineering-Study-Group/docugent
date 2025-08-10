"""
Redis service for caching.
"""
import redis
import json
import logging
from typing import Optional, Any
from app.config.settings import settings

logger = logging.getLogger(__name__)

class RedisService:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.redis_url = settings.redis_url
        self.client = None
        try:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            self.client.ping()
            logger.info("Successfully connected to Redis.")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to Redis: {e}")
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        if not self.client:
            return None
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis GET error: {e}")
        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        if not self.client:
            return
        try:
            self.client.set(key, json.dumps(value), ex=ttl)
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis SET error: {e}")

    def get_stats(self):
        if not self.client:
            return {"status": "disconnected"}
        try:
            return self.client.info()
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis INFO error: {e}")
            return {"status": "error", "message": str(e)}

    def clear_cache(self):
        if not self.client:
            return {"status": "disconnected"}
        try:
            keys_deleted = self.client.flushdb()
            logger.info("Redis cache cleared.")
            return {"status": "success", "keys_deleted": keys_deleted}
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis FLUSHDB error: {e}")
            return {"status": "error", "message": str(e)}
