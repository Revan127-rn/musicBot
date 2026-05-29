import asyncio
import os
import re
from typing import Any, Dict, List, Optional

from loguru import logger
from yt_dlp import YoutubeDL

from src.config import settings


class YouTubeClient:
    def __init__(self):
        self.ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": "%(id)s.%(ext)s",
            "cachedir": settings.YTDLP_CACHE_DIR,
            "cookiefile": settings.YTDLP_COOKIES_FILE if settings.YTDLP_COOKIES_FILE else None,
            "noplaylist": True,
            "ignoreerrors": True,
            "no_warnings": True,
            "quiet": True,
            "verbose": False,
            "throttledratelimit": 102400,  # 100KB/s to avoid aggressive rate limiting
            "retries": 5,
            "extractor_args": {
                "youtube": {
                    "player_client": ["web_safari"],  # Use web_safari for potentially fewer PO Token issues
                    "skip": ["dash_manifest", "hls_playlist"], # Skip these to avoid some detection
                }
            },
        }

    async def search_video(self, query: str) -> List[Dict[str, Any]]:
        logger.info(f"Searching YouTube for: {query}")
        search_url = f"ytsearch10:{query}"
        try:
            with YoutubeDL(self.ydl_opts) as ydl:
                loop = asyncio.get_event_loop()
                info_dict = await loop.run_in_executor(None, lambda: ydl.extract_info(search_url, download=False))

                if info_dict and "entries" in info_dict:
                    results = []
                    for entry in info_dict["entries"]:
                        if entry and entry.get("duration") and entry.get("duration") < 3600:  # Max 1 hour
                            results.append({
                                "id": entry.get("id"),
                                "title": entry.get("title"),
                                "artist": entry.get("artist") or entry.get("channel"),
                                "duration": entry.get("duration"),
                                "thumbnail": entry.get("thumbnail"),
                                "webpage_url": entry.get("webpage_url"),
                            })
                    return results
                return []
        except Exception as e:
            logger.error(f"YouTube search failed for \'{query}\': {e}")
            return []

    async def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        logger.info(f"Getting YouTube video info for: {url}")
        try:
            with YoutubeDL(self.ydl_opts) as ydl:
                loop = asyncio.get_event_loop()
                info_dict = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))

                if info_dict and info_dict.get("duration") and info_dict.get("duration") < 3600:
                    return {
                        "id": info_dict.get("id"),
                        "title": info_dict.get("title"),
                        "artist": info_dict.get("artist") or info_dict.get("channel"),
                        "duration": info_dict.get("duration"),
                        "thumbnail": info_dict.get("thumbnail"),
                        "webpage_url": info_dict.get("webpage_url"),
                    }
                return None
        except Exception as e:
            logger.error(f"YouTube info retrieval failed for \'{url}\': {e}")
            return None

    async def download_audio(self, youtube_id: str, output_path: str) -> Optional[str]:
        logger.info(f"Downloading audio for YouTube ID: {youtube_id} to {output_path}")
        video_url = f"https://www.youtube.com/watch?v={youtube_id}"
        download_opts = self.ydl_opts.copy()
        download_opts["outtmpl"] = output_path  # Full path including filename and extension
        download_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            },
            {"key": "FFmpegMetadata"},  # Embed metadata
        ]

        try:
            with YoutubeDL(download_opts) as ydl:
                loop = asyncio.get_event_loop()
                info_dict = await loop.run_in_executor(None, lambda: ydl.extract_info(video_url, download=True))
                if info_dict:
                    # yt-dlp might add .mp3 if not explicitly given in outtmpl
                    final_path = f"{output_path.rsplit('.', 1)[0]}.mp3"
                    if os.path.exists(final_path):
                        return final_path
                    # Fallback for when yt-dlp adds extension itself
                    for pp in info_dict.get("requested_downloads", []):
                        if pp.get("filepath") and pp["filepath"].endswith(".mp3"):
                            return pp["filepath"]
                    # If the above fails, try to guess based on the output path template
                    guessed_path = f"{output_path.rsplit('.', 1)[0]}.mp3"
                    if os.path.exists(guessed_path):
                        return guessed_path
                return None
        except Exception as e:
            logger.error(f"YouTube audio download failed for \'{youtube_id}\': {e}")
            return None


youtube_client = YouTubeClient()
