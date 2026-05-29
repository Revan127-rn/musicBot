import os
import asyncio
import ffmpeg
from loguru import logger

async def convert_to_mp3_and_optimize(input_path: str, output_path: str) -> str:
    """
    Sesi MP3 formatına dönüştürür ve Telegram limitleri için optimize eder.
    """
    try:
        # Asenkron çalıştırmak için sarmalıyoruz
        process = await asyncio.create_subprocess_exec(
            'ffmpeg', '-y', '-i', input_path,
            '-codec:a', 'libmp3lame',
            '-qscale:a', '4',  # İyi kalite, düşük boyut
            '-ar', '44100',
            output_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"FFmpeg dönüştürme hatası: {stderr.decode()}")
            return None
            
        return output_path
    except Exception as e:
        logger.error(f"Dönüştürme sırasında hata: {e}")
        return None

async def embed_thumbnail(audio_path: str, thumbnail_path: str, output_path: str) -> str:
    """
    MP3 dosyasına kapak fotoğrafı (thumbnail) ekler.
    """
    try:
        # Tekrar eden 'map' argümanı hatasını düzeltmek için 
        # komutu liste olarak oluşturup subprocess ile çalıştırıyoruz
        process = await asyncio.create_subprocess_exec(
            'ffmpeg', '-y',
            '-i', audio_path,
            '-i', thumbnail_path,
            '-map', '0:0',
            '-map', '1:0',
            '-c', 'copy',
            '-id3v2_version', '3',
            '-metadata:s:v', 'title="Album cover"',
            '-metadata:s:v', 'comment="Cover (front)"',
            output_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"Thumbnail gömme hatası: {stderr.decode()}")
            # Hata olsa bile orijinal dosyayı döndürelim ki bot çalışmaya devam etsin
            return audio_path
            
        return output_path
    except Exception as e:
        logger.error(f"Thumbnail gömme sırasında hata: {e}")
        return audio_path
