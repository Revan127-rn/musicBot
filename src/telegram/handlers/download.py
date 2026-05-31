import os
import asyncio

from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.services.song_service import SongService
from src.database.models import Song
from src.youtube.client import youtube_client
from src.utils.ffmpeg_converter import convert_to_mp3_and_optimize, embed_thumbnail
from src.telegram.keyboards import main_menu_keyboard

router = Router()

DOWNLOAD_DIR = "./downloads"

@router.callback_query(F.data.startswith("download_song:"))
async def download_song_callback(callback: CallbackQuery, session: AsyncSession):
    song_db_id = int(callback.data.split(":")[1])
    song_service = SongService(session)

    song = await session.get(Song, song_db_id)
    if not song:
        await callback.message.answer("Şarkı bulunamadı.")
        await callback.answer()
        return

    await callback.message.answer(f"\"**{song.title}**\" şarkısı indiriliyor ve optimize ediliyor... Bu biraz zaman alabilir.")
    await callback.answer()

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    temp_audio_path = os.path.join(DOWNLOAD_DIR, f"{song.youtube_id}_temp.mp3")
    final_audio_path = os.path.join(DOWNLOAD_DIR, f"{song.youtube_id}.mp3")

    try:
        # Download audio using yt-dlp
        downloaded_file = await youtube_client.download_audio(song.youtube_id, temp_audio_path)

        if not downloaded_file:
            await callback.message.answer("Şarkı indirilemedi. Lütfen daha sonra tekrar deneyin.", reply_markup=main_menu_keyboard())
            return

        # Optimize audio with FFmpeg
        optimized_file = await convert_to_mp3_and_optimize(downloaded_file, final_audio_path)

        if not optimized_file:
            await callback.message.answer("Şarkı optimize edilemedi veya dosya boyutu çok büyük.", reply_markup=main_menu_keyboard())
            return

        # Embed thumbnail if available
        if song.thumbnail_url:
            thumbnail_path = os.path.join(DOWNLOAD_DIR, f"{song.youtube_id}.jpg")
            # Download thumbnail (simple http request)
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(song.thumbnail_url)
                if response.status_code == 200:
                    with open(thumbnail_path, "wb") as f:
                        f.write(response.content)
                    # Embed thumbnail into the optimized audio file
                    audio_with_thumbnail_path = os.path.join(DOWNLOAD_DIR, f"{song.youtube_id}_final.mp3")
                    embedded_file = await embed_thumbnail(optimized_file, thumbnail_path, audio_with_thumbnail_path)
                    if embedded_file:
                        optimized_file = embedded_file
                    else:
                        logger.warning(f"Could not embed thumbnail for {song.youtube_id}")
                else:
                    logger.warning(f"Could not download thumbnail for {song.youtube_id}: {response.status_code}")

        # Send audio to user
        audio_file = FSInputFile(optimized_file, filename=f"{song.title}.mp3")
        await callback.message.answer_audio(audio=audio_file, caption=f"🎵 **{song.title}** - {song.artist}")

        # Update song file_path in DB
        await song_service.update_song_file_path(song.id, optimized_file)

    except Exception as e:
        logger.error(f"Error during song download or processing for {song.youtube_id}: {e}")
        await callback.message.answer("Şarkı indirilirken veya işlenirken bir hata oluştu. Lütfen tekrar deneyin.", reply_markup=main_menu_keyboard())
    finally:
        # Clean up temporary files
        files_to_clean = [temp_audio_path, final_audio_path]
        if 'thumbnail_path' in locals() and thumbnail_path:
            files_to_clean.append(thumbnail_path)
        if 'audio_with_thumbnail_path' in locals() and audio_with_thumbnail_path:
            files_to_clean.append(audio_with_thumbnail_path)

        for f in files_to_clean:
            if f and os.path.exists(f):
                os.remove(f)
