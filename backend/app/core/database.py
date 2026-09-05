import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

logger = logging.getLogger(__name__)


def _engine_kwargs(url: str) -> dict:
    """Return create_async_engine kwargs appropriate for the database URL.

    PostgreSQL (asyncpg) gets a real connection pool. SQLite test databases use
    a NullPool and reject PostgreSQL-only pool arguments (pool_size and
    max_overflow raise TypeError against SQLiteDialect_aiosqlite), so those
    arguments are only applied for PostgreSQL URLs.
    """
    kwargs: dict = {
        "echo": settings.DEBUG,
        "future": True,
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    if url.startswith("postgresql"):
        kwargs.update(pool_size=20, max_overflow=10)
    return kwargs


def build_engine(url: str | None = None, **overrides):
    """Build an async engine for ``url`` (default: settings.DATABASE_URL).

    ``overrides`` are merged last so callers (e.g. the test bootstrap) can
    override behavior without re-implementing dialect awareness.
    """
    url = url or settings.DATABASE_URL
    kwargs = {**_engine_kwargs(url), **overrides}
    return create_async_engine(url, **kwargs)


engine = build_engine()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
