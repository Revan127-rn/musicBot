from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import make_url
from loguru import logger
from src.database.models import Base

class Database:
    def __init__(self, db_url: str):
        # 1. URL'yi düzenle (psycopg sürücüsünü kullanıyoruz)
        url = make_url(db_url)
        
        # Dialect'i postgresql+psycopg olarak ayarla
        if "psycopg" not in url.drivername:
            url = url.set(drivername="postgresql+psycopg")
        
        # 2. Neon için SSL ayarlarını doğrudan URL parametresi olarak bırakabiliriz
        # psycopg, URL içindeki sslmode=require parametresini mükemmel anlar.
        
        self.engine = create_async_engine(
            url, 
            echo=False,
            # Bağlantı havuzu ayarları (Neon için optimize edildi)
            pool_pre_ping=True,
            pool_recycle=300
        )
        
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
            logger.info("Veritabanı bağlantısı (psycopg) başarılı.")
        except Exception as e:
            logger.error(f"Veritabanı başlatma hatası: {e}")
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
        raise Exception("Database initialized değil!")
    async for session in db.get_session():
        yield session
