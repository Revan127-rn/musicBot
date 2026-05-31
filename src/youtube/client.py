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
                search_resp = await client.get(self.SEARCH_URL, params={
                    "part": "snippet",
                    "q": query,
                    "type": "video",
                    "videoCategoryId": "10",
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

                video_ids = [item["id"]["videoId"] for item in items]

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
        video_url = f"https://www.youtube.com/watch?v={youtube_id}"

        try:
            from pytubefix import YouTube
            from pytubefix.cli import on_progress
            import subprocess

            loop = asyncio.get_event_loop()

            def _download():
                yt = YouTube(video_url, on_progress_callback=on_progress, use_oauth=False, allow_oauth_cache=True)
                stream = yt.streams.filter(only_audio=True).order_by("abr").last()
                if not stream:
                    return None
                base = output_path.rsplit(".", 1)[0]
                downloaded = stream.download(
                    output_path=os.path.dirname(base),
                    filename=os.path.basename(base)
                )
                mp3_path = f"{base}.mp3"
                subprocess.run([
                    "ffmpeg", "-i", downloaded,
                    "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k",
                    mp3_path, "-y"
                ], check=True, capture_output=True)
                os.remove(downloaded)
                return mp3_path

            result = await loop.run_in_executor(None, _download)
            return result

        except Exception as e:
            logger.error(f"Audio yükləmə xətası '{youtube_id}': {e}")
            return None

    def _parse_duration(self, duration_str: str) -> Optional[int]:
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
