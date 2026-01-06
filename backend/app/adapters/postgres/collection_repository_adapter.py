"""Collection repository PostgreSQL adapter."""

from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.collection_repository import CollectionRepository
from app.domain.entities import CollectionItem
from app.adapters.postgres.models import (
    CollectionItemModel,
    PressingModel,
    AlbumModel,
    ArtistModel,
    MarketDataModel,
    UserPreferencesModel,
)


class CollectionRepositoryAdapter(CollectionRepository):
    """
    PostgreSQL implementation of CollectionRepository.

    CRITICAL: All methods enforce user_id filtering for security.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, item: CollectionItem) -> CollectionItem:
        """Add a new item to collection."""
        model = CollectionItemModel.from_domain(item)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def get(self, item_id: UUID, user_id: UUID) -> Optional[CollectionItem]:
        """
        Get collection item by ID.

        CRITICAL: Enforces user_id ownership check.
        """
        result = await self.session.execute(
            select(CollectionItemModel).where(
                and_(
                    CollectionItemModel.id == item_id,
                    CollectionItemModel.user_id == user_id  # SECURITY: User isolation
                )
            )
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_all_for_user(
        self,
        user_id: UUID,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "date_added_desc",
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[CollectionItem], int]:
        """
        Get all collection items for a user with filters and sorting.

        CRITICAL: All queries filtered by user_id.
        """
        filters = filters or {}

        # Build base query with user_id filter (SECURITY)
        query = select(CollectionItemModel).where(
            CollectionItemModel.user_id == user_id
        )

        # Build filter conditions
        where_clauses = []

        # Media condition filter
        if 'media_condition' in filters and filters['media_condition']:
            where_clauses.append(
                CollectionItemModel.media_condition.in_(filters['media_condition'])
            )

        # Sleeve condition filter
        if 'sleeve_condition' in filters and filters['sleeve_condition']:
            where_clauses.append(
                CollectionItemModel.sleeve_condition.in_(filters['sleeve_condition'])
            )

        # Rating range filter
        if 'rating_min' in filters:
            where_clauses.append(
                CollectionItemModel.user_rating >= filters['rating_min']
            )
        if 'rating_max' in filters:
            where_clauses.append(
                CollectionItemModel.user_rating <= filters['rating_max']
            )

        # Price range filter
        if 'price_min' in filters:
            where_clauses.append(
                CollectionItemModel.purchase_price >= filters['price_min']
            )
        if 'price_max' in filters:
            where_clauses.append(
                CollectionItemModel.purchase_price <= filters['price_max']
            )

        # Tags filter (OR - any of the tags)
        if 'tags' in filters and filters['tags']:
            # PostgreSQL array overlap operator
            where_clauses.append(
                CollectionItemModel.tags.op('&&')(filters['tags'])
            )

        # Apply filters
        if where_clauses:
            query = query.where(and_(*where_clauses))

        # Get total count (with filters, with user_id)
        count_query = select(func.count()).select_from(query.alias())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        # Apply sorting
        if sort_by == "date_added_desc":
            query = query.order_by(CollectionItemModel.date_added.desc())
        elif sort_by == "date_added_asc":
            query = query.order_by(CollectionItemModel.date_added.asc())
        elif sort_by == "rating_desc":
            query = query.order_by(CollectionItemModel.user_rating.desc().nullslast())
        elif sort_by == "rating_asc":
            query = query.order_by(CollectionItemModel.user_rating.asc().nullslast())
        elif sort_by == "price_desc":
            query = query.order_by(CollectionItemModel.purchase_price.desc().nullslast())
        elif sort_by == "price_asc":
            query = query.order_by(CollectionItemModel.purchase_price.asc().nullslast())
        elif sort_by == "condition_desc":
            query = query.order_by(CollectionItemModel.media_condition.desc())
        elif sort_by == "condition_asc":
            query = query.order_by(CollectionItemModel.media_condition.asc())
        else:
            query = query.order_by(CollectionItemModel.date_added.desc())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(query)
        models = result.scalars().all()

        return [m.to_domain() for m in models], total

    async def search_user_collection(
        self,
        user_id: UUID,
        query: str,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[CollectionItem], int]:
        """
        Search within user's collection (searches album/artist names).

        CRITICAL: Filtered by user_id.
        """
        # Join to pressings, albums, and artists to search titles/names
        search_query = select(CollectionItemModel).join(
            PressingModel, CollectionItemModel.pressing_id == PressingModel.id
        ).join(
            AlbumModel, PressingModel.album_id == AlbumModel.id
        ).join(
            ArtistModel, AlbumModel.primary_artist_id == ArtistModel.id
        ).where(
            and_(
                CollectionItemModel.user_id == user_id,  # SECURITY: User isolation
                or_(
                    AlbumModel.title.ilike(f"%{query}%"),
                    ArtistModel.name.ilike(f"%{query}%")
                )
            )
        )

        # Get total count
        count_query = select(func.count()).select_from(search_query.alias())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        # Apply pagination
        search_query = search_query.limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(search_query)
        models = result.scalars().all()

        return [m.to_domain() for m in models], total

    async def update(self, item: CollectionItem, user_id: UUID) -> CollectionItem:
        """
        Update collection item.

        CRITICAL: Verifies user_id ownership.
        """
        # Get existing model with user_id check
        result = await self.session.execute(
            select(CollectionItemModel).where(
                and_(
                    CollectionItemModel.id == item.id,
                    CollectionItemModel.user_id == user_id  # SECURITY: User isolation
                )
            )
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Collection item {item.id} not found for user {user_id}")

        # Update fields
        model.pressing_id = item.pressing_id
        model.media_condition = item.media_condition
        model.sleeve_condition = item.sleeve_condition
        model.play_tested = item.play_tested
        model.defect_notes = item.defect_notes
        model.purchase_price = item.purchase_price
        model.purchase_currency = item.purchase_currency
        model.purchase_date = item.purchase_date
        model.seller = item.seller
        model.storage_location = item.storage_location
        model.play_count = item.play_count
        model.last_played_date = item.last_played_date
        model.user_rating = item.user_rating
        model.user_notes = item.user_notes
        model.tags = item.tags

        await self.session.flush()
        await self.session.refresh(model)
        return model.to_domain()

    async def delete(self, item_id: UUID, user_id: UUID) -> None:
        """
        Delete collection item.

        CRITICAL: Verifies user_id ownership.
        """
        result = await self.session.execute(
            select(CollectionItemModel).where(
                and_(
                    CollectionItemModel.id == item_id,
                    CollectionItemModel.user_id == user_id  # SECURITY: User isolation
                )
            )
        )
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def exists(self, item_id: UUID, user_id: UUID) -> bool:
        """
        Check if collection item exists for user.

        CRITICAL: Verifies user_id ownership.
        """
        result = await self.session.execute(
            select(func.count()).select_from(CollectionItemModel).where(
                and_(
                    CollectionItemModel.id == item_id,
                    CollectionItemModel.user_id == user_id  # SECURITY: User isolation
                )
            )
        )
        count = result.scalar_one()
        return count > 0

    async def exists_for_user_pressing(self, user_id: UUID, pressing_id: UUID) -> bool:
        """
        Check if user already has a pressing in their collection.

        CRITICAL: Verifies user_id ownership.
        """
        result = await self.session.execute(
            select(func.count()).select_from(CollectionItemModel).where(
                and_(
                    CollectionItemModel.user_id == user_id,  # SECURITY: User isolation
                    CollectionItemModel.pressing_id == pressing_id
                )
            )
        )
        count = result.scalar_one()
        return count > 0

    async def get_all_with_details(
        self,
        user_id: UUID,
        query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "artist_album"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get collection items with joined artist and album details.

        Returns enriched data for hierarchical display in UI.
        CRITICAL: Filtered by user_id.
        """
        from app.adapters.postgres.models import (
            PressingModel, AlbumModel, ArtistModel, MarketDataModel
        )
        from sqlalchemy.orm import selectinload

        # Build base query with joins and eager loading
        stmt = select(
            CollectionItemModel,
            PressingModel,
            AlbumModel,
            ArtistModel,
            MarketDataModel
        ).join(
            PressingModel, CollectionItemModel.pressing_id == PressingModel.id
        ).join(
            AlbumModel, PressingModel.album_id == AlbumModel.id
        ).join(
            ArtistModel, AlbumModel.primary_artist_id == ArtistModel.id
        ).outerjoin(
            MarketDataModel, MarketDataModel.pressing_id == PressingModel.id
        ).options(
            selectinload(AlbumModel.genres)
        ).where(
            CollectionItemModel.user_id == user_id  # SECURITY: User isolation
        )

        # Add search filter if provided
        if query:
            stmt = stmt.where(
                or_(
                    AlbumModel.title.ilike(f"%{query}%"),
                    ArtistModel.name.ilike(f"%{query}%")
                )
            )

        # Get total count
        count_stmt = select(func.count()).select_from(
            select(CollectionItemModel.id).join(
                PressingModel, CollectionItemModel.pressing_id == PressingModel.id
            ).join(
                AlbumModel, PressingModel.album_id == AlbumModel.id
            ).join(
                ArtistModel, AlbumModel.primary_artist_id == ArtistModel.id
            ).where(
                CollectionItemModel.user_id == user_id
            ).subquery()
        )

        if query:
            count_stmt = select(func.count()).select_from(
                select(CollectionItemModel.id).join(
                    PressingModel, CollectionItemModel.pressing_id == PressingModel.id
                ).join(
                    AlbumModel, PressingModel.album_id == AlbumModel.id
                ).join(
                    ArtistModel, AlbumModel.primary_artist_id == ArtistModel.id
                ).where(
                    and_(
                        CollectionItemModel.user_id == user_id,
                        or_(
                            AlbumModel.title.ilike(f"%{query}%"),
                            ArtistModel.name.ilike(f"%{query}%")
                        )
                    )
                ).subquery()
            )

        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        # Apply pagination and ordering
        if sort_by == "date_added_asc":
            stmt = stmt.order_by(
                CollectionItemModel.date_added.asc().nullslast(),
                CollectionItemModel.id.asc()
            )
        elif sort_by == "date_added_desc":
            stmt = stmt.order_by(
                CollectionItemModel.date_added.desc().nullslast(),
                CollectionItemModel.id.desc()
            )
        else:
            stmt = stmt.order_by(
                ArtistModel.sort_name.asc().nullslast(),
                ArtistModel.name.asc(),
                AlbumModel.original_release_year.asc().nullslast(),
                AlbumModel.title.asc()
            )
        stmt = stmt.limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(stmt)
        rows = result.all()

        # Build enriched response data
        items = []
        for collection_item, pressing, album, artist, market_data in rows:
            # Access genres through the relationship (already eager loaded)
            genres = [g.name for g in album.genres]

            items.append({
                "collection_item": collection_item,
                "pressing": pressing,
                "artist": artist,
                "album": album,
                "genres": genres,
                "market_data": market_data
            })

        return items, total

    async def get_statistics(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get collection statistics for user.

        Returns purchase price-based statistics and estimated sales price statistics.
        """
        # Get all collection items for user with market data
        result = await self.session.execute(
            select(CollectionItemModel, MarketDataModel)
            .outerjoin(PressingModel, CollectionItemModel.pressing_id == PressingModel.id)
            .outerjoin(MarketDataModel, PressingModel.id == MarketDataModel.pressing_id)
            .where(CollectionItemModel.user_id == user_id)
        )
        rows = result.all()

        total_albums = len(rows)

        # Calculate purchase price statistics
        prices = [
            item.purchase_price for item, _ in rows
            if item.purchase_price is not None
        ]

        if prices:
            total_purchase_price = sum(prices)
            min_value = min(prices)
            avg_value = total_purchase_price / len(prices)
            max_value = max(prices)
        else:
            total_purchase_price = Decimal(0)
            min_value = Decimal(0)
            avg_value = Decimal(0)
            max_value = Decimal(0)

        # Calculate estimated sales price statistics from market data
        low_est_prices = [
            market_data.min_value for _, market_data in rows
            if market_data and market_data.min_value is not None
        ]
        avg_est_prices = [
            market_data.median_value for _, market_data in rows
            if market_data and market_data.median_value is not None
        ]
        high_est_prices = [
            market_data.max_value for _, market_data in rows
            if market_data and market_data.max_value is not None
        ]

        low_est_sales_price = sum(low_est_prices) if low_est_prices else Decimal(0)
        avg_est_sales_price = sum(avg_est_prices) if avg_est_prices else Decimal(0)
        high_est_sales_price = sum(high_est_prices) if high_est_prices else Decimal(0)

        # Get currency from first item with price, or default to DKK
        currency = "DKK"
        for item, _ in rows:
            if item.purchase_currency:
                currency = item.purchase_currency
                break

        return {
            "total_albums": total_albums,
            "total_purchase_price": total_purchase_price,
            "min_value": min_value,
            "avg_value": avg_value,
            "max_value": max_value,
            "low_est_sales_price": low_est_sales_price,
            "avg_est_sales_price": avg_est_sales_price,
            "high_est_sales_price": high_est_sales_price,
            "currency": currency
        }

    async def get_owners_for_pressing(
        self,
        pressing_id: UUID,
        viewer_user_id: UUID,
        followed_user_ids: List[UUID]
    ) -> List[Tuple[UUID, int]]:
        """
        Get owners of a specific pressing (viewer + followed users with sharing enabled).

        Only returns users who:
        1. Own the pressing (have collection_items for this pressing_id)
        2. Have collection sharing enabled (for followed users)
        3. Are either the viewer themselves OR are in the followed_user_ids list

        Args:
            pressing_id: The pressing to check ownership for
            viewer_user_id: The current user viewing (always included if they own it)
            followed_user_ids: List of user IDs that viewer follows

        Returns:
            List of tuples (user_id, copy_count) where copy_count is the number
            of copies owned by that user
        """
        # Query to get owners with copy counts
        # For viewer: always include if they own it
        # For followed users: only include if sharing is enabled

        query = (
            select(
                CollectionItemModel.user_id,
                func.count(CollectionItemModel.id).label('copy_count')
            )
            .where(CollectionItemModel.pressing_id == pressing_id)
            .group_by(CollectionItemModel.user_id)
        )

        # Get all owners
        result = await self.session.execute(query)
        all_owners = result.all()

        if not all_owners:
            return []

        # Separate viewer's ownership from others
        owner_dict = {user_id: copy_count for user_id, copy_count in all_owners}

        # Build result list
        result_list = []

        # Always include viewer if they own it
        if viewer_user_id in owner_dict:
            result_list.append((viewer_user_id, owner_dict[viewer_user_id]))

        # Check followed users
        if followed_user_ids:
            # Get user IDs from owner_dict that are in followed_user_ids
            followed_owners = [uid for uid in followed_user_ids if uid in owner_dict]

            if followed_owners:
                # Check which of these followed owners have sharing enabled
                prefs_query = (
                    select(UserPreferencesModel.user_id)
                    .where(UserPreferencesModel.user_id.in_(followed_owners))
                    .where(
                        cast(
                            UserPreferencesModel.display_settings['collection_sharing']['enabled'].astext,
                            String
                        ) == 'true'
                    )
                )

                prefs_result = await self.session.execute(prefs_query)
                users_with_sharing = {user_id for user_id, in prefs_result.all()}

                # Add followed users with sharing enabled
                for user_id in followed_owners:
                    if user_id in users_with_sharing:
                        result_list.append((user_id, owner_dict[user_id]))

        return result_list

    async def get_owners_for_pressings(
        self,
        pressing_ids: List[UUID],
        viewer_user_id: UUID,
        followed_user_ids: List[UUID]
    ) -> Dict[UUID, List[Tuple[UUID, int]]]:
        """
        Get owners for multiple pressings (viewer + followed users with sharing enabled).

        Returns a dictionary keyed by pressing_id with ordered owners.
        """
        if not pressing_ids:
            return {}

        query = (
            select(
                CollectionItemModel.pressing_id,
                CollectionItemModel.user_id,
                func.count(CollectionItemModel.id).label('copy_count')
            )
            .where(CollectionItemModel.pressing_id.in_(pressing_ids))
            .group_by(CollectionItemModel.pressing_id, CollectionItemModel.user_id)
        )

        result = await self.session.execute(query)
        all_owners = result.all()

        if not all_owners:
            return {}

        owners_by_pressing: Dict[UUID, Dict[UUID, int]] = {}
        for pressing_id, user_id, copy_count in all_owners:
            owners_by_pressing.setdefault(pressing_id, {})[user_id] = copy_count

        followed_set = set(followed_user_ids or [])
        followed_owner_ids = {
            user_id
            for owner_dict in owners_by_pressing.values()
            for user_id in owner_dict.keys()
            if user_id in followed_set
        }

        users_with_sharing: set[UUID] = set()
        if followed_owner_ids:
            prefs_query = (
                select(UserPreferencesModel.user_id)
                .where(UserPreferencesModel.user_id.in_(followed_owner_ids))
                .where(
                    cast(
                        UserPreferencesModel.display_settings['collection_sharing']['enabled'].astext,
                        String
                    ) == 'true'
                )
            )
            prefs_result = await self.session.execute(prefs_query)
            users_with_sharing = {user_id for user_id, in prefs_result.all()}

        result_map: Dict[UUID, List[Tuple[UUID, int]]] = {}
        for pressing_id, owner_dict in owners_by_pressing.items():
            result_list: List[Tuple[UUID, int]] = []

            if viewer_user_id in owner_dict:
                result_list.append((viewer_user_id, owner_dict[viewer_user_id]))

            if followed_user_ids:
                for user_id in followed_user_ids:
                    if user_id == viewer_user_id:
                        continue
                    if user_id in owner_dict and user_id in users_with_sharing:
                        result_list.append((user_id, owner_dict[user_id]))

            result_map[pressing_id] = result_list

        return result_map

    async def get_owners_for_album(
        self,
        album_id: UUID,
        viewer_user_id: UUID,
        followed_user_ids: List[UUID]
    ) -> List[Tuple[UUID, int]]:
        """
        Get owners of a specific album (any pressing) (viewer + followed users with sharing enabled).

        Only returns users who:
        1. Own at least one pressing of this album
        2. Have collection sharing enabled (for followed users)
        3. Are either the viewer themselves OR are in the followed_user_ids list

        Args:
            album_id: The album to check ownership for (any pressing)
            viewer_user_id: The current user viewing (always included if they own it)
            followed_user_ids: List of user IDs that viewer follows

        Returns:
            List of tuples (user_id, copy_count) where copy_count is the total
            number of pressings of this album owned by that user
        """
        # Query to get owners with copy counts (across all pressings of this album)
        query = (
            select(
                CollectionItemModel.user_id,
                func.count(CollectionItemModel.id).label('copy_count')
            )
            .join(PressingModel, CollectionItemModel.pressing_id == PressingModel.id)
            .where(PressingModel.album_id == album_id)
            .group_by(CollectionItemModel.user_id)
        )

        # Get all owners
        result = await self.session.execute(query)
        all_owners = result.all()

        if not all_owners:
            return []

        # Separate viewer's ownership from others
        owner_dict = {user_id: copy_count for user_id, copy_count in all_owners}

        # Build result list
        result_list = []

        # Always include viewer if they own it
        if viewer_user_id in owner_dict:
            result_list.append((viewer_user_id, owner_dict[viewer_user_id]))

        # Check followed users
        if followed_user_ids:
            # Get user IDs from owner_dict that are in followed_user_ids
            followed_owners = [uid for uid in followed_user_ids if uid in owner_dict]

            if followed_owners:
                # Check which of these followed owners have sharing enabled
                prefs_query = (
                    select(UserPreferencesModel.user_id)
                    .where(UserPreferencesModel.user_id.in_(followed_owners))
                    .where(
                        cast(
                            UserPreferencesModel.display_settings['collection_sharing']['enabled'].astext,
                            String
                        ) == 'true'
                    )
                )

                prefs_result = await self.session.execute(prefs_query)
                users_with_sharing = {user_id for user_id, in prefs_result.all()}

                # Add followed users with sharing enabled
                for user_id in followed_owners:
                    if user_id in users_with_sharing:
                        result_list.append((user_id, owner_dict[user_id]))

        return result_list

    async def get_owners_for_albums(
        self,
        album_ids: List[UUID],
        viewer_user_id: UUID,
        followed_user_ids: List[UUID]
    ) -> Dict[UUID, List[Tuple[UUID, int]]]:
        """
        Get owners for multiple albums (viewer + followed users with sharing enabled).

        Returns a dictionary keyed by album_id with ordered owners.
        """
        if not album_ids:
            return {}

        query = (
            select(
                PressingModel.album_id,
                CollectionItemModel.user_id,
                func.count(CollectionItemModel.id).label('copy_count')
            )
            .join(PressingModel, CollectionItemModel.pressing_id == PressingModel.id)
            .where(PressingModel.album_id.in_(album_ids))
            .group_by(PressingModel.album_id, CollectionItemModel.user_id)
        )

        result = await self.session.execute(query)
        all_owners = result.all()

        if not all_owners:
            return {}

        owners_by_album: Dict[UUID, Dict[UUID, int]] = {}
        for album_id, user_id, copy_count in all_owners:
            owners_by_album.setdefault(album_id, {})[user_id] = copy_count

        followed_set = set(followed_user_ids or [])
        followed_owner_ids = {
            user_id
            for owner_dict in owners_by_album.values()
            for user_id in owner_dict.keys()
            if user_id in followed_set
        }

        users_with_sharing: set[UUID] = set()
        if followed_owner_ids:
            prefs_query = (
                select(UserPreferencesModel.user_id)
                .where(UserPreferencesModel.user_id.in_(followed_owner_ids))
                .where(
                    cast(
                        UserPreferencesModel.display_settings['collection_sharing']['enabled'].astext,
                        String
                    ) == 'true'
                )
            )
            prefs_result = await self.session.execute(prefs_query)
            users_with_sharing = {user_id for user_id, in prefs_result.all()}

        result_map: Dict[UUID, List[Tuple[UUID, int]]] = {}
        for album_id, owner_dict in owners_by_album.items():
            result_list: List[Tuple[UUID, int]] = []

            if viewer_user_id in owner_dict:
                result_list.append((viewer_user_id, owner_dict[viewer_user_id]))

            if followed_user_ids:
                for user_id in followed_user_ids:
                    if user_id == viewer_user_id:
                        continue
                    if user_id in owner_dict and user_id in users_with_sharing:
                        result_list.append((user_id, owner_dict[user_id]))

            result_map[album_id] = result_list

        return result_map
