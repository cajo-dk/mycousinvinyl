"""
Service for Discogs OAuth authentication and token management.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4
from urllib.parse import urlparse

import httpx

from app.application.ports.unit_of_work import UnitOfWork
from app.application.ports.discogs_oauth_client import DiscogsOAuthClient
from app.domain.entities import DiscogsOAuthRequest, DiscogsUserToken


class DiscogsOAuthService:
    def __init__(
        self,
        uow: UnitOfWork,
        oauth_client: DiscogsOAuthClient,
        authorize_url: str,
        callback_url: str,
        frontend_base_url: str,
    ):
        self.uow = uow
        self._client = oauth_client
        self._authorize_url = authorize_url.rstrip("/")
        self._callback_url = callback_url
        self._frontend_base_url = frontend_base_url.rstrip("/")

    async def start_authorization(self, user_id: UUID, redirect_uri: Optional[str]) -> str:
        state = uuid4().hex
        redirect_target = self._resolve_redirect_uri(redirect_uri)
        callback_with_state = self._build_callback_url(state)
        token_data = await self._client.get_request_token(callback_with_state)
        request_token = token_data.get("oauth_token")
        request_secret = token_data.get("oauth_token_secret")

        if not request_token or not request_secret:
            raise ValueError("Failed to obtain Discogs request token")

        request = DiscogsOAuthRequest(
            user_id=user_id,
            request_token=request_token,
            request_secret=request_secret,
            state=state,
            redirect_uri=redirect_target,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )

        async with self.uow:
            await self.uow.discogs_oauth_request_repository.create(request)
            await self.uow.commit()

        return f"{self._authorize_url}?oauth_token={request_token}"

    async def complete_authorization(
        self,
        request_token: str,
        verifier: str,
        state: Optional[str],
    ) -> str:
        async with self.uow:
            request = await self.uow.discogs_oauth_request_repository.get_by_token(request_token)
            if not request:
                raise ValueError("Discogs OAuth request not found")
            if request.expires_at and request.expires_at < datetime.utcnow():
                await self.uow.discogs_oauth_request_repository.delete(request.id)
                await self.uow.commit()
                raise ValueError("Discogs OAuth request expired")
            if state and state != request.state:
                raise ValueError("Discogs OAuth state mismatch")

        token_data = await self._client.get_access_token(
            request_token=request_token,
            request_secret=request.request_secret,
            verifier=verifier,
        )
        access_token = token_data.get("oauth_token")
        access_secret = token_data.get("oauth_token_secret")
        if not access_token or not access_secret:
            raise ValueError("Failed to obtain Discogs access token")

        identity = await self._client.get_identity(access_token, access_secret)
        username = identity.get("username")
        if not username:
            raise ValueError("Discogs identity missing username")

        token = DiscogsUserToken(
            user_id=request.user_id,
            access_token=access_token,
            access_secret=access_secret,
            discogs_username=username,
            last_synced_at=None,
        )

        async with self.uow:
            await self.uow.discogs_user_token_repository.upsert(token)
            await self.uow.discogs_oauth_request_repository.delete(request.id)
            await self.uow.commit()

        return request.redirect_uri

    async def get_status(self, user_id: UUID) -> Optional[DiscogsUserToken]:
        async with self.uow:
            return await self.uow.discogs_user_token_repository.get_by_user(user_id)

    async def disconnect(self, user_id: UUID) -> None:
        async with self.uow:
            await self.uow.discogs_user_token_repository.delete_by_user(user_id)
            await self.uow.commit()

    def _build_callback_url(self, state: str) -> str:
        return str(httpx.URL(self._callback_url, params={"state": state}))

    def _resolve_redirect_uri(self, redirect_uri: Optional[str]) -> str:
        if not redirect_uri:
            return f"{self._frontend_base_url}/profile"

        parsed = urlparse(redirect_uri)
        if parsed.scheme and parsed.netloc:
            base = urlparse(self._frontend_base_url)
            if parsed.scheme == base.scheme and parsed.netloc == base.netloc:
                return redirect_uri
            return f"{self._frontend_base_url}/profile"

        if redirect_uri.startswith("/"):
            return f"{self._frontend_base_url}{redirect_uri}"

        return f"{self._frontend_base_url}/profile"
