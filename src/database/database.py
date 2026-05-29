from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import make_url
from loguru import logger
from src.database.models import Base

class Database:
    def __init__(self, db_url: str):
        # 1. URL'yi temizle ve düzenle
        url = make_url(db_url)
        
        # asyncpg için sürücüyü kontrol et
        if url.drivername == "postgresql":
            url = url.set(drivername="postgresql+asyncpg")
        
        # Neon/asyncpg ile çakışan 'sslmode' parametresini URL'den kaldır
        query = dict(url.query)
        if "sslmode" in query:
            del query["sslmode"]
        url = url.set(query=query)
        
        # 2. SSL ayarlarını güvenli şekilde yap
        connect_args = {}
        if "neon.tech" in str(url):
            connect_args["ssl"] = "require"
            
        self.engine = create_async_engine(
            url, 
            echo=False, 
            connect_args=connect_args
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
                # Tabloları oluştur/güncelle
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Veritabanı bağlantısı başarılı ve tablolar hazır.")
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
