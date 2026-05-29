from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def search_results_keyboard(results: list[dict], current_page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, song in enumerate(results):
        # Tırnak işaretleri düzeltildi: f"{song['title']}"
        builder.button(text=f"{song['title']} - {song['artist']}", callback_data=f"select_song:{song['id']}")
    builder.adjust(1)

    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Önceki", callback_data=f"search_page:{current_page - 1}"))
    if len(results) == 10: # Sayfa başına 10 sonuç varsayımı
        nav_buttons.append(InlineKeyboardButton(text="Sonraki ➡️", callback_data=f"search_page:{current_page + 1}"))
    if nav_buttons:
        builder.row(*nav_buttons)

    return builder.as_markup()


def song_actions_keyboard(song_db_id: int, youtube_id: str, is_liked: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬇️ İndir", callback_data=f"download_song:{song_db_id}")
    builder.button(text="➕ Playlist'e Ekle", callback_data=f"add_to_playlist_select:{youtube_id}")
    if is_liked:
        builder.button(text="❤️ Beğenmekten Vazgeç", callback_data=f"unlike_song:{song_db_id}")
    else:
        builder.button(text="🤍 Beğen", callback_data=f"like_song:{song_db_id}")
    builder.button(text="🎶 Benzer Öneriler", callback_data=f"ai_recommend_similar:{youtube_id}")
    builder.button(text="↩️ Tekrar Ara", callback_data="search_again")
    builder.adjust(2)
    return builder.as_markup()


def playlist_selection_keyboard(playlists: list[dict], song_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for playlist in playlists:
        builder.button(text=playlist['name'], callback_data=f"add_to_playlist:{playlist['id']}:{song_id}")
    builder.button(text="➕ Yeni Playlist Oluştur", callback_data=f"create_new_playlist:{song_id}")
    builder.button(text="⬅️ Geri", callback_data=f"back_to_song_actions:{song_id}")
    builder.adjust(1)
    return builder.as_markup()


def user_playlists_keyboard(playlists: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for playlist in playlists:
        builder.button(text=playlist['name'], callback_data=f"view_playlist:{playlist['id']}")
    builder.button(text="➕ Yeni Playlist Oluştur", callback_data="create_new_playlist_main")
    builder.adjust(1)
    return builder.as_markup()


def playlist_songs_keyboard(playlist_id: int, songs: list[dict], current_page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, song in enumerate(songs):
        builder.button(text=f"{song['title']} - {song['artist']}", callback_data=f"view_playlist_song:{playlist_id}:{song['id']}")
    builder.adjust(1)

    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Önceki", callback_data=f"playlist_page:{playlist_id}:{current_page - 1}"))
    if len(songs) == 10:
        nav_buttons.append(InlineKeyboardButton(text="Sonraki ➡️", callback_data=f"playlist_page:{playlist_id}:{current_page + 1}"))
    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="🗑️ Playlisti Sil", callback_data=f"delete_playlist_confirm:{playlist_id}"))
    builder.row(InlineKeyboardButton(text="⬅️ Geri", callback_data="back_to_playlists"))
    return builder.as_markup()


def playlist_song_actions_keyboard(playlist_id: int, song_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬇️ İndir", callback_data=f"download_song:{song_id}")
    builder.button(text="❌ Playlistten Çıkar", callback_data=f"remove_from_playlist:{playlist_id}:{song_id}")
    builder.button(text="⬅️ Geri", callback_data=f"view_playlist:{playlist_id}")
    builder.adjust(1)
    return builder.as_markup()


def confirm_delete_playlist_keyboard(playlist_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Evet, Sil", callback_data=f"delete_playlist:{playlist_id}")
    builder.button(text="❌ Hayır, İptal", callback_data=f"view_playlist:{playlist_id}")
    return builder.as_markup()


def liked_songs_keyboard(songs: list[dict], current_page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, song in enumerate(songs):
        builder.button(text=f"{song['title']} - {song['artist']}", callback_data=f"view_liked_song:{song['id']}")
    builder.adjust(1)

    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Önceki", callback_data=f"liked_page:{current_page - 1}"))
    if len(songs) == 10:
        nav_buttons.append(InlineKeyboardButton(text="Sonraki ➡️", callback_data=f"liked_page:{current_page + 1}"))
    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="⬅️ Geri", callback_data="start"))
    return builder.as_markup()


def liked_song_actions_keyboard(song_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬇️ İndir", callback_data=f"download_song:{song_id}")
    builder.button(text="❤️ Beğenmekten Vazgeç", callback_data=f"unlike_song:{song_id}")
    builder.button(text="⬅️ Geri", callback_data="liked_songs")
    builder.adjust(1)
    return builder.as_markup()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎵 Müzik Ara", callback_data="search_music")
    builder.button(text="▶️ Playlistlerim", callback_data="my_playlists")
    builder.button(text="❤️ Beğenilen Şarkılar", callback_data="my_liked_songs")
    builder.button(text="✨ AI Önerileri", callback_data="ai_recommendations")
    builder.adjust(2)
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ İptal", callback_data="cancel")
    return builder.as_markup()


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Bot İstatistikleri", callback_data="bot_stats")
    builder.button(text="📣 Duyuru Yap", callback_data="broadcast_message")
    builder.button(text="⬅️ Ana Menü", callback_data="start")
    builder.adjust(1)
    return builder.as_markup()
