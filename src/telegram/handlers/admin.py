from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.config import settings
from src.services.user_service import UserService
from src.database.models import User, Song
from src.telegram.keyboards import admin_menu_keyboard, main_menu_keyboard

router = Router()


@router.message(F.text == "/admin")
async def admin_command_handler(message: Message, session: AsyncSession):
    user_service = UserService(session)
    if message.from_user.id in settings.ADMIN_TELEGRAM_IDS:
        await message.answer("Admin menüsüne hoş geldiniz!", reply_markup=admin_menu_keyboard())
    else:
        await message.answer("Bu komutu kullanmaya yetkiniz yok.")


@router.callback_query(F.data == "bot_stats")
async def bot_stats_callback(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user.id not in settings.ADMIN_TELEGRAM_IDS:
        await callback.answer("Bu işlemi yapmaya yetkiniz yok.", show_alert=True)
        return

    total_users = await session.scalar(select(func.count(User.id)))
    total_songs = await session.scalar(select(func.count(Song.id)))
    total_downloads = await session.scalar(select(func.count(Song.file_path)).where(Song.file_path.isnot(None)))

    stats_message = (
        f"📊 **Bot İstatistikleri**\n\n"
        f"Toplam Kullanıcı: {total_users}\n"
        f"Toplam Şarkı (Veritabanında): {total_songs}\n"
        f"Toplam İndirilen Şarkı: {total_downloads}\n"
    )
    await callback.message.edit_text(stats_message, reply_markup=admin_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "broadcast_message")
async def broadcast_message_callback(callback: CallbackQuery):
    if callback.from_user.id not in settings.ADMIN_TELEGRAM_IDS:
        await callback.answer("Bu işlemi yapmaya yetkiniz yok.", show_alert=True)
        return
    await callback.message.edit_text("Duyuru mesajınızı girin:", reply_markup=main_menu_keyboard())
    # Implement FSM for broadcast message
    await callback.answer()


@router.callback_query(F.data == "start")
async def back_to_main_menu_from_admin(callback: CallbackQuery):
    await callback.message.edit_text("Ana menüye dönüldü.", reply_markup=main_menu_keyboard())
    await callback.answer()
