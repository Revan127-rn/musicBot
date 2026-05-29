from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext
from src.services.user_service import UserService
from src.telegram.keyboards import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user_service = UserService(session)
    await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    await message.answer(
        f"Merhaba {message.from_user.full_name}! Müzik botuna hoş geldin. Ne yapmak istersin?",
        reply_markup=main_menu_keyboard(),
    )
