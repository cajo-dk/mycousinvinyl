"""
SQLAlchemy Unit of Work implementation.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.unit_of_work import UnitOfWork
from app.adapters.postgres.artist_repository_adapter import ArtistRepositoryAdapter
from app.adapters.postgres.album_repository_adapter import AlbumRepositoryAdapter
from app.adapters.postgres.track_repository_adapter import TrackRepositoryAdapter
from app.adapters.postgres.pressing_repository_adapter import PressingRepositoryAdapter
from app.adapters.postgres.collection_repository_adapter import CollectionRepositoryAdapter
from app.adapters.postgres.lookup_repository_adapter import LookupRepositoryAdapter
from app.adapters.postgres.additional_repository_adapters import (
    MatrixRepositoryAdapter,
    PackagingRepositoryAdapter,
    PreferencesRepositoryAdapter,
    MediaRepositoryAdapter,
    ExternalReferenceRepositoryAdapter,
    DiscogsOAuthRequestRepositoryAdapter,
    DiscogsUserTokenRepositoryAdapter,
)
from app.adapters.postgres.outbox_repository_adapter import OutboxRepositoryAdapter
from app.adapters.postgres.user_follows_repository_adapter import UserFollowsRepositoryAdapter
from app.adapters.postgres.collection_import_repository_adapter import CollectionImportRepositoryAdapter


class SqlAlchemyUnitOfWork(UnitOfWork):
    """
    SQLAlchemy implementation of Unit of Work.

    Manages a database session and provides access to all repositories.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

        # Initialize all repository adapters with the session
        self.artist_repository = ArtistRepositoryAdapter(session)
        self.album_repository = AlbumRepositoryAdapter(session)
        self.track_repository = TrackRepositoryAdapter(session)
        self.pressing_repository = PressingRepositoryAdapter(session)
        self.matrix_repository = MatrixRepositoryAdapter(session)
        self.packaging_repository = PackagingRepositoryAdapter(session)
        self.collection_repository = CollectionRepositoryAdapter(session)
        self.preferences_repository = PreferencesRepositoryAdapter(session)
        self.lookup_repository = LookupRepositoryAdapter(session)
        self.media_repository = MediaRepositoryAdapter(session)
        self.external_reference_repository = ExternalReferenceRepositoryAdapter(session)
        self.discogs_oauth_request_repository = DiscogsOAuthRequestRepositoryAdapter(session)
        self.discogs_user_token_repository = DiscogsUserTokenRepositoryAdapter(session)
        self.outbox_repository = OutboxRepositoryAdapter(session)
        self.user_follows_repository = UserFollowsRepositoryAdapter(session)
        self.collection_import_repository = CollectionImportRepositoryAdapter(session)

    async def __aenter__(self):
        """Enter the unit of work context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the unit of work context, handling commit/rollback."""
        if exc_type is not None:
            await self.rollback()
        await self.session.close()

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self.session.rollback()
