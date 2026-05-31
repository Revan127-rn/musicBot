import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.fsm.storage.memory import MemoryStorage # Yedek hafıza
from loguru import logger

from src.config import settings
from src.database.database import Database
from src.services.redis_client import redis_client
from src.telegram.handlers import admin, ai_recommendation, liked_songs, playlist, search, start, download
from src.telegram.middlewares.throttling import ThrottlingMiddleware
from src.telegram.middlewares.session_middleware import SessionMiddleware

async def handle(request ):
    return web.Response(text="Bot is alive!")

async def main():
    # --- 1. RENDER İÇİN PORTU HEMEN AÇ (Kritik!) ---
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    asyncio.create_task(site.start())
    logger.info(f"Render health check portu {port} üzerinde açıldı.")

    # --- 2. VERİTABANI BAŞLATMA ---
    try:
        db_instance = Database(settings.DATABASE_URL)
        await db_instance.init_db()
        SessionMiddleware.db = db_instance
    except Exception as e:
        logger.error(f"Veritabanı başlatılamadı: {e}")
        # Veritabanı olmadan bot çalışamaz, bu yüzden burada durabiliriz.
        return

    # --- 3. REDIS BAĞLANTISI VE STORAGE SEÇİMİ ---
    storage = MemoryStorage() # Varsayılan olarak hafızayı seç
    try:
        await redis_client.connect()
        if redis_client.client:
            storage = RedisStorage(
                redis=redis_client.client, 
                key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True)
            )
            logger.info("Redis bağlandı, RedisStorage kullanılıyor.")
    except Exception as e:
        logger.warning(f"Redis bağlantısı başarısız, MemoryStorage ile devam ediliyor: {e}")

    # --- 4. BOT VE DISPATCHER ---
    from aiogram.client.default import DefaultBotProperties
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

    logger.info("Bot başarıyla başlatıldı ve dinlemeye geçti...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"Bot durduruldu: {e}")
