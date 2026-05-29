import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from loguru import logger

from src.config import settings
from src.database.database import Database, get_db_session
from src.services.redis_client import redis_client

# Handlers
from src.telegram.handlers import admin, ai_recommendation, liked_songs, playlist, search, start, download

# Middlewares
from src.telegram.middlewares.throttling import ThrottlingMiddleware
from src.telegram.middlewares.session_middleware import SessionMiddleware


class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger.opt(depth=6, exception=record.exc_info).log(record.levelname, record.getMessage())


def setup_logging():
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


async def main():
    setup_logging()

    # Initialize Database
    db_instance = Database(settings.DATABASE_URL)
    await db_instance.init_db()

    # Pass db_instance to SessionMiddleware
    SessionMiddleware.db = db_instance

    # Initialize Redis for FSM and caching
    await redis_client.connect()
    storage = RedisStorage(redis=redis_client.client, key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True))

    bot = Bot(settings.BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=storage)

    # Register middlewares
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.message.middleware(SessionMiddleware())
    dp.callback_query.middleware(SessionMiddleware())

    # Register routers
    dp.include_router(start.router)
    dp.include_router(search.router)
    dp.include_router(playlist.router)
    dp.include_router(liked_songs.router)
    dp.include_router(ai_recommendation.router)
    dp.include_router(admin.router)
    dp.include_router(download.router)

    # Register database session middleware (if needed, or pass session via DI)


    logger.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


# src/main.py dosyasının en altındaki bloğu şu şekilde güncelleyin:

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        # Kritik hataları loglamak için güncellendi
        logger.exception(f"Bot başlatılırken kritik bir hata oluştu: {e}")
    finally:
        try:
            asyncio.run(redis_client.disconnect())
        except:
            pass
