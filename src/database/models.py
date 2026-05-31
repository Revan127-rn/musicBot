from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    playlists: Mapped[List["Playlist"]] = relationship(
        "Playlist", back_populates="user", cascade="all, delete-orphan"
    )
    liked_songs: Mapped[List["LikedSong"]] = relationship(
        "LikedSong", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    youtube_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    artist: Mapped[Optional[str]] = mapped_column(String(255))
    duration: Mapped[Optional[int]] = mapped_column(BigInteger)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text)
    file_path: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    playlists: Mapped[List["PlaylistSong"]] = relationship(
        "PlaylistSong", back_populates="song", cascade="all, delete-orphan"
    )
    liked_by: Mapped[List["LikedSong"]] = relationship(
        "LikedSong", back_populates="song", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Song(id={self.id}, title='{self.title}', youtube_id='{self.youtube_id}')>"


class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="playlists")
    playlist_songs: Mapped[List["PlaylistSong"]] = relationship(
        "PlaylistSong", back_populates="playlist", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Playlist(id={self.id}, name='{self.name}', user_id={self.user_id})>"


class PlaylistSong(Base):
    __tablename__ = "playlist_songs"

    playlist_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("playlists.id"), primary_key=True)
    song_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("songs.id"), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    playlist: Mapped["Playlist"] = relationship("Playlist", back_populates="playlist_songs")
    song: Mapped["Song"] = relationship("Song", back_populates="playlists")

    def __repr__(self) -> str:
        return f"<PlaylistSong(playlist_id={self.playlist_id}, song_id={self.song_id})>"


class LikedSong(Base):
    __tablename__ = "liked_songs"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), primary_key=True)
    song_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("songs.id"), primary_key=True)
    liked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="liked_songs")
    song: Mapped["Song"] = relationship("Song", back_populates="liked_by")

    def __repr__(self) -> str:
        return f"<LikedSong(user_id={self.user_id}, song_id={self.song_id})>"
