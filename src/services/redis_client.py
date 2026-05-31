# src/services/redis_client.py dosyasını tamamen bununla değiştirin:
import redis.asyncio as redis
from loguru import logger
from src.config import settings

class RedisClient:
    def __init__(self):
        self.client: redis.Redis | None = None

    async def connect(self):
        try:
            # Otomatik yeniden bağlanma ve ping kontrolü eklendi
            self.client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=10.0,
                socket_connect_timeout=10.0,
                socket_keepalive=True,
                retry_on_timeout=True,
                health_check_interval=30
            )
            await self.client.ping()
            logger.info("Redis bağlantısı başarıyla kuruldu.")
        except Exception as e:
            logger.error(f"Redis bağlantı hatası: {e}")
            raise

    async def disconnect(self):
        if self.client:
            await self.client.close()
            logger.info("Redis bağlantısı kapatıldı.")

redis_client = RedisClient()
