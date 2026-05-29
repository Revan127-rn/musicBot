# src/database/database.py dosyasını tamamen bununla değiştirin:
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger
from src.database.models import Base

class Database:
    def __init__(self, db_url: str):
        # Neon.tech için SSL zorunluluğu eklendi
        self.engine = create_async_engine(db_url, echo=False, connect_args={
            "ssl": "require" if "neon.tech" in db_url else "prefer"
        })
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def init_db(self):
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Veritabanı tabloları başarıyla oluşturuldu/güncellendi.")
        except Exception as e:
            logger.error(f"Veritabanı tabloları oluşturulurken hata oluştu: {e}")
            raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.SessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

db: Database | None = None

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    if db is None:
        raise Exception("Database not initialized. Call init_db() first.")
    async for session in db.get_session():
        yield session
