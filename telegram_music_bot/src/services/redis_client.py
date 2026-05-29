import json
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from loguru import logger

from src.config import settings


class RedisClient:
    def __init__(self):
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        if not self.client:
            self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            logger.info("Connected to Redis.")

    async def disconnect(self):
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Disconnected from Redis.")

    async def set_cache(self, key: str, value: Any, ex: int = 3600):
        """Sets a value in Redis cache with an expiration time (default 1 hour)."""
        if not self.client:
            await self.connect()
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await self.client.set(key, value, ex=ex)
            logger.debug(f"Cache set for key: {key}")
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {e}")

    async def get_cache(self, key: str) -> Optional[Any]:
        """Gets a value from Redis cache."""
        if not self.client:
            await self.connect()
        try:
            value = await self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {e}")
            return None

    async def delete_cache(self, key: str):
        """Deletes a value from Redis cache."""
        if not self.client:
            await self.connect()
        try:
            await self.client.delete(key)
            logger.debug(f"Cache deleted for key: {key}")
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")

    async def get_search_results(self, query: str) -> Optional[List[Dict[str, Any]]]:
        return await self.get_cache(f"youtube_search:{query}")

    async def set_search_results(self, query: str, results: List[Dict[str, Any]], ex: int = 3600):
        await self.set_cache(f"youtube_search:{query}", results, ex)

    async def get_ai_recommendation(self, user_input: str) -> Optional[Dict[str, Any]]:
        return await self.get_cache(f"ai_recommendation:{user_input}")

    async def set_ai_recommendation(self, user_input: str, recommendation: Dict[str, Any], ex: int = 3600):
        await self.set_cache(f"ai_recommendation:{user_input}", recommendation, ex)


redis_client = RedisClient()
