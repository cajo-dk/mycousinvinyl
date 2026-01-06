"""Additional repository adapters for simpler entities."""

from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy import select, func, delete, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.matrix_repository import MatrixRepository
from app.application.ports.packaging_repository import PackagingRepository
from app.application.ports.preferences_repository import PreferencesRepository
from app.application.ports.media_repository import MediaRepository
from app.application.ports.external_reference_repository import ExternalReferenceRepository
from app.application.ports.discogs_oauth_repository import (
    DiscogsOAuthRequestRepository,
    DiscogsUserTokenRepository,
)
from app.domain.entities import (
    Matrix,
    Packaging,
    UserPreferences,
    MediaAsset,
    ExternalReference,
    DiscogsOAuthRequest,
    DiscogsUserToken,
)
from app.adapters.postgres.models import (
    MatrixModel, PackagingModel, UserPreferencesModel,
    MediaAssetModel, ExternalReferenceModel,
    DiscogsOAuthRequestModel, DiscogsUserTokenModel
)


# ============================================================================
# MATRIX REPOSITORY
# ============================================================================

class MatrixRepositoryAdapter(MatrixRepository):
    """PostgreSQL implementation of MatrixRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, matrix: Matrix) -> Matrix:
        """Add a new matrix code."""
        model = MatrixModel.from_domain(matrix)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def get(self, matrix_id: UUID) -> Optional[Matrix]:
        """Get matrix by ID."""
        result = await self.session.execute(
            select(MatrixModel).where(MatrixModel.id == matrix_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_pressing(self, pressing_id: UUID) -> List[Matrix]:
        """Get all matrix codes for a pressing, sorted by side."""
        result = await self.session.execute(
            select(MatrixModel)
            .where(MatrixModel.pressing_id == pressing_id)
            .order_by(MatrixModel.side)
        )
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def get_by_pressing_and_side(self, pressing_id: UUID, side: str) -> Optional[Matrix]:
        """Get matrix code for a specific pressing side."""
        result = await self.session.execute(
            select(MatrixModel).where(
                MatrixModel.pressing_id == pressing_id,
                MatrixModel.side == side
            )
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def update(self, matrix: Matrix) -> Matrix:
        """Update matrix code."""
        result = await self.session.execute(
            select(MatrixModel).where(MatrixModel.id == matrix.id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Matrix {matrix.id} not found")

        model.pressing_id = matrix.pressing_id
        model.side = matrix.side
        model.matrix_code = matrix.matrix_code
        model.etchings = matrix.etchings
        model.stamper_info = matrix.stamper_info

        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, matrix_id: UUID) -> None:
        """Delete matrix code."""
        result = await self.session.execute(
            select(MatrixModel).where(MatrixModel.id == matrix_id)
        )
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def bulk_upsert(self, pressing_id: UUID, matrices: List[Matrix]) -> List[Matrix]:
        """Bulk upsert matrix codes for a pressing."""
        # Delete existing matrices for this pressing
        await self.session.execute(
            delete(MatrixModel).where(MatrixModel.pressing_id == pressing_id)
        )

        # Insert new matrices
        result_matrices = []
        for matrix in matrices:
            model = MatrixModel.from_domain(matrix)
            self.session.add(model)
            await self.session.flush()
            await self.session.refresh(model)
            result_matrices.append(model.to_domain())

        return result_matrices


# ============================================================================
# PACKAGING REPOSITORY
# ============================================================================

class PackagingRepositoryAdapter(PackagingRepository):
    """PostgreSQL implementation of PackagingRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, packaging: Packaging) -> Packaging:
        """Add packaging details for a pressing."""
        model = PackagingModel.from_domain(packaging)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def get(self, packaging_id: UUID) -> Optional[Packaging]:
        """Get packaging by ID."""
        result = await self.session.execute(
            select(PackagingModel).where(PackagingModel.id == packaging_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_pressing(self, pressing_id: UUID) -> Optional[Packaging]:
        """Get packaging for a pressing (one-to-one relationship)."""
        result = await self.session.execute(
            select(PackagingModel).where(PackagingModel.pressing_id == pressing_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def update(self, packaging: Packaging) -> Packaging:
        """Update packaging details."""
        result = await self.session.execute(
            select(PackagingModel).where(PackagingModel.id == packaging.id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Packaging {packaging.id} not found")

        model.pressing_id = packaging.pressing_id
        model.sleeve_type = packaging.sleeve_type
        model.cover_artist = packaging.cover_artist
        model.includes_inner_sleeve = packaging.includes_inner_sleeve
        model.includes_insert = packaging.includes_insert
        model.includes_poster = packaging.includes_poster
        model.includes_obi = packaging.includes_obi
        model.stickers = packaging.stickers
        model.notes = packaging.notes

        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, packaging_id: UUID) -> None:
        """Delete packaging."""
        result = await self.session.execute(
            select(PackagingModel).where(PackagingModel.id == packaging_id)
        )
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def upsert(self, packaging: Packaging) -> Packaging:
        """Upsert packaging (update if exists, insert if not)."""
        # Check if packaging exists for this pressing
        existing = await self.get_by_pressing(packaging.pressing_id)

        if existing:
            # Update existing
            packaging.id = existing.id
            return await self.update(packaging)
        else:
            # Insert new
            return await self.add(packaging)


# ============================================================================
# PREFERENCES REPOSITORY
# ============================================================================

class PreferencesRepositoryAdapter(PreferencesRepository):
    """PostgreSQL implementation of PreferencesRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: UUID) -> Optional[UserPreferences]:
        """Get user preferences by user ID."""
        result = await self.session.execute(
            select(UserPreferencesModel).where(UserPreferencesModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def create(self, preferences: UserPreferences) -> UserPreferences:
        """Create user preferences."""
        model = UserPreferencesModel.from_domain(preferences)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def update(self, preferences: UserPreferences) -> UserPreferences:
        """Update user preferences."""
        result = await self.session.execute(
            select(UserPreferencesModel).where(
                UserPreferencesModel.user_id == preferences.user_id
            )
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Preferences for user {preferences.user_id} not found")

        model.currency = preferences.currency
        model.display_settings = preferences.display_settings

        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def get_or_create_default(self, user_id: UUID) -> UserPreferences:
        """Get user preferences or create with defaults if not exists."""
        existing = await self.get(user_id)

        if existing:
            return existing

        # Create default preferences
        default_prefs = UserPreferences(user_id=user_id, currency="DKK", display_settings={})
        return await self.create(default_prefs)

    async def get_many_by_user_ids(self, user_ids: List[UUID]) -> Dict[UUID, UserPreferences]:
        """
        Get multiple user preferences by list of user IDs.

        Args:
            user_ids: List of user IDs to retrieve preferences for

        Returns:
            Dictionary mapping user_id to UserPreferences (only includes found users)
        """
        if not user_ids:
            return {}

        result = await self.session.execute(
            select(UserPreferencesModel).where(
                UserPreferencesModel.user_id.in_(user_ids)
            )
        )
        models = result.scalars().all()

        return {
            model.user_id: model.to_domain()
            for model in models
        }

    async def search_users_by_name(self, query: str, limit: int = 10) -> List[UserPreferences]:
        """
        Search for users by name (for autocomplete in user search).

        Searches in user_profile.display_name and user_profile.first_name fields
        stored in display_settings JSONB. Only returns users with collection
        sharing enabled.

        Args:
            query: Search query string (case-insensitive partial match)
            limit: Maximum number of results to return (default 10)

        Returns:
            List of UserPreferences for matching users with sharing enabled
        """
        if not query or not query.strip():
            return []

        search_term = f"%{query.lower()}%"

        # Search in JSONB fields: display_settings->'user_profile'->>'display_name' and 'first_name'
        # Also filter for collection_sharing->>'enabled' = 'true'
        result = await self.session.execute(
            select(UserPreferencesModel)
            .where(
                # Only users with sharing enabled
                cast(
                    UserPreferencesModel.display_settings['collection_sharing']['enabled'].astext,
                    String
                ) == 'true'
            )
            .where(
                # Search in display_name or first_name (case-insensitive)
                or_(
                    func.lower(
                        UserPreferencesModel.display_settings['user_profile']['display_name'].astext
                    ).like(search_term),
                    func.lower(
                        UserPreferencesModel.display_settings['user_profile']['first_name'].astext
                    ).like(search_term)
                )
            )
            .limit(limit)
        )

        models = result.scalars().all()
        return [model.to_domain() for model in models]


# ============================================================================
# MEDIA REPOSITORY
# ============================================================================

class MediaRepositoryAdapter(MediaRepository):
    """PostgreSQL implementation of MediaRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, media: MediaAsset) -> MediaAsset:
        """Add a new media asset."""
        model = MediaAssetModel.from_domain(media)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def get(self, media_id: UUID) -> Optional[MediaAsset]:
        """Get media asset by ID."""
        result = await self.session.execute(
            select(MediaAssetModel).where(MediaAssetModel.id == media_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: UUID
    ) -> List[MediaAsset]:
        """Get all media assets for an entity."""
        result = await self.session.execute(
            select(MediaAssetModel).where(
                MediaAssetModel.entity_type == entity_type,
                MediaAssetModel.entity_id == entity_id
            ).order_by(MediaAssetModel.created_at)
        )
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def update(self, media: MediaAsset) -> MediaAsset:
        """Update media asset."""
        result = await self.session.execute(
            select(MediaAssetModel).where(MediaAssetModel.id == media.id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Media asset {media.id} not found")

        model.entity_type = media.entity_type
        model.entity_id = media.entity_id
        model.media_type = media.media_type
        model.url = media.url
        model.description = media.description
        model.uploaded_by_user = media.uploaded_by_user

        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, media_id: UUID) -> None:
        """Delete media asset."""
        result = await self.session.execute(
            select(MediaAssetModel).where(MediaAssetModel.id == media_id)
        )
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()


# ============================================================================
# EXTERNAL REFERENCE REPOSITORY
# ============================================================================

class ExternalReferenceRepositoryAdapter(ExternalReferenceRepository):
    """PostgreSQL implementation of ExternalReferenceRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, reference: ExternalReference) -> ExternalReference:
        """Add a new external reference."""
        model = ExternalReferenceModel.from_domain(reference)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def get(self, reference_id: UUID) -> Optional[ExternalReference]:
        """Get external reference by ID."""
        result = await self.session.execute(
            select(ExternalReferenceModel).where(ExternalReferenceModel.id == reference_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: UUID
    ) -> List[ExternalReference]:
        """Get all external references for an entity."""
        result = await self.session.execute(
            select(ExternalReferenceModel).where(
                ExternalReferenceModel.entity_type == entity_type,
                ExternalReferenceModel.entity_id == entity_id
            ).order_by(ExternalReferenceModel.source)
        )
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def get_by_entity_and_source(
        self,
        entity_type: str,
        entity_id: UUID,
        source
    ) -> Optional[ExternalReference]:
        """Get external reference for an entity and specific source."""
        result = await self.session.execute(
            select(ExternalReferenceModel).where(
                ExternalReferenceModel.entity_type == entity_type,
                ExternalReferenceModel.entity_id == entity_id,
                ExternalReferenceModel.source == source
            )
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def update(self, reference: ExternalReference) -> ExternalReference:
        """Update external reference."""
        result = await self.session.execute(
            select(ExternalReferenceModel).where(ExternalReferenceModel.id == reference.id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"External reference {reference.id} not found")

        model.entity_type = reference.entity_type
        model.entity_id = reference.entity_id
        model.source = reference.source
        model.external_id = reference.external_id
        model.url = reference.url

        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, reference_id: UUID) -> None:
        """Delete external reference."""
        result = await self.session.execute(
            select(ExternalReferenceModel).where(ExternalReferenceModel.id == reference_id)
        )
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def upsert(self, reference: ExternalReference) -> ExternalReference:
        """Upsert external reference (update if exists, insert if not)."""
        existing = await self.get_by_entity_and_source(
            reference.entity_type,
            reference.entity_id,
            reference.source
        )

        if existing:
            reference.id = existing.id
            return await self.update(reference)
        else:
            return await self.add(reference)


# ============================================================================
# DISCOGS OAUTH REPOSITORIES
# ============================================================================

class DiscogsOAuthRequestRepositoryAdapter(DiscogsOAuthRequestRepository):
    """PostgreSQL implementation of DiscogsOAuthRequestRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, request: DiscogsOAuthRequest) -> DiscogsOAuthRequest:
        model = DiscogsOAuthRequestModel.from_domain(request)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def get_by_token(self, request_token: str) -> Optional[DiscogsOAuthRequest]:
        result = await self.session.execute(
            select(DiscogsOAuthRequestModel).where(
                DiscogsOAuthRequestModel.request_token == request_token
            )
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def delete(self, request_id: UUID) -> None:
        result = await self.session.execute(
            select(DiscogsOAuthRequestModel).where(DiscogsOAuthRequestModel.id == request_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()


class DiscogsUserTokenRepositoryAdapter(DiscogsUserTokenRepository):
    """PostgreSQL implementation of DiscogsUserTokenRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, token: DiscogsUserToken) -> DiscogsUserToken:
        existing = await self.get_by_user(token.user_id)
        if existing:
            result = await self.session.execute(
                select(DiscogsUserTokenModel).where(DiscogsUserTokenModel.user_id == token.user_id)
            )
            model = result.scalar_one()
            model.access_token = token.access_token
            model.access_secret = token.access_secret
            model.discogs_username = token.discogs_username
            model.last_synced_at = token.last_synced_at
            await self.session.flush()
            await self.session.refresh(model)
            return model.to_domain()

        model = DiscogsUserTokenModel.from_domain(token)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def get_by_user(self, user_id: UUID) -> Optional[DiscogsUserToken]:
        result = await self.session.execute(
            select(DiscogsUserTokenModel).where(DiscogsUserTokenModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def delete_by_user(self, user_id: UUID) -> None:
        result = await self.session.execute(
            select(DiscogsUserTokenModel).where(DiscogsUserTokenModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()
