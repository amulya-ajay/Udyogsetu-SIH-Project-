import logging
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

logger = logging.getLogger(__name__)

# asyncpg's ``ssl`` parameter accepts the same values libpq uses for
# ``sslmode`` (disable/allow/prefer/require/verify-ca/verify-full), but the
# URL key must be ``ssl`` -- asyncpg raises
# ``TypeError: connect() got an unexpected keyword argument 'sslmode'`` when
# the libpq-style ``sslmode=require`` query parameter is forwarded to it.
_SSLMODE_VALUES = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}


def normalize_database_url(url: str | None) -> str:
    """Make a PostgreSQL ``DATABASE_URL`` usable by SQLAlchemy asyncpg.

    Handles two common hosted-lite incompatibilities:

    * Driver-less URLs: Railway/Neon inject ``postgresql://`` (no driver).
      Without a driver SQLAlchemy's async engine falls back to the
      synchronous psycopg2 dialect, which is not installed, crashing startup.
      The scheme is rewritten to ``postgresql+asyncpg://``.

    * ``sslmode`` query parameters: Neon URLs ship ``?sslmode=require``.
      asyncpg does not accept ``sslmode`` as a ``connect()`` keyword, so the
      parameter is renamed to ``ssl`` (the asyncpg-native key that accepts the
      same values). All other query parameters (``application_name``,
      ``connect_timeout``, ``options``, ...) are preserved as-is, and an
      explicit ``ssl`` parameter wins over ``sslmode``.

    Non-PostgreSQL URLs (e.g. SQLite tests) are returned unchanged.
    """
    if not url:
        return url or ""
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ("postgres", "postgresql", "postgresql+asyncpg"):
        return url

    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    has_explicit_ssl = any(key.lower() == "ssl" for key, _ in pairs)
    normalized = []
    for key, value in pairs:
        if key.lower() == "sslmode":
            if not value or has_explicit_ssl or value.lower() not in _SSLMODE_VALUES:
                continue
            key = "ssl"
        normalized.append((key, value))

    return urlunparse(
        parsed._replace(
            scheme="postgresql+asyncpg",
            query=urlencode(normalized),
        )
    )


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
    return create_async_engine(normalize_database_url(url), **kwargs)


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
