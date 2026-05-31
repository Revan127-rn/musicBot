import asyncio
import os
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from src.config import settings


class YouTubeClient:

    SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
    VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

    async def search_video(self, query: str) -> List[Dict[str, Any]]:
        logger.info(f"YouTube API axtarışı: {query}")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Axtarış
                search_resp = await client.get(self.SEARCH_URL, params={
                    "part": "snippet",
                    "q": query,
                    "type": "video",
                    "videoCategoryId": "10",  # Music kateqoriyası
                    "maxResults": 10,
                    "key": settings.YOUTUBE_API_KEY,
                })
                search_data = search_resp.json()

                if "error" in search_data:
                    logger.error(f"YouTube API xətası: {search_data['error']}")
                    return []

                items = search_data.get("items", [])
                if not items:
                    return []

                # Video ID-lərini topla
                video_ids = [item["id"]["videoId"] for item in items]

                # Duration üçün videos endpoint-ə müraciət et
                videos_resp = await client.get(self.VIDEOS_URL, params={
                    "part": "contentDetails,snippet",
                    "id": ",".join(video_ids),
                    "key": settings.YOUTUBE_API_KEY,
                })
                videos_data = videos_resp.json()

                results = []
                for video in videos_data.get("items", []):
                    duration_sec = self._parse_duration(
                        video["contentDetails"]["duration"]
                    )
                    if duration_sec and duration_sec < 3600:
                        snippet = video["snippet"]
                        results.append({
                            "id": video["id"],
                            "title": snippet.get("title", "Bilinmiyor"),
                            "artist": snippet.get("channelTitle", "Bilinmiyor"),
                            "duration": duration_sec,
                            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                            "webpage_url": f"https://www.youtube.com/watch?v={video['id']}",
                        })

                logger.info(f"Tapılan nəticə sayı: {len(results)}")
                return results

        except Exception as e:
            logger.error(f"YouTube API axtarış xətası '{query}': {e}")
            return []

    async def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        logger.info(f"Video məlumatı alınır: {url}")
        try:
            video_id = url.split("v=")[-1].split("&")[0]
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(self.VIDEOS_URL, params={
                    "part": "contentDetails,snippet",
                    "id": video_id,
                    "key": settings.YOUTUBE_API_KEY,
                })
                data = resp.json()
                items = data.get("items", [])
                if not items:
                    return None

                video = items[0]
                duration_sec = self._parse_duration(video["contentDetails"]["duration"])
                snippet = video["snippet"]

                return {
                    "id": video["id"],
                    "title": snippet.get("title"),
                    "artist": snippet.get("channelTitle"),
                    "duration": duration_sec,
                    "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                    "webpage_url": url,
                }
        except Exception as e:
            logger.error(f"Video məlumatı xətası '{url}': {e}")
            return None

    async def download_audio(self, youtube_id: str, output_path: str) -> Optional[str]:
        logger.info(f"Audio yüklənir: {youtube_id}")
        logger.info(f"Cookies faylı: {settings.YTDLP_COOKIES_FILE}")
        import os
        logger.info(f"Cookies mövcuddur: {os.path.exists(settings.YTDLP_COOKIES_FILE) if settings.YTDLP_COOKIES_FILE else 'YOX'}")
        from yt_dlp import YoutubeDL
        video_url = f"https://www.youtube.com/watch?v={youtube_id}"
        opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "noplaylist": True,
            "quiet": True,
            "no_check_certificate": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                },
                {"key": "FFmpegMetadata"},
            ],
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "web"],
                }
            },
        }
        try:
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

    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """ISO 8601 duration-u saniyəyə çevir (PT4M13S → 253)"""
        import re
        if not duration_str:
            return None
        match = re.match(
            r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str
        )
        if not match:
            return None
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds


youtube_client = YouTubeClient()
