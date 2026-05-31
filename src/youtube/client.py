import asyncio
import os
from typing import Any, Dict, List, Optional

from loguru import logger
from yt_dlp import YoutubeDL

from src.config import settings


class YouTubeClient:
    def __init__(self):
        self.base_opts = {
            "noplaylist": True,
            "ignoreerrors": True,
            "no_warnings": True,
            "quiet": True,
            "verbose": False,
            "retries": 3,
            "no_check_certificate": True,
            "cachedir": settings.YTDLP_CACHE_DIR,
            "cookiefile": settings.YTDLP_COOKIES_FILE if settings.YTDLP_COOKIES_FILE else None,
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "web"],
                }
            },
        }

    def _get_search_opts(self) -> dict:
        opts = self.base_opts.copy()
        opts["format"] = "bestaudio/best"
        opts["outtmpl"] = "%(id)s.%(ext)s"
        return opts

    def _get_download_opts(self, output_path: str) -> dict:
        opts = self.base_opts.copy()
        opts["format"] = "bestaudio/best"
        opts["outtmpl"] = output_path
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            },
            {"key": "FFmpegMetadata"},
        ]
        return opts

    async def search_video(self, query: str) -> List[Dict[str, Any]]:
        logger.info(f"YouTube axtarışı: {query}")
        search_url = f"ytsearch10:{query}"
        try:
            opts = self._get_search_opts()
            loop = asyncio.get_event_loop()

            def _search():
                with YoutubeDL(opts) as ydl:
                    return ydl.extract_info(search_url, download=False)

            info_dict = await loop.run_in_executor(None, _search)

            if not info_dict or "entries" not in info_dict:
                logger.warning(f"Axtarış nəticəsi boşdur: {query}")
                return []

            results = []
            for entry in info_dict["entries"]:
                if not entry:
                    continue
                duration = entry.get("duration")
                if duration and duration < 3600:
                    results.append({
                        "id": entry.get("id"),
                        "title": entry.get("title", "Bilinmiyor"),
                        "artist": entry.get("artist") or entry.get("channel") or "Bilinmiyor",
                        "duration": duration,
                        "thumbnail": entry.get("thumbnail"),
                        "webpage_url": entry.get("webpage_url"),
                    })

            logger.info(f"Tapılan nəticə sayı: {len(results)}")
            return results

        except Exception as e:
            logger.error(f"YouTube axtarış xətası '{query}': {e}")
            return []

    async def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        logger.info(f"Video məlumatı alınır: {url}")
        try:
            opts = self._get_search_opts()
            loop = asyncio.get_event_loop()

            def _info():
                with YoutubeDL(opts) as ydl:
                    return ydl.extract_info(url, download=False)

            info_dict = await loop.run_in_executor(None, _info)

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
            logger.error(f"Video məlumatı xətası '{url}': {e}")
            return None

    async def download_audio(self, youtube_id: str, output_path: str) -> Optional[str]:
        logger.info(f"Audio yüklənir: {youtube_id}")
        video_url = f"https://www.youtube.com/watch?v={youtube_id}"
        try:
            opts = self._get_download_opts(output_path)
            loop = asyncio.get_event_loop()

            def _download():
                with YoutubeDL(opts) as ydl:
                    return ydl.extract_info(video_url, download=True)

            info_dict = await loop.run_in_executor(None, _download)

            if info_dict:
                base = output_path.rsplit(".", 1)[0]
                final_path = f"{base}.mp3"
                if os.path.exists(final_path):
                    return final_path
                for pp in info_dict.get("requested_downloads", []):
                    fp = pp.get("filepath", "")
                    if fp.endswith(".mp3"):
                        return fp
            return None
        except Exception as e:
            logger.error(f"Audio yükləmə xətası '{youtube_id}': {e}")
            return None


youtube_client = YouTubeClient()
