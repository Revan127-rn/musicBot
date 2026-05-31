from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.playlist_service import PlaylistService
from src.services.song_service import SongService
from src.telegram.keyboards import (
    cancel_keyboard,
    confirm_delete_playlist_keyboard,
    main_menu_keyboard,
    playlist_selection_keyboard,
    playlist_song_actions_keyboard,
    playlist_songs_keyboard,
    user_playlists_keyboard,
)

router = Router()


class PlaylistStates(StatesGroup):
    waiting_for_playlist_name = State()
    waiting_for_song_to_add = State()


@router.callback_query(F.data == "my_playlists")
async def my_playlists_callback(callback: CallbackQuery, session: AsyncSession):
    playlist_service = PlaylistService(session)
    user_playlists = await playlist_service.get_user_playlists(callback.from_user.id)

    if not user_playlists:
        await callback.message.edit_text(
            "Henüz bir çalma listeniz yok. Yeni bir tane oluşturmak ister misiniz?",
            reply_markup=user_playlists_keyboard([])
        )
    else:
        playlists_data = [{
            "id": p.id,
            "name": p.name
        } for p in user_playlists]
        await callback.message.edit_text(
            "Çalma listeleriniz:",
            reply_markup=user_playlists_keyboard(playlists_data)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("create_new_playlist"))
async def create_new_playlist_callback(callback: CallbackQuery, state: FSMContext):
    song_id = None
    if len(callback.data.split(":")) > 1:
        song_id = callback.data.split(":")[1]
    await state.update_data(song_id_to_add_after_creation=song_id)

    await callback.message.edit_text("Lütfen yeni çalma listenizin adını girin:", reply_markup=cancel_keyboard())
    await state.set_state(PlaylistStates.waiting_for_playlist_name)
    await callback.answer()


@router.message(PlaylistStates.waiting_for_playlist_name)
async def process_new_playlist_name(message: Message, state: FSMContext, session: AsyncSession):
    playlist_name = message.text
    if not playlist_name:
        await message.answer("Geçersiz isim. Lütfen tekrar deneyin.")
        return

    playlist_service = PlaylistService(session)
    new_playlist = await playlist_service.create_playlist(message.from_user.id, playlist_name)

    state_data = await state.get_data()
    song_id_to_add = state_data.get("song_id_to_add_after_creation")

    if song_id_to_add:
        song_service = SongService(session)
        song = await song_service.get_song_by_youtube_id(song_id_to_add)
        if song:
            await playlist_service.add_song_to_playlist(new_playlist.id, song.id)
            await message.answer(
                f"'{song.title}' şarkısı '{new_playlist.name}' çalma listesine eklendi!",
                reply_markup=main_menu_keyboard()
            )
        else:
            await message.answer(
                f"'{new_playlist.name}' çalma listesi oluşturuldu, ancak şarkı bulunamadı.",
                reply_markup=main_menu_keyboard()
            )
    else:
        await message.answer(
            f"'{new_playlist.name}' adında yeni bir çalma listesi oluşturuldu!",
            reply_markup=main_menu_keyboard()
        )

    await state.clear()


@router.callback_query(F.data.startswith("add_to_playlist_select:"))
async def add_to_playlist_select_callback(callback: CallbackQuery, session: AsyncSession):
    song_youtube_id = callback.data.split(":")[1]
    playlist_service = PlaylistService(session)
    user_playlists = await playlist_service.get_user_playlists(callback.from_user.id)

    if not user_playlists:
        await callback.message.edit_text(
            "Henüz bir çalma listeniz yok. Yeni bir tane oluşturmak ister misiniz?",
            reply_markup=playlist_selection_keyboard([], song_youtube_id)
        )
    else:
        playlists_data = [{
            "id": p.id,
            "name": p.name
        } for p in user_playlists]
        await callback.message.edit_text(
            f"'{song_youtube_id}' şarkısını hangi çalma listesine eklemek istersiniz?",
            reply_markup=playlist_selection_keyboard(playlists_data, song_youtube_id)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("add_to_playlist:"))
