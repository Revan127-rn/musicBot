import os

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    BOT_TOKEN: str = Field(..., env="BOT_TOKEN")
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    REDIS_URL: str = Field(..., env="REDIS_URL")
    GROQ_API_KEY: str = Field(..., env="GROQ_API_KEY")
    ADMIN_TELEGRAM_IDS: list[int] = Field(default_factory=list, env="ADMIN_TELEGRAM_IDS")

    # yt-dlp settings
    YTDLP_CACHE_DIR: str = Field("./.ytdlp_cache", env="YTDLP_CACHE_DIR")
    YTDLP_COOKIES_FILE: str = Field("", env="YTDLP_COOKIES_FILE") # Path to cookies.txt if using

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
