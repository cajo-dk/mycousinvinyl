"""
Collection Sharing Service.

Business logic for managing user follows and collection sharing visibility.
Enforces privacy rules and follow limits.
"""

from typing import List, Dict
from uuid import UUID

from app.application.ports.unit_of_work import UnitOfWork
from app.domain.value_objects import UserOwnerInfo


class CollectionSharingService:
    """Service for managing collection sharing and user follows."""

    MAX_FOLLOWS = 3

    def __init__(self, uow: UnitOfWork):
        """
        Initialize the service.

        Args:
            uow: Unit of Work for database transactions
        """
        self.uow = uow

    async def add_follow(self, user_id: UUID, followed_user_id: UUID) -> None:
        """
        Add a follow relationship.

        Args:
            user_id: UUID of the user who is following
            followed_user_id: UUID of the user being followed

        Raises:
            ValueError: If validation fails (self-follow, max follows exceeded, user not found)
        """
        # Validate: Cannot follow yourself
        if user_id == followed_user_id:
            raise ValueError("Cannot follow yourself")

        async with self.uow:
            # Check if already following
            is_following = await self.uow.user_follows_repository.is_following(
                user_id, followed_user_id
            )
            if is_following:
                raise ValueError(f"Already following user {followed_user_id}")

            # Check follow count limit
            follow_count = await self.uow.user_follows_repository.get_follow_count(user_id)
            if follow_count >= self.MAX_FOLLOWS:
                raise ValueError(f"Cannot follow more than {self.MAX_FOLLOWS} users")

            # Validate that followed user exists and has sharing enabled
            followed_prefs = await self.uow.preferences_repository.get(followed_user_id)
            if not followed_prefs:
                raise ValueError(f"User {followed_user_id} not found")

            sharing_settings = followed_prefs.get_collection_sharing_settings()
            if not sharing_settings.enabled:
                raise ValueError(f"User {followed_user_id} has not enabled collection sharing")

            # Add the follow relationship
            await self.uow.user_follows_repository.add_follow(user_id, followed_user_id)
            await self.uow.commit()

    async def remove_follow(self, user_id: UUID, followed_user_id: UUID) -> None:
        """
        Remove a follow relationship.

        Args:
            user_id: UUID of the user who is following
            followed_user_id: UUID of the user being unfollowed

        Note:
            Does not raise an error if relationship doesn't exist (idempotent)
        """
        async with self.uow:
            await self.uow.user_follows_repository.remove_follow(user_id, followed_user_id)
            await self.uow.commit()

    async def get_follows(self, user_id: UUID) -> List[UserOwnerInfo]:
        """
        Get list of users that user_id follows with their icon settings.

        Args:
            user_id: UUID of the user whose follows to retrieve

        Returns:
            List of UserOwnerInfo for followed users with sharing enabled
        """
        async with self.uow:
            # Get list of followed user IDs
            followed_ids = await self.uow.user_follows_repository.get_follows(user_id)

            if not followed_ids:
                return []

            # Get preferences for followed users
            prefs_dict = await self.uow.preferences_repository.get_many_by_user_ids(
                followed_ids
            )

            # Build UserOwnerInfo for each followed user
            result = []
            for followed_id in followed_ids:
                prefs = prefs_dict.get(followed_id)
                if not prefs:
                    continue  # Skip if preferences not found

                sharing_settings = prefs.get_collection_sharing_settings()
                if not sharing_settings.enabled:
                    continue  # Skip if sharing disabled

                user_profile = prefs.get_user_profile()
                display_name = user_profile.get("display_name", "Unknown User")
                first_name = user_profile.get("first_name", "U")

                result.append(
                    UserOwnerInfo(
                        user_id=followed_id,
                        display_name=display_name,
                        first_name=first_name,
                        icon_type=sharing_settings.icon_type,
                        icon_fg_color=sharing_settings.icon_fg_color,
                        icon_bg_color=sharing_settings.icon_bg_color,
                        copy_count=1,  # Not relevant for follows list, but must be >= 1
                    )
                )

            return result

    async def get_owners_for_pressing(
        self,
        user_id: UUID,
        pressing_id: UUID,
        alternate_user_ids: List[UUID] | None = None
    ) -> List[UserOwnerInfo]:
        """
        Get owners of a specific pressing (current user + followed users with sharing enabled).

        Args:
            user_id: UUID of the current user viewing
            pressing_id: UUID of the pressing to check ownership for

        Returns:
            List of UserOwnerInfo (max 4: current user + 3 followed users)
        """
        viewer_aliases = [user_id] + [uid for uid in (alternate_user_ids or []) if uid != user_id]

        async with self.uow:
            # Get followed user IDs
            followed_ids = await self.uow.user_follows_repository.get_follows(user_id)

            # Get owners (returns list of tuples: (user_id, copy_count))
            owners = await self.uow.collection_repository.get_owners_for_pressing(
                pressing_id, user_id, followed_ids
            )
            if not owners and alternate_user_ids:
                for alt_id in alternate_user_ids:
                    if alt_id == user_id:
                        continue
                    owners = await self.uow.collection_repository.get_owners_for_pressing(
                        pressing_id, alt_id, followed_ids
                    )
                    if owners:
                        break

            if not owners:
                return []

            # Get all user IDs from owners
            owner_user_ids = [owner_id for owner_id, _ in owners]

            # Get preferences for all owners
            prefs_dict = await self.uow.preferences_repository.get_many_by_user_ids(
                owner_user_ids
            )

            # Build UserOwnerInfo for each owner
            result = []
            for owner_id, copy_count in owners:
                prefs = prefs_dict.get(owner_id)
                if not prefs and owner_id in viewer_aliases:
                    prefs = await self.uow.preferences_repository.get_or_create_default(owner_id)
                    prefs_dict[owner_id] = prefs
                if not prefs:
                    continue  # Skip if preferences not found

                # For current user, always include (even if sharing disabled)
                # For followed users, only include if sharing enabled
                sharing_settings = prefs.get_collection_sharing_settings()
                is_viewer = owner_id in viewer_aliases
                if not is_viewer and not sharing_settings.enabled:
                    continue

                user_profile = prefs.get_user_profile()
                display_name = user_profile.get("display_name", "Unknown User")
                first_name = user_profile.get("first_name", "U")

                result.append(
                    UserOwnerInfo(
                        user_id=user_id if is_viewer else owner_id,
                        display_name=display_name,
                        first_name=first_name,
                        icon_type=sharing_settings.icon_type,
                        icon_fg_color=sharing_settings.icon_fg_color,
                        icon_bg_color=sharing_settings.icon_bg_color,
                        copy_count=copy_count,
                    )
                )

            return result

    async def get_owners_for_pressings(
        self,
        user_id: UUID,
        pressing_ids: List[UUID],
        alternate_user_ids: List[UUID] | None = None
    ) -> Dict[UUID, List[UserOwnerInfo]]:
        """
        Get owners for multiple pressings (current user + followed users with sharing enabled).

        Returns a dictionary keyed by pressing_id.
        """
        if not pressing_ids:
            return {}

        viewer_aliases = [user_id] + [uid for uid in (alternate_user_ids or []) if uid != user_id]

        async with self.uow:
            followed_ids = await self.uow.user_follows_repository.get_follows(user_id)

            owners_map = await self.uow.collection_repository.get_owners_for_pressings(
                pressing_ids, user_id, followed_ids
            )

            if alternate_user_ids:
                remaining_ids = [
                    pid for pid in pressing_ids
                    if not owners_map.get(pid)
                ]
                for alt_id in alternate_user_ids:
                    if not remaining_ids:
                        break
                    if alt_id == user_id:
                        continue
                    alt_map = await self.uow.collection_repository.get_owners_for_pressings(
                        remaining_ids, alt_id, followed_ids
                    )
                    for pressing_id, owners in alt_map.items():
                        if owners:
                            owners_map[pressing_id] = owners
                    remaining_ids = [
                        pid for pid in remaining_ids
                        if not owners_map.get(pid)
                    ]

            owner_user_ids: List[UUID] = []
            for owners in owners_map.values():
                owner_user_ids.extend([owner_id for owner_id, _ in owners])

            prefs_dict = await self.uow.preferences_repository.get_many_by_user_ids(
                list(set(owner_user_ids))
            )

            for owner_id in viewer_aliases:
                if owner_id in owner_user_ids and owner_id not in prefs_dict:
                    prefs = await self.uow.preferences_repository.get_or_create_default(owner_id)
                    prefs_dict[owner_id] = prefs

            result: Dict[UUID, List[UserOwnerInfo]] = {}
            for pressing_id in pressing_ids:
                owners = owners_map.get(pressing_id, [])
                owners_response: List[UserOwnerInfo] = []

                for owner_id, copy_count in owners:
                    prefs = prefs_dict.get(owner_id)
                    if not prefs:
                        continue

                    sharing_settings = prefs.get_collection_sharing_settings()
                    is_viewer = owner_id in viewer_aliases
                    if not is_viewer and not sharing_settings.enabled:
                        continue

                    user_profile = prefs.get_user_profile()
                    display_name = user_profile.get("display_name", "Unknown User")
                    first_name = user_profile.get("first_name", "U")

                    owners_response.append(
                        UserOwnerInfo(
                            user_id=user_id if is_viewer else owner_id,
                            display_name=display_name,
                            first_name=first_name,
                            icon_type=sharing_settings.icon_type,
                            icon_fg_color=sharing_settings.icon_fg_color,
                            icon_bg_color=sharing_settings.icon_bg_color,
                            copy_count=copy_count,
                        )
                    )

                result[pressing_id] = owners_response

            return result

    async def get_owners_for_album(
        self,
        user_id: UUID,
        album_id: UUID,
        alternate_user_ids: List[UUID] | None = None
    ) -> List[UserOwnerInfo]:
        """
        Get owners of a specific album (any pressing) (current user + followed users with sharing enabled).

        Args:
            user_id: UUID of the current user viewing
            album_id: UUID of the album to check ownership for

        Returns:
            List of UserOwnerInfo (max 4: current user + 3 followed users)
        """
        viewer_aliases = [user_id] + [uid for uid in (alternate_user_ids or []) if uid != user_id]

        async with self.uow:
            # Get followed user IDs
            followed_ids = await self.uow.user_follows_repository.get_follows(user_id)

            # Get owners (returns list of tuples: (user_id, copy_count))
            owners = await self.uow.collection_repository.get_owners_for_album(
                album_id, user_id, followed_ids
            )
            if not owners and alternate_user_ids:
                for alt_id in alternate_user_ids:
                    if alt_id == user_id:
                        continue
                    owners = await self.uow.collection_repository.get_owners_for_album(
                        album_id, alt_id, followed_ids
                    )
                    if owners:
                        break

            if not owners:
                return []

            # Get all user IDs from owners
            owner_user_ids = [owner_id for owner_id, _ in owners]

            # Get preferences for all owners
            prefs_dict = await self.uow.preferences_repository.get_many_by_user_ids(
                owner_user_ids
            )

            # Build UserOwnerInfo for each owner
            result = []
            for owner_id, copy_count in owners:
                prefs = prefs_dict.get(owner_id)
                if not prefs and owner_id in viewer_aliases:
                    prefs = await self.uow.preferences_repository.get_or_create_default(owner_id)
                    prefs_dict[owner_id] = prefs
                if not prefs:
                    continue  # Skip if preferences not found

                # For current user, always include (even if sharing disabled)
                # For followed users, only include if sharing enabled
                sharing_settings = prefs.get_collection_sharing_settings()
                is_viewer = owner_id in viewer_aliases
                if not is_viewer and not sharing_settings.enabled:
                    continue

                user_profile = prefs.get_user_profile()
                display_name = user_profile.get("display_name", "Unknown User")
                first_name = user_profile.get("first_name", "U")

                result.append(
                    UserOwnerInfo(
                        user_id=user_id if is_viewer else owner_id,
                        display_name=display_name,
                        first_name=first_name,
                        icon_type=sharing_settings.icon_type,
                        icon_fg_color=sharing_settings.icon_fg_color,
                        icon_bg_color=sharing_settings.icon_bg_color,
                        copy_count=copy_count,
                    )
                )

            return result

    async def get_owners_for_albums(
        self,
        user_id: UUID,
        album_ids: List[UUID],
        alternate_user_ids: List[UUID] | None = None
    ) -> Dict[UUID, List[UserOwnerInfo]]:
        """
        Get owners for multiple albums (current user + followed users with sharing enabled).

        Returns a dictionary keyed by album_id.
        """
        if not album_ids:
            return {}

        viewer_aliases = [user_id] + [uid for uid in (alternate_user_ids or []) if uid != user_id]

        async with self.uow:
            followed_ids = await self.uow.user_follows_repository.get_follows(user_id)

            owners_map = await self.uow.collection_repository.get_owners_for_albums(
                album_ids, user_id, followed_ids
            )

            if alternate_user_ids:
                remaining_ids = [
                    album_id for album_id in album_ids
                    if not owners_map.get(album_id)
                ]
                for alt_id in alternate_user_ids:
                    if not remaining_ids:
                        break
                    if alt_id == user_id:
                        continue
                    alt_map = await self.uow.collection_repository.get_owners_for_albums(
                        remaining_ids, alt_id, followed_ids
                    )
                    for album_id, owners in alt_map.items():
                        if owners:
                            owners_map[album_id] = owners
                    remaining_ids = [
                        album_id for album_id in remaining_ids
                        if not owners_map.get(album_id)
                    ]

            owner_user_ids: List[UUID] = []
            for owners in owners_map.values():
                owner_user_ids.extend([owner_id for owner_id, _ in owners])

            prefs_dict = await self.uow.preferences_repository.get_many_by_user_ids(
                list(set(owner_user_ids))
            )

            for owner_id in viewer_aliases:
                if owner_id in owner_user_ids and owner_id not in prefs_dict:
                    prefs = await self.uow.preferences_repository.get_or_create_default(owner_id)
                    prefs_dict[owner_id] = prefs

            result: Dict[UUID, List[UserOwnerInfo]] = {}
            for album_id in album_ids:
                owners = owners_map.get(album_id, [])
                owners_response: List[UserOwnerInfo] = []

                for owner_id, copy_count in owners:
                    prefs = prefs_dict.get(owner_id)
                    if not prefs:
                        continue

                    sharing_settings = prefs.get_collection_sharing_settings()
                    is_viewer = owner_id in viewer_aliases
                    if not is_viewer and not sharing_settings.enabled:
                        continue

                    user_profile = prefs.get_user_profile()
                    display_name = user_profile.get("display_name", "Unknown User")
                    first_name = user_profile.get("first_name", "U")

                    owners_response.append(
                        UserOwnerInfo(
                            user_id=user_id if is_viewer else owner_id,
                            display_name=display_name,
                            first_name=first_name,
                            icon_type=sharing_settings.icon_type,
                            icon_fg_color=sharing_settings.icon_fg_color,
                            icon_bg_color=sharing_settings.icon_bg_color,
                            copy_count=copy_count,
                        )
                    )

                result[album_id] = owners_response

            return result

    async def search_users(
        self, query: str, current_user_id: UUID, limit: int = 10
    ) -> List[UserOwnerInfo]:
        """
        Search for users by name (for autocomplete in user search).

        Only returns users with collection sharing enabled. Excludes current user.

        Args:
            query: Search query string (case-insensitive partial match)
            current_user_id: UUID of the current user (to exclude from results)
            limit: Maximum number of results to return (default 10)

        Returns:
            List of UserOwnerInfo for matching users with sharing enabled
        """
        async with self.uow:
            # Search users by name (only returns users with sharing enabled)
            prefs_list = await self.uow.preferences_repository.search_users_by_name(
                query, limit=limit + 1  # Get one extra to account for filtering out current user
            )

            # Build UserOwnerInfo for each matching user
            result = []
            for prefs in prefs_list:
                # Skip current user
                if prefs.user_id == current_user_id:
                    continue

                sharing_settings = prefs.get_collection_sharing_settings()
                if not sharing_settings.enabled:
                    continue  # Should already be filtered, but double-check

                user_profile = prefs.get_user_profile()
                display_name = user_profile.get("display_name", "Unknown User")
                first_name = user_profile.get("first_name", "U")

                result.append(
                    UserOwnerInfo(
                        user_id=prefs.user_id,
                        display_name=display_name,
                        first_name=first_name,
                        icon_type=sharing_settings.icon_type,
                        icon_fg_color=sharing_settings.icon_fg_color,
                        icon_bg_color=sharing_settings.icon_bg_color,
                        copy_count=1,  # Not relevant for search results, but must be >= 1
                    )
                )

                if len(result) >= limit:
                    break

            return result
