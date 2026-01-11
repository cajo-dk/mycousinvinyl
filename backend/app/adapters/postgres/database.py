"""
PostgreSQL database connection and session management.
"""

import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import get_settings

settings = get_settings()

# Convert postgres:// to postgresql+asyncpg://
database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
echo_env = os.getenv("SQLALCHEMY_ECHO", "").strip().lower()
sqlalchemy_level = os.getenv("SQLALCHEMY_LOG_LEVEL", "").strip().upper()
if echo_env in {"1", "true", "yes", "on"}:
    echo_setting = True
elif echo_env in {"0", "false", "no", "off"}:
    echo_setting = False
elif sqlalchemy_level and sqlalchemy_level != "DEBUG":
    echo_setting = False
else:
    echo_setting = (
        settings.environment == "development"
        and settings.log_level.upper() == "DEBUG"
    )

engine = create_async_engine(
    database_url,
    echo=echo_setting,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for SQLAlchemy models
Base = declarative_base()


async def get_session() -> AsyncSession:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        yield session
