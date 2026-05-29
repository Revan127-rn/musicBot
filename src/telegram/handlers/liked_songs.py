from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.song_service import SongService
from src.telegram.keyboards import liked_songs_keyboard, liked_song_actions_keyboard, main_menu_keyboard

router = Router()


@router.callback_query(F.data == "my_liked_songs")
async def my_liked_songs_callback(callback: CallbackQuery, session: AsyncSession):
    song_service = SongService(session)
    liked_songs = await song_service.get_liked_songs(callback.from_user.id)

    if not liked_songs:
        await callback.message.edit_text("Henüz beğendiğiniz bir şarkı yok.", reply_markup=main_menu_keyboard())
    else:
        songs_data = [{
            "id": s.id,
            "title": s.title,
            "artist": s.artist,
            "youtube_id": s.youtube_id
        } for s in liked_songs]
        await callback.message.edit_text(
            "Beğendiğiniz şarkılar:",
            reply_markup=liked_songs_keyboard(songs_data)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("like_song:"))
async def like_song_callback(callback: CallbackQuery, session: AsyncSession):
    youtube_id = callback.data.split(":")[1]
    song_service = SongService(session)

    song = await song_service.get_song_by_youtube_id(youtube_id)
    if not song:
        await callback.message.answer("Şarkı bulunamadı.")
        await callback.answer()
        return

    if await song_service.like_song(callback.from_user.id, song.id):
        await callback.message.edit_reply_markup(reply_markup=liked_song_actions_keyboard(song.id))
        await callback.answer("Şarkı beğenilenlere eklendi!")
    else:
        await callback.answer("Şarkı zaten beğenilenlerde veya bir hata oluştu.")


@router.callback_query(F.data.startswith("unlike_song:"))
async def unlike_song_callback(callback: CallbackQuery, session: AsyncSession):
    song_id = int(callback.data.split(":")[1])
    song_service = SongService(session)

    if await song_service.unlike_song(callback.from_user.id, song_id):
        await callback.message.edit_text("Şarkı beğenilenlerden çıkarıldı.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.answer("Şarkı beğenilenlerde bulunamadı veya bir hata oluştu.")
    await callback.answer()


@router.callback_query(F.data.startswith("view_liked_song:"))
async def view_liked_song_callback(callback: CallbackQuery, session: AsyncSession):
    song_id = int(callback.data.split(":")[1])
    song_service = SongService(session)
    song = await song_service.session.get(Song, song_id)

    if not song:
        await callback.message.answer("Şarkı bulunamadı.")
        await callback.answer()
        return

    await callback.message.edit_text(
        f"**{song.title}** - {song.artist}\nSüre: {song.duration // 60:02d}:{song.duration % 60:02d}",
        reply_markup=liked_song_actions_keyboard(song.id)
    )
    await callback.answer()


@router.callback_query(F.data == "liked_songs")
async def back_to_liked_songs_callback(callback: CallbackQuery, session: AsyncSession):
    await my_liked_songs_callback(callback, session)
