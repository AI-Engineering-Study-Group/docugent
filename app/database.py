"""Database configuration and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config.settings import settings
from app.models.base import Base


def _to_asyncpg_url(url: str) -> str:
    """Ensure SQLAlchemy uses the asyncpg driver for PostgreSQL URLs.

    SQLAlchemy's async engine requires an async driver. If the provided URL
    uses the default "postgresql://" (which maps to psycopg2), convert it to
    "postgresql+asyncpg://". This preserves the rest of the URL including any
    query parameters like sslmode.
    """
    if not url:
        return url
    # Normalize common postgres schemes to asyncpg
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    if url.startswith("postgres://"):
        # Some providers still use the deprecated postgres:// scheme
        return "postgresql+asyncpg://" + url[len("postgres://") :]
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql+asyncpg://" + url[len("postgresql+psycopg2://") :]
    return url


# Create async engine using asyncpg driver
engine = create_async_engine(
    _to_asyncpg_url(settings.database_url),
    echo=settings.debug,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """Create database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
