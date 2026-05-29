from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from src.youtube.client import youtube_client
from src.services.song_service import SongService
from src.telegram.keyboards import search_results_keyboard, song_actions_keyboard, main_menu_keyboard
from src.services.redis_client import redis_client

router = Router()


class SearchStates(StatesGroup):
    waiting_for_query = State()


@router.callback_query(F.data == "search_music")
async def search_music_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Lütfen aramak istediğiniz şarkının adını, sanatçısını veya YouTube linkini girin:")
    await state.set_state(SearchStates.waiting_for_query)
    await callback.answer()


@router.message(SearchStates.waiting_for_query)
async def process_search_query(message: Message, state: FSMContext, session: AsyncSession):
    query = message.text
    if not query:
        await message.answer("Geçersiz giriş. Lütfen tekrar deneyin.")
        return

    await message.answer(f"\"**{query}**\" için arama yapılıyor...")

    # Check cache first
    cached_results = await redis_client.get_search_results(query)
    if cached_results:
        results = cached_results
    else:
        results = await youtube_client.search_video(query)
        await redis_client.set_search_results(query, results)

    if not results:
        await message.answer("Üzgünüm, aramanızla eşleşen bir sonuç bulunamadı.", reply_markup=main_menu_keyboard())
        await state.clear()
        return

    await message.answer(
        "Arama sonuçları:",
        reply_markup=search_results_keyboard(results, current_page=0)
    )
    await state.clear()


@router.callback_query(F.data.startswith("select_song:"))
async def select_song_callback(callback: CallbackQuery, session: AsyncSession):
    youtube_id = callback.data.split(":")[1]
    song_service = SongService(session)

    # Get song info from YouTube (or cache if available)
    song_info = await youtube_client.get_video_info(f"https://www.youtube.com/watch?v={youtube_id}")
    if not song_info:
        await callback.message.answer("Şarkı bilgileri alınamadı.")
        await callback.answer()
        return

    song = await song_service.get_or_create_song(
        youtube_id=youtube_id,
        title=song_info["title"],
        artist=song_info["artist"],
        duration=song_info["duration"],
        thumbnail_url=song_info["thumbnail"],
    )

    is_liked = await song_service.is_song_liked(callback.from_user.id, song.id)

    await callback.message.edit_text(
        f"**{song.title}** - {song.artist}\nSüre: {song.duration // 60:02d}:{song.duration % 60:02d}",
        reply_markup=song_actions_keyboard(song.id, song.youtube_id, is_liked=is_liked)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("search_page:"))
async def search_page_callback(callback: CallbackQuery, session: AsyncSession):
    # This part needs more complex state management if search results are not cached per user
    # For simplicity, we'll assume a fresh search or a simple pagination for a limited set of results
    # In a real app, you'd store search results in FSM or Redis for pagination
    await callback.answer("Sayfalama özelliği şu an için sadece örnek amaçlıdır. Geliştirme aşamasındadır.")
    # For now, just return to main menu
    await callback.message.edit_text("Ana menüye dönülüyor.", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "search_again")
async def search_again_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Lütfen aramak istediğiniz şarkının adını, sanatçısını veya YouTube linkini girin:")
    await state.set_state(SearchStates.waiting_for_query)
    await callback.answer()
