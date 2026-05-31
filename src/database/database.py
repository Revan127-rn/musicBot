from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger
from src.database.models import Base

# Global veritabanı nesnesi
class Database:
    def __init__(self, db_url: str):
        # asyncpg yerine daha kararlı olan psycopg sürücüsünü zorla
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        
        self.engine = create_async_engine(db_url, echo=False)
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
            logger.info("Veritabanı tabloları hazır.")
        except Exception as e:
            logger.error(f"Veritabanı hatası: {e}")
            raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.SessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

# Bu değişkeni dışarıdan erişilebilir kılıyoruz
db: Database | None = None

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    global db
    if db is None:
        logger.error("Veritabanı henüz başlatılmamış!")
        return
    async for session in db.get_session():
        yield session
