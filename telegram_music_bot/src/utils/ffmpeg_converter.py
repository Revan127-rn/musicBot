import asyncio
import os
from typing import Optional

import ffmpeg
from loguru import logger


async def convert_to_mp3_and_optimize(
    input_path: str, output_path: str, bitrate: str = "128k", max_size_mb: int = 50
) -> Optional[str]:
    logger.info(f"Converting {input_path} to MP3 and optimizing to {output_path}")
    try:
        # First pass: convert to MP3 with specified bitrate
        probe = await asyncio.to_thread(ffmpeg.probe, input_path)
        audio_stream = next((stream for stream in probe["streams"] if stream["codec_type"] == "audio"), None)
        if not audio_stream:
            logger.error(f"No audio stream found in {input_path}")
            return None

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        (ffmpeg.input(input_path)
            .output(output_path, acodec="libmp3lame", audio_bitrate=bitrate, map_metadata=0)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True))

        # Check file size and re-encode if necessary to meet Telegram's 50MB limit
        current_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        if current_size_mb > max_size_mb:
            logger.warning(
                f"Optimized MP3 file size ({current_size_mb:.2f}MB) exceeds {max_size_mb}MB. Re-encoding with lower bitrate."
            )
            # Calculate new bitrate to fit within max_size_mb
            # Assuming original duration is available from probe
            duration = float(probe["format"]["duration"])
            if duration == 0:
                logger.error("Could not determine audio duration for size optimization.")
                return None

            # Target bitrate in bits/s
            target_bitrate_bps = (max_size_mb * 1024 * 1024 * 8) / duration
            # Convert to kbit/s and ensure it's not too low
            new_bitrate_kbps = max(64, int(target_bitrate_bps / 1000) - 32) # -32 for overhead
            new_bitrate = f"{new_bitrate_kbps}k"

            logger.info(f"Re-encoding with new bitrate: {new_bitrate}")
            temp_output_path = output_path + ".tmp.mp3"
            (ffmpeg.input(input_path)
                .output(temp_output_path, acodec="libmp3lame", audio_bitrate=new_bitrate, map_metadata=0)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True))

            if os.path.exists(temp_output_path):
                os.replace(temp_output_path, output_path)
                final_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                logger.info(f"Final optimized MP3 size: {final_size_mb:.2f}MB")
                if final_size_mb > max_size_mb:
                    logger.warning(f"File still exceeds {max_size_mb}MB after re-encoding. ({final_size_mb:.2f}MB)")
                    return None # Still too large, return None
            else:
                logger.error("Re-encoding failed, temporary file not found.")
                return None

        return output_path
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error during conversion: {e.stderr.decode()}")
        return None
    except Exception as e:
        logger.error(f"Error during audio conversion: {e}")
        return None


async def embed_thumbnail(audio_path: str, thumbnail_path: str, output_path: str) -> Optional[str]:
    logger.info(f"Embedding thumbnail {thumbnail_path} into {audio_path} to {output_path}")
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        (ffmpeg.input(audio_path)
            .input(thumbnail_path)
            .output(output_path, map_metadata=0, codec_copy="copy", map="0", map="1", id3v2_version="3")
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True))
        return output_path
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error during thumbnail embedding: {e.stderr.decode()}")
        return None
    except Exception as e:
        logger.error(f"Error during thumbnail embedding: {e}")
        return None
