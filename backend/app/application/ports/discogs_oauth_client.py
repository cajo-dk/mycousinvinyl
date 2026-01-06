"""Port interface for Discogs OAuth and user collection API."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class DiscogsOAuthClient(ABC):
    """Abstract client for Discogs OAuth and user collection API."""

    @abstractmethod
    async def get_request_token(self, callback_url: str) -> Dict[str, str]:
        """Request a temporary OAuth token."""
        raise NotImplementedError

    @abstractmethod
    async def get_access_token(
        self,
        request_token: str,
        request_secret: str,
        verifier: str,
    ) -> Dict[str, str]:
        """Exchange a request token for an access token."""
        raise NotImplementedError

    @abstractmethod
    async def get_identity(self, access_token: str, access_secret: str) -> Dict[str, Any]:
        """Fetch Discogs identity information for a user."""
        raise NotImplementedError

    @abstractmethod
    async def get_collection_items(
        self,
        username: str,
        folder_id: int,
        page: int,
        per_page: int,
        access_token: str,
        access_secret: str | None,
    ) -> Dict[str, Any]:
        """Fetch collection items for a user by folder."""
        raise NotImplementedError

    @abstractmethod
    async def get_collection_fields(
        self,
        username: str,
        access_token: str,
        access_secret: str | None,
    ) -> Dict[str, Any]:
        """Fetch collection field definitions for a user."""
        raise NotImplementedError

    @abstractmethod
    async def get_collection_instance(
        self,
        username: str,
        folder_id: int,
        release_id: int,
        instance_id: int,
        access_token: str,
        access_secret: str | None,
    ) -> Dict[str, Any]:
        """Fetch collection instance details for a release."""
        raise NotImplementedError
