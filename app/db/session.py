from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# engine with connection timeout and pool settings
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False,
    future=True,
    connect_args={"timeout": settings.DB_CONNECT_TIMEOUT},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
