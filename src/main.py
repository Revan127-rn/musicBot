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
import src.database.database as db_module
from src.database.database import Database
from src.services.redis_client import redis_client
from src.telegram.handlers import admin, ai_recommendation, liked_songs, playlist, search, start, download
from src.telegram.middlewares.throttling import ThrottlingMiddleware
from src.telegram.middlewares.session_middleware import SessionMiddleware

# Yapılandırma
BASE_URL = os.getenv("RENDER_EXTERNAL_URL" )
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
    # 1. Veritabanı Başlatma (Global Değişkeni Set Et)
    try:
        db_instance = Database(settings.DATABASE_URL)
        await db_instance.init_db()
        db_module.db = db_instance # Diğer modüllerin erişimi için
    except Exception as e:
        logger.error(f"Veritabanı başlatılamadı: {e}")
        return

    # 2. Storage Seçimi (Redis veya Memory)
    storage = MemoryStorage()
    try:
        await redis_client.connect()
        if redis_client.client:
            storage = RedisStorage(
                redis=redis_client.client, 
                key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True)
            )
            logger.info("RedisStorage aktif.")
    except Exception as e:
        logger.warning(f"Redis bağlantısı başarısız, MemoryStorage kullanılıyor: {e}")

    # 3. Bot ve Dispatcher Kurulumu
    bot = Bot(
        token=settings.BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=storage)

    # Debug Middleware (Gelen mesajları loglarda görmek için)
   # Debug Middleware (Admin kullanıcılara hata mesajları gönderir)
    @dp.update.outer_middleware()
    async def debug_middleware(handler, event, data):
        logger.info(f"--- Yeni İstek: {event.event_type} ---")
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Xəta: {e}")
            # Admin-lərə xəta göndər
            error_text = (
                f"🚨 <b>Xəta baş verdi!</b>\n\n"
                f"<code>{type(e).__name__}: {str(e)}</code>\n\n"
                f"<b>Event:</b> {event.event_type}"
            )
            for admin_id in settings.ADMIN_TELEGRAM_IDS:
                try:
                    await bot.send_message(admin_id, error_text)
                except Exception:
                    pass
            raise)

    # Middleware Kayıtları
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.message.middleware(SessionMiddleware())
    dp.callback_query.middleware(SessionMiddleware())

    # Router Kayıtları
    dp.include_router(start.router)
    dp.include_router(search.router)
    dp.include_router(playlist.router)
    dp.include_router(liked_songs.router)
    dp.include_router(ai_recommendation.router)
    dp.include_router(admin.router)
    dp.include_router(download.router)

    # Startup Kaydı
    dp.startup.register(on_startup)

    # 4. Web Sunucusu Kurulumu
    app = web.Application()
    
    # Sağlık Kontrolü
    app.router.add_get("/", lambda r: web.Response(text="Bot is running!"))
    
    # Webhook Handler
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    
    return app

if __name__ == "__main__":
    # Uygulamayı Render'ın beklediği portta başlat
    app = asyncio.run(main())
    if app:
        web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
