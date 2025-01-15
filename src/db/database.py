from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from src.config.config import settings


BASE_URL = settings.get_database_link

engine = create_async_engine(
    url=BASE_URL,
    max_overflow=15,
)

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
