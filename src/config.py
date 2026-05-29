import os
from typing import List, Union
from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    BOT_TOKEN: str = Field(..., env="BOT_TOKEN")
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    REDIS_URL: str = Field(..., env="REDIS_URL")
    GROQ_API_KEY: str = Field(..., env="GROQ_API_KEY")
    
    # Virgülle ayrılmış metni listeye çeviren validator eklendi
    ADMIN_TELEGRAM_IDS: List[int] = Field(default_factory=list, env="ADMIN_TELEGRAM_IDS")

    @field_validator("ADMIN_TELEGRAM_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Union[str, int, List[int]]) -> List[int]:
        if isinstance(v, str):
            # Eğer boş metinse boş liste dön
            if not v.strip():
                return []
            # Virgülle ayrılmışsa parçala ve int'e çevir
            return [int(x.strip()) for x in v.split(",")]
        elif isinstance(v, int):
            # Tek bir sayı gelirse listeye koy
            return [v]
        return v

    # yt-dlp settings
    YTDLP_CACHE_DIR: str = Field("./.ytdlp_cache", env="YTDLP_CACHE_DIR")
    YTDLP_COOKIES_FILE: str = Field("", env="YTDLP_COOKIES_FILE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
