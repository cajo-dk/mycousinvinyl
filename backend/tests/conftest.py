"""
Pytest configuration and shared fixtures.

This file provides fixtures for both unit and integration tests.
SQLAlchemy fixtures are only available when dependencies are installed.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator

# Try to import SQLAlchemy dependencies for integration tests
# If not available, integration test fixtures will be skipped
try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlalchemy.pool import NullPool
    from httpx import AsyncClient, ASGITransport
    from app.adapters.postgres.database import Base
    from app.adapters.postgres.unit_of_work import SqlAlchemyUnitOfWork
    from app.entrypoints.http.main import app
    from app.config import Settings
    INTEGRATION_DEPS_AVAILABLE = True
except ImportError:
    INTEGRATION_DEPS_AVAILABLE = False


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/mycousinvinyl_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Integration test fixtures (only available if dependencies are installed)
if INTEGRATION_DEPS_AVAILABLE:
    @pytest_asyncio.fixture(scope="function")
    async def test_db_engine():
        """Create a test database engine."""
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            poolclass=NullPool,
        )

        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        yield engine

        # Cleanup
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        await engine.dispose()


    @pytest_asyncio.fixture(scope="function")
    async def test_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
        """Create a test database session."""
        async_session = async_sessionmaker(
            test_db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with async_session() as session:
            yield session


    @pytest_asyncio.fixture(scope="function")
    async def uow(test_session: AsyncSession) -> SqlAlchemyUnitOfWork:
        """Create a Unit of Work for testing."""
        return SqlAlchemyUnitOfWork(test_session)


    @pytest_asyncio.fixture
    async def client() -> AsyncGenerator[AsyncClient, None]:
        """Create an async HTTP client for testing API endpoints."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


    @pytest.fixture
    def mock_settings(monkeypatch):
        """Mock settings for testing."""
        test_settings = Settings(
            database_url=TEST_DATABASE_URL,
            activemq_url="stomp://localhost:61613",
            azure_tenant_id="test-tenant-id",
            azure_client_id="test-client-id",
            azure_audience="api://test-client-id",
            azure_group_admin="admin-group-id",
            azure_group_editor="editor-group-id",
            azure_group_viewer="viewer-group-id",
            log_level="DEBUG"
        )

        monkeypatch.setattr("app.config.get_settings", lambda: test_settings)
        return test_settings


@pytest.fixture
def sample_artist_data():
    """Sample artist data for testing."""
    return {
        "name": "Test Artist",
        "sort_name": "Artist, Test",
        "artist_type": "Person",
        "country": "US",
        "bio": "A test artist biography"
    }


@pytest.fixture
def sample_album_data():
    """Sample album data for testing."""
    return {
        "title": "Test Album",
        "release_type": "Studio",
        "release_year": 2024,
        "label": "Test Records",
        "catalog_number": "TEST-001"
    }


@pytest.fixture
def sample_pressing_data():
    """Sample pressing data for testing."""
    return {
        "format": "LP",
        "speed_rpm": "33",
        "size_inches": "12",
        "disc_count": 1,
        "country": "US",
        "release_year": 2024
    }
