"""Discogs OAuth repository port interfaces."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities import DiscogsOAuthRequest, DiscogsUserToken


class DiscogsOAuthRequestRepository(ABC):
    """Repository interface for Discogs OAuth request tokens."""

    @abstractmethod
    async def create(self, request: DiscogsOAuthRequest) -> DiscogsOAuthRequest:
        pass

    @abstractmethod
    async def get_by_token(self, request_token: str) -> Optional[DiscogsOAuthRequest]:
        pass

    @abstractmethod
    async def delete(self, request_id: UUID) -> None:
        pass


class DiscogsUserTokenRepository(ABC):
    """Repository interface for Discogs OAuth access tokens."""

    @abstractmethod
    async def upsert(self, token: DiscogsUserToken) -> DiscogsUserToken:
        pass

    @abstractmethod
    async def get_by_user(self, user_id: UUID) -> Optional[DiscogsUserToken]:
        pass

    @abstractmethod
    async def delete_by_user(self, user_id: UUID) -> None:
        pass
