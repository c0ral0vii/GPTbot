from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from src.config.config import settings


BASE_URL = settings.get_database_link

engine = create_async_engine(
    url=BASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=50,
    max_overflow=100,
    pool_timeout=30,
    pool_recycle=3600,
)

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator:
    """Dependency for getting async session"""
    try:
        session: AsyncSession = async_session()
        yield session
    finally:
        await session.close()