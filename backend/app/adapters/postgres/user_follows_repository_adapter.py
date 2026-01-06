"""
SQLAlchemy user follows repository implementation.
"""

from typing import List
from uuid import UUID
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.application.ports.user_follows_repository import UserFollowsRepository
from app.adapters.postgres.models import UserFollowsModel


class UserFollowsRepositoryAdapter(UserFollowsRepository):
    """SQLAlchemy implementation of user follows repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

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
        if follower_id == followed_id:
            raise ValueError("Cannot follow yourself")

        follow = UserFollowsModel(
            follower_user_id=follower_id,
            followed_user_id=followed_id
        )

        try:
            self.session.add(follow)
            await self.session.flush()
        except IntegrityError as e:
            if 'no_self_follow' in str(e):
                raise ValueError("Cannot follow yourself") from e
            elif 'PRIMARY KEY' in str(e) or 'duplicate key' in str(e):
                raise ValueError(f"Already following user {followed_id}") from e
            raise

    async def remove_follow(self, follower_id: UUID, followed_id: UUID) -> None:
        """
        Remove a follow relationship.

        Args:
            follower_id: UUID of the user who is following
            followed_id: UUID of the user being unfollowed

        Note:
            Does not raise an error if relationship doesn't exist (idempotent)
        """
        stmt = delete(UserFollowsModel).where(
            UserFollowsModel.follower_user_id == follower_id,
            UserFollowsModel.followed_user_id == followed_id
        )

        await self.session.execute(stmt)

    async def get_follows(self, follower_id: UUID) -> List[UUID]:
        """
        Get list of user IDs that follower_id follows.

        Args:
            follower_id: UUID of the user whose follows to retrieve

        Returns:
            List of user IDs (UUIDs) that the follower follows
        """
        stmt = (
            select(UserFollowsModel.followed_user_id)
            .where(UserFollowsModel.follower_user_id == follower_id)
            .order_by(UserFollowsModel.created_at)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_follow_count(self, follower_id: UUID) -> int:
        """
        Get count of users that follower_id follows.

        Args:
            follower_id: UUID of the user

        Returns:
            Number of users being followed
        """
        stmt = (
            select(func.count())
            .select_from(UserFollowsModel)
            .where(UserFollowsModel.follower_user_id == follower_id)
        )

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def is_following(self, follower_id: UUID, followed_id: UUID) -> bool:
        """
        Check if follower_id follows followed_id.

        Args:
            follower_id: UUID of the potential follower
            followed_id: UUID of the potential followed user

        Returns:
            True if the follow relationship exists, False otherwise
        """
        stmt = (
            select(UserFollowsModel)
            .where(
                UserFollowsModel.follower_user_id == follower_id,
                UserFollowsModel.followed_user_id == followed_id
            )
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
