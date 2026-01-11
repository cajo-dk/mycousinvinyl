"""
Dependency injection for FastAPI endpoints.

Provides service instances with proper database session management.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import get_settings
from app.adapters.postgres.unit_of_work import SqlAlchemyUnitOfWork
from app.adapters.postgres.discogs_cache_repository_adapter import PostgresDiscogsCacheRepository
from app.application.services.artist_service import ArtistService
from app.application.services.album_service import AlbumService
from app.application.services.track_service import TrackService
from app.application.services.pressing_service import PressingService
from app.application.services.collection_service import CollectionService
from app.application.services.lookup_service import LookupService
from app.application.services.preferences_service import PreferencesService
from app.application.services.discogs_service import DiscogsService
from app.application.services.collection_sharing_service import CollectionSharingService
from app.application.services.collection_import_service import CollectionImportService
from app.application.services.album_wizard_service import AlbumWizardService
from app.application.services.discogs_oauth_service import DiscogsOAuthService
from app.application.services.discogs_pat_service import DiscogsPatService
from app.application.services.discogs_collection_sync_service import DiscogsCollectionSyncService
from app.application.services.system_log_service import SystemLogService
from app.adapters.http.discogs_client import DiscogsClientAdapter
from app.adapters.http.discogs_oauth_client import DiscogsOAuthClientAdapter
from app.adapters.http.album_wizard_client import AlbumWizardClientAdapter


# Database engine and session factory (module-level singletons)
settings = get_settings()

# Convert postgresql:// to postgresql+asyncpg:// for async driver
database_url = settings.database_url
if database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

engine = create_async_engine(
    database_url,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using
    pool_size=20,
    max_overflow=10
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides database session for dependency injection.

    Automatically commits on success, rolls back on exception.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================================================
# SERVICE DEPENDENCIES
# ============================================================================

async def get_artist_service() -> ArtistService:
    """Provides ArtistService with UnitOfWork."""
    async with async_session_factory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        yield ArtistService(uow)


async def get_album_service() -> AlbumService:
    """Provides AlbumService with UnitOfWork."""
    async with async_session_factory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        yield AlbumService(uow)


async def get_track_service() -> TrackService:
    """Provides TrackService with UnitOfWork."""
    async with async_session_factory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        yield TrackService(uow)


async def get_pressing_service() -> PressingService:
    """Provides PressingService with UnitOfWork."""
    async with async_session_factory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        yield PressingService(uow)


async def get_collection_service() -> CollectionService:
    """Provides CollectionService with UnitOfWork."""
    async with async_session_factory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        yield CollectionService(uow)


async def get_lookup_service() -> LookupService:
    """Provides LookupService with UnitOfWork."""
    async with async_session_factory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        yield LookupService(uow)


async def get_preferences_service() -> PreferencesService:
    """Provides PreferencesService with UnitOfWork."""
    async with async_session_factory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        yield PreferencesService(uow)


async def get_system_log_service() -> SystemLogService:
    """Provides SystemLogService with UnitOfWork."""
    async with async_session_factory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        yield SystemLogService(uow)


async def get_discogs_service() -> DiscogsService:
    """Provides DiscogsService with Discogs client adapter and cache repository."""
    discogs_client = DiscogsClientAdapter(settings.discogs_service_url, timeout_seconds=60.0)

    # Create cache repository with new session
    async with async_session_factory() as session:
        cache_repo = PostgresDiscogsCacheRepository(session)
        yield DiscogsService(discogs_client, cache_repo)


async def get_collection_sharing_service() -> CollectionSharingService:
    """Provides CollectionSharingService with UnitOfWork."""
    async with async_session_factory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        yield CollectionSharingService(uow)


async def get_album_wizard_service() -> AlbumWizardService:
    """Provides AlbumWizardService with UnitOfWork and AI client adapter."""
    wizard_client = AlbumWizardClientAdapter(
        base_url=settings.album_wizard_api_url,
        api_key=settings.album_wizard_api_key,
        model_id=settings.album_wizard_model_id,
        timeout_seconds=settings.album_wizard_timeout_seconds,
    )
    async with async_session_factory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        yield AlbumWizardService(uow, wizard_client)


async def get_collection_import_service() -> CollectionImportService:
    """Provides CollectionImportService with UnitOfWork and DiscogsService."""
    discogs_client = DiscogsClientAdapter(settings.discogs_service_url, timeout_seconds=60.0)

    async with async_session_factory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        cache_repo = PostgresDiscogsCacheRepository(session)
        discogs_service = DiscogsService(discogs_client, cache_repo)
        yield CollectionImportService(uow, discogs_service, settings.discogs_import_log_level)


async def get_discogs_oauth_service() -> DiscogsOAuthService:
    """Provides DiscogsOAuthService with UnitOfWork and OAuth client."""
    oauth_client = DiscogsOAuthClientAdapter(
        consumer_key=settings.discogs_consumer_key,
        consumer_secret=settings.discogs_consumer_secret,
        api_base_url=settings.discogs_oauth_api_base_url,
        authorize_url=settings.discogs_oauth_authorize_url,
        user_agent=settings.discogs_user_agent,
        rate_limit_per_minute=settings.discogs_oauth_rate_limit_per_minute,
    )
    async with async_session_factory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        yield DiscogsOAuthService(
            uow=uow,
            oauth_client=oauth_client,
            authorize_url=settings.discogs_oauth_authorize_url,
            callback_url=settings.discogs_oauth_callback_url,
            frontend_base_url=settings.frontend_base_url,
        )


async def get_discogs_pat_service() -> DiscogsPatService:
    """Provides DiscogsPatService with UnitOfWork."""
    async with async_session_factory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        yield DiscogsPatService(uow)


async def get_discogs_collection_sync_service() -> DiscogsCollectionSyncService:
    """Provides DiscogsCollectionSyncService with UnitOfWork and OAuth client."""
    oauth_client = DiscogsOAuthClientAdapter(
        consumer_key=settings.discogs_consumer_key,
        consumer_secret=settings.discogs_consumer_secret,
        api_base_url=settings.discogs_oauth_api_base_url,
        authorize_url=settings.discogs_oauth_authorize_url,
        user_agent=settings.discogs_user_agent,
        rate_limit_per_minute=settings.discogs_oauth_rate_limit_per_minute,
    )
    discogs_client = DiscogsClientAdapter(settings.discogs_service_url, timeout_seconds=60.0)

    async with async_session_factory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        cache_repo = PostgresDiscogsCacheRepository(session)
        discogs_service = DiscogsService(discogs_client, cache_repo)
        import_service = CollectionImportService(uow, discogs_service, settings.discogs_import_log_level)
        yield DiscogsCollectionSyncService(
            uow=uow,
            oauth_client=oauth_client,
            import_service=import_service,
            import_log_level=settings.discogs_import_log_level,
        )
