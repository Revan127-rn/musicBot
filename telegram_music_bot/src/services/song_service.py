from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database.models import LikedSong, Song, User


class SongService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_song(
        self, youtube_id: str, title: str, artist: Optional[str], duration: Optional[int], thumbnail_url: Optional[str]
    ) -> Song:
        result = await self.session.execute(select(Song).where(Song.youtube_id == youtube_id))
        song = result.scalar_one_or_none()

        if not song:
            song = Song(
                youtube_id=youtube_id,
                title=title,
                artist=artist,
                duration=duration,
                thumbnail_url=thumbnail_url,
            )
            self.session.add(song)
            await self.session.commit()
            await self.session.refresh(song)
        return song

    async def get_song_by_youtube_id(self, youtube_id: str) -> Optional[Song]:
        result = await self.session.execute(select(Song).where(Song.youtube_id == youtube_id))
        return result.scalar_one_or_none()

    async def update_song_file_path(self, song_id: int, file_path: str) -> Optional[Song]:
        song = await self.session.get(Song, song_id)
        if song:
            song.file_path = file_path
            await self.session.commit()
            await self.session.refresh(song)
        return song

    async def like_song(self, user_id: int, song_id: int) -> bool:
        liked_song = LikedSong(user_id=user_id, song_id=song_id)
        self.session.add(liked_song)
        try:
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            return False

    async def unlike_song(self, user_id: int, song_id: int) -> bool:
        result = await self.session.execute(
            select(LikedSong).where(LikedSong.user_id == user_id, LikedSong.song_id == song_id)
        )
        liked_song = result.scalar_one_or_none()
        if liked_song:
            await self.session.delete(liked_song)
            await self.session.commit()
            return True
        return False

    async def get_liked_songs(self, user_id: int) -> List[Song]:
        result = await self.session.execute(
            select(Song)
            .join(LikedSong)
            .where(LikedSong.user_id == user_id)
            .options(joinedload(Song.liked_by))
        )
        return result.scalars().all()

    async def is_song_liked(self, user_id: int, song_id: int) -> bool:
        result = await self.session.execute(
            select(LikedSong).where(LikedSong.user_id == user_id, LikedSong.song_id == song_id)
        )
        return result.scalar_one_or_none() is not None
