from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings

_db_url = str(settings.DATABASE_URL)

# SQLite (used in tests) doesn't support connection pooling.
# PostgreSQL gets a tuned pool for async web workloads.
_is_sqlite = _db_url.startswith("sqlite")

_engine_kwargs: dict = {
    "echo": False,
    "future": True,
}
if _is_sqlite:
    _engine_kwargs["poolclass"] = NullPool
else:
    # pool_size: persistent connections kept alive.
    # max_overflow: extra burst connections.
    # pool_pre_ping: validates connections before use (detects stale conns).
    _engine_kwargs["pool_size"] = 10
    _engine_kwargs["max_overflow"] = 20
    _engine_kwargs["pool_pre_ping"] = True
    _engine_kwargs["connect_args"] = {"timeout": settings.DB_CONNECT_TIMEOUT}

engine = create_async_engine(_db_url, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            yield session
