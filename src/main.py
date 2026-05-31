import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.client.default import DefaultBotProperties
from loguru import logger

from src.config import settings
from src.database.database import Database
from src.services.redis_client import redis_client
from src.telegram.handlers import admin, ai_recommendation, liked_songs, playlist, search, start, download
from src.telegram.middlewares.throttling import ThrottlingMiddleware
from src.telegram.middlewares.session_middleware import SessionMiddleware

# Render tarafından sağlanan otomatik URL (örn: https://musicbot-6v34.onrender.com )
BASE_URL = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_PATH = f"/webhook/{settings.BOT_TOKEN}"

async def on_startup(bot: Bot):
    """Bot başladığında Telegram'a webhook adresini bildirir."""
    webhook_url = f"{BASE_URL}{WEBHOOK_PATH}"
    logger.info(f"Webhook ayarlanıyor: {webhook_url}")
    await bot.set_webhook(
        url=webhook_url,
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"]
    )

async def main():
    # 1. Veritabanı
    try:
        db_instance = Database(settings.DATABASE_URL)
        await db_instance.init_db()
        SessionMiddleware.db = db_instance
    except Exception as e:
        logger.error(f"Veritabanı hatası: {e}")
        return

    # 2. Storage (Redis veya Memory)
    storage = MemoryStorage()
    try:
        await redis_client.connect()
        if redis_client.client:
            storage = RedisStorage(
                redis=redis_client.client, 
                key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True)
            )
            logger.info("RedisStorage aktif.")
    except:
        logger.warning("Redis bağlantısı yok, MemoryStorage kullanılıyor.")

    # 3. Bot ve Dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=storage)

    # Middlewares
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.message.middleware(SessionMiddleware())
    dp.callback_query.middleware(SessionMiddleware())

    # Routers
    dp.include_router(start.router)
    dp.include_router(search.router)
    dp.include_router(playlist.router)
    dp.include_router(liked_songs.router)
    dp.include_router(ai_recommendation.router)
    dp.include_router(admin.router)
    dp.include_router(download.router)

    # Startup işlemini kaydet
    dp.startup.register(on_startup)

    # 4. Web Sunucusu (Webhook için)
    app = web.Application()
    
    # Render Sağlık Kontrolü
    app.router.add_get("/", lambda r: web.Response(text="Bot is running in Webhook mode!"))
    
    # Telegram Webhook İşleyici
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Uygulamayı kur ve başlat
    setup_application(app, dp, bot=bot)
    
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Bot Webhook modunda {port} portunda başlatılıyor...")
    
    return app

if __name__ == "__main__":
    # Render/aiohttp için uygulama başlatma
    app = asyncio.run(main( ))
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