async def add_to_playlist_callback(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":")
    playlist_id = int(parts[1])
    song_youtube_id = parts[2]

    playlist_service = PlaylistService(session)
    song_service = SongService(session)

    song = await song_service.get_song_by_youtube_id(song_youtube_id)
    if not song:
        await callback.message.answer("Şarkı bulunamadı.")
        await callback.answer()
        return

    if await playlist_service.add_song_to_playlist(playlist_id, song.id):
        playlist = await playlist_service.get_playlist_by_id(playlist_id)
        await callback.message.edit_text(
            f"'{song.title}' şarkısı '{playlist.name}' çalma listesine eklendi!",
            reply_markup=main_menu_keyboard()
        )
    else:
        await callback.message.answer("Şarkı zaten bu çalma listesinde veya bir hata oluştu.")
    await callback.answer()


@router.callback_query(F.data.startswith("view_playlist:"))
async def view_playlist_callback(callback: CallbackQuery, session: AsyncSession):
    playlist_id = int(callback.data.split(":")[1])
    playlist_service = PlaylistService(session)
    playlist = await playlist_service.get_playlist_by_id(playlist_id)

    if not playlist:
        await callback.message.edit_text("Çalma listesi bulunamadı.", reply_markup=main_menu_keyboard())
        await callback.answer()
        return

    songs_data = [{
        "id": ps.song.id,
        "title": ps.song.title,
        "artist": ps.song.artist,
        "youtube_id": ps.song.youtube_id
    } for ps in playlist.playlist_songs]

    await callback.message.edit_text(
        f"**{playlist.name}** çalma listesi:\n" +
        (f"Şarkı sayısı: {len(songs_data)}" if songs_data else "Henüz şarkı yok."),
        reply_markup=playlist_songs_keyboard(playlist_id, songs_data)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("view_playlist_song:"))
async def view_playlist_song_callback(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":")
    playlist_id = int(parts[1])
    song_id = int(parts[2])

    song_service = SongService(session)
    song = await song_service.session.get(Song, song_id)

    if not song:
        await callback.message.answer("Şarkı bulunamadı.")
        await callback.answer()
        return

    await callback.message.edit_text(
        f"**{song.title}** - {song.artist}\nSüre: {song.duration // 60:02d}:{song.duration % 60:02d}",
        reply_markup=playlist_song_actions_keyboard(playlist_id, song.id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("remove_from_playlist:"))
async def remove_from_playlist_callback(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":")
    playlist_id = int(parts[1])
    song_id = int(parts[2])

    playlist_service = PlaylistService(session)
    if await playlist_service.remove_song_from_playlist(playlist_id, song_id):
        await callback.message.answer("Şarkı çalma listesinden çıkarıldı.")
        # Refresh playlist view
        await view_playlist_callback(callback, session) # Re-use view_playlist_callback
    else:
        await callback.message.answer("Şarkı çalma listesinde bulunamadı veya bir hata oluştu.")
    await callback.answer()


@router.callback_query(F.data.startswith("delete_playlist_confirm:"))
async def delete_playlist_confirm_callback(callback: CallbackQuery):
    playlist_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "Bu çalma listesini silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.",
        reply_markup=confirm_delete_playlist_keyboard(playlist_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_playlist:"))
async def delete_playlist_callback(callback: CallbackQuery, session: AsyncSession):
    playlist_id = int(callback.data.split(":")[1])
    playlist_service = PlaylistService(session)

    if await playlist_service.delete_playlist(playlist_id):
        await callback.message.edit_text("Çalma listesi başarıyla silindi.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text("Çalma listesi silinirken bir hata oluştu.", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "back_to_playlists")
async def back_to_playlists_callback(callback: CallbackQuery, session: AsyncSession):
    await my_playlists_callback(callback, session)


@router.callback_query(F.data.startswith("back_to_song_actions:"))
async def back_to_song_actions_callback(callback: CallbackQuery, session: AsyncSession):
    song_youtube_id = callback.data.split(":")[1]
    song_service = SongService(session)
    song = await song_service.get_song_by_youtube_id(song_youtube_id)

    if not song:
        await callback.message.answer("Şarkı bulunamadı.")
        await callback.answer()
        return

    is_liked = await song_service.is_song_liked(callback.from_user.id, song.id)

    await callback.message.edit_text(
        f"**{song.title}** - {song.artist}\nSüre: {song.duration // 60:02d}:{song.duration % 60:02d}",
        reply_markup=song_actions_keyboard(song.youtube_id, is_liked=is_liked)
    )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_action_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("İşlem iptal edildi.", reply_markup=main_menu_keyboard())
    await callback.answer()
