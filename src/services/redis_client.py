import json
import redis.asyncio as redis
from loguru import logger
from src.config import settings

SEARCH_CACHE_TTL = 300  # 5 dəqiqə

class RedisClient:
    def __init__(self):
        self.client: redis.Redis | None = None

    async def connect(self):
        if not settings.REDIS_URL or settings.REDIS_URL.lower() == "none":
            return
        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=5.0,
                retry_on_timeout=True
            )
            await self.client.ping()
            logger.info("Redis bağlantısı quruldu.")
        except Exception as e:
            logger.error(f"Redis hatası: {e}")
            self.client = None
            raise

    async def disconnect(self):
        if self.client:
            try:
                await self.client.close()
            except:
                pass

    async def get_search_results(self, query: str):
        if not self.client:
            return None
        try:
            key = f"search:{query.lower().strip()}"
            data = await self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Redis get xətası: {e}")
            return None

    async def set_search_results(self, query: str, results: list):
        if not self.client:
            return
        try:
            key = f"search:{query.lower().strip()}"
            await self.client.setex(key, SEARCH_CACHE_TTL, json.dumps(results))
        except Exception as e:
            logger.warning(f"Redis set xətası: {e}")

redis_client = RedisClient()
