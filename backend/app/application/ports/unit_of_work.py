"""
Unit of Work port interface.

Manages database transactions and coordinates repository access.
"""

from abc import ABC, abstractmethod

from app.application.ports.artist_repository import ArtistRepository
from app.application.ports.album_repository import AlbumRepository
from app.application.ports.track_repository import TrackRepository
from app.application.ports.pressing_repository import PressingRepository
from app.application.ports.matrix_repository import MatrixRepository
from app.application.ports.packaging_repository import PackagingRepository
from app.application.ports.collection_repository import CollectionRepository
from app.application.ports.preferences_repository import PreferencesRepository
from app.application.ports.lookup_repository import LookupRepository
from app.application.ports.media_repository import MediaRepository
from app.application.ports.external_reference_repository import ExternalReferenceRepository
from app.application.ports.discogs_oauth_repository import (
    DiscogsOAuthRequestRepository,
    DiscogsUserTokenRepository,
)
from app.application.ports.outbox_repository import OutboxRepository
from app.application.ports.user_follows_repository import UserFollowsRepository
from app.application.ports.collection_import_repository import CollectionImportRepository


class UnitOfWork(ABC):
    """
    Unit of Work interface for transaction management.

    Coordinates access to all repositories and manages database transactions.
    """

    # Repository instances
    artist_repository: ArtistRepository
    album_repository: AlbumRepository
    track_repository: TrackRepository
    pressing_repository: PressingRepository
    matrix_repository: MatrixRepository
    packaging_repository: PackagingRepository
    collection_repository: CollectionRepository
    preferences_repository: PreferencesRepository
    lookup_repository: LookupRepository
    media_repository: MediaRepository
    external_reference_repository: ExternalReferenceRepository
    discogs_oauth_request_repository: DiscogsOAuthRequestRepository
    discogs_user_token_repository: DiscogsUserTokenRepository
    outbox_repository: OutboxRepository
    user_follows_repository: UserFollowsRepository
    collection_import_repository: CollectionImportRepository

    @abstractmethod
    async def __aenter__(self):
        """Enter the unit of work context."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the unit of work context, handling commit/rollback."""
        pass

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        pass
