from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database.models import Playlist, PlaylistSong, Song, User


class PlaylistService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_playlist(self, user_id: int, name: str) -> Playlist:
        playlist = Playlist(user_id=user_id, name=name)
        self.session.add(playlist)
        await self.session.commit()
        await self.session.refresh(playlist)
        return playlist

    async def get_playlist_by_id(self, playlist_id: int) -> Optional[Playlist]:
        result = await self.session.execute(
            select(Playlist).where(Playlist.id == playlist_id).options(joinedload(Playlist.playlist_songs).joinedload(PlaylistSong.song))
        )
        return result.scalar_one_or_none()

    async def get_user_playlists(self, user_id: int) -> List[Playlist]:
        result = await self.session.execute(
            select(Playlist).where(Playlist.user_id == user_id)
        )
        return result.scalars().all()

    async def add_song_to_playlist(self, playlist_id: int, song_id: int) -> bool:
        playlist_song = PlaylistSong(playlist_id=playlist_id, song_id=song_id)
        self.session.add(playlist_song)
        try:
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            return False

    async def remove_song_from_playlist(self, playlist_id: int, song_id: int) -> bool:
        result = await self.session.execute(
            select(PlaylistSong).where(
                PlaylistSong.playlist_id == playlist_id, PlaylistSong.song_id == song_id
            )
        )
        playlist_song = result.scalar_one_or_none()
        if playlist_song:
            await self.session.delete(playlist_song)
            await self.session.commit()
            return True
        return False

    async def delete_playlist(self, playlist_id: int) -> bool:
        playlist = await self.session.get(Playlist, playlist_id)
        if playlist:
            await self.session.delete(playlist)
            await self.session.commit()
            return True
        return False
