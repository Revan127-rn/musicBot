import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from loguru import logger

from src.config import settings
from src.database.database import Database
from src.services.redis_client import redis_client
from src.telegram.handlers import admin, ai_recommendation, liked_songs, playlist, search, start, download
from src.telegram.middlewares.throttling import ThrottlingMiddleware
from src.telegram.middlewares.session_middleware import SessionMiddleware

async def main():
    # 1. Veritabanı Başlatma
    db_instance = Database(settings.DATABASE_URL)
    await db_instance.init_db()
    SessionMiddleware.db = db_instance

    # 2. Redis Başlatma
    await redis_client.connect()
    storage = RedisStorage(
        redis=redis_client.client, 
        key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True)
    )

    # 3. Bot ve Dispatcher
    bot = Bot(settings.BOT_TOKEN, parse_mode=ParseMode.HTML)
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
        logger.exception(f"KRİTİK HATA: {e}")
    finally:
        try:
            asyncio.run(redis_client.disconnect())
        except:
            pass

