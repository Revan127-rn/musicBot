import redis.asyncio as redis
from loguru import logger
from src.config import settings

class RedisClient:
    def __init__(self):
        self.client: redis.Redis | None = None

    async def connect(self):
        # Eğer URL boşsa veya 'none' ise bağlanma
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
        except Exception as e:
            logger.error(f"Redis hatası: {e}")
            self.client = None # Hata durumunda client'ı temizle
            raise

    async def disconnect(self):
        if self.client:
            try:
                await self.client.close()
            except:
                pass

redis_client = RedisClient()
