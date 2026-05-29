from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.client import groq_ai_client
from src.youtube.client import youtube_client
from src.services.song_service import SongService
from src.telegram.keyboards import search_results_keyboard, main_menu_keyboard, cancel_keyboard
from src.services.redis_client import redis_client

router = Router()


class AIRecommendationStates(StatesGroup):
    waiting_for_description = State()


@router.callback_query(F.data == "ai_recommendations")
async def ai_recommendations_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Nasıl bir müzik arıyorsunuz? Ruh halinizi, türü veya sanatçı tarzını açıklayın. "
        "Örn: 'gece araba sürerken dinlenecek karanlık phonk' veya 'The Weeknd tarzı'.",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AIRecommendationStates.waiting_for_description)
    await callback.answer()


@router.message(AIRecommendationStates.waiting_for_description)
async def process_ai_description(message: Message, state: FSMContext, session: AsyncSession):
    user_input = message.text
    if not user_input:
        await message.answer("Geçersiz giriş. Lütfen tekrar deneyin.")
        return

    await message.answer(f"\"**{user_input}**\" açıklamasına göre müzik önerileri aranıyor...")

    # Check cache first
    cached_recommendation = await redis_client.get_ai_recommendation(user_input)
    if cached_recommendation:
        ai_response = cached_recommendation
    else:
        ai_response = await groq_ai_client.get_music_recommendation_prompt(user_input)
        await redis_client.set_ai_recommendation(user_input, ai_response)

    search_query = ai_response.get("keywords", user_input)

    # Search YouTube with AI-generated keywords
    youtube_results = await youtube_client.search_video(search_query)

    if not youtube_results:
        await message.answer("Üzgünüm, bu açıklamaya uygun müzik bulunamadı.", reply_markup=main_menu_keyboard())
        await state.clear()
        return

    await message.answer(
        "AI tarafından önerilen müzikler:",
        reply_markup=search_results_keyboard(youtube_results)
    )
    await state.clear()


@router.callback_query(F.data.startswith("ai_recommend_similar:"))
async def ai_recommend_similar_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    youtube_id = callback.data.split(":")[1]
    song_service = SongService(session)
    song = await song_service.get_song_by_youtube_id(youtube_id)

    if not song:
        await callback.message.answer("Şarkı bulunamadı.")
        await callback.answer()
        return

    user_input = f"Benzer müzikler: {song.title} - {song.artist}"
    await callback.message.edit_text(
        f"\"**{song.title}**\" şarkısına benzer müzikler aranıyor...",
        reply_markup=cancel_keyboard()
    )

    # Check cache first
    cached_recommendation = await redis_client.get_ai_recommendation(user_input)
    if cached_recommendation:
        ai_response = cached_recommendation
    else:
        ai_response = await groq_ai_client.get_music_recommendation_prompt(user_input)
        await redis_client.set_ai_recommendation(user_input, ai_response)

    search_query = ai_response.get("keywords", f"{song.title} {song.artist}")

    youtube_results = await youtube_client.search_video(search_query)

    if not youtube_results:
        await callback.message.answer("Üzgünüm, benzer müzik bulunamadı.", reply_markup=main_menu_keyboard())
        await state.clear()
        return

    await callback.message.answer(
        f"\"**{song.title}**\" şarkısına benzer öneriler:",
        reply_markup=search_results_keyboard(youtube_results)
    )
    await state.clear()
    await callback.answer()
