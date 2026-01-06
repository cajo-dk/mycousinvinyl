"""
Repository port for managing user follow relationships.

This port defines the interface for storing and retrieving user follow data,
enabling the collection sharing feature.
"""

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID


class UserFollowsRepository(ABC):
    """Repository interface for managing user follow relationships."""

    @abstractmethod
    async def add_follow(self, follower_id: UUID, followed_id: UUID) -> None:
        """
        Add a follow relationship.

        Args:
            follower_id: UUID of the user who is following
            followed_id: UUID of the user being followed

        Raises:
            ValueError: If follower_id == followed_id (self-follow)
            IntegrityError: If follow relationship already exists
        """
        pass

    @abstractmethod
    async def remove_follow(self, follower_id: UUID, followed_id: UUID) -> None:
        """
        Remove a follow relationship.

        Args:
            follower_id: UUID of the user who is following
            followed_id: UUID of the user being followed

        Note:
            Does not raise an error if relationship doesn't exist (idempotent)
        """
        pass

    @abstractmethod
    async def get_follows(self, follower_id: UUID) -> List[UUID]:
        """
        Get list of user IDs that follower_id follows.

        Args:
            follower_id: UUID of the user whose follows to retrieve

        Returns:
            List of user IDs (UUIDs) that the follower follows
        """
        pass

    @abstractmethod
    async def get_follow_count(self, follower_id: UUID) -> int:
        """
        Get count of users that follower_id follows.

        Args:
            follower_id: UUID of the user

        Returns:
            Number of users being followed
        """
        pass

    @abstractmethod
    async def is_following(self, follower_id: UUID, followed_id: UUID) -> bool:
        """
        Check if follower_id follows followed_id.

        Args:
            follower_id: UUID of the potential follower
            followed_id: UUID of the potential followed user

        Returns:
            True if the follow relationship exists, False otherwise
        """
        pass
