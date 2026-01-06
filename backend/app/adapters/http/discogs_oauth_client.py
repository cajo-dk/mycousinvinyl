"""
Discogs OAuth 1.0a client with PAT fallback for user collection endpoints.
"""

import asyncio
import time
from typing import Dict, Any, Optional
from urllib.parse import parse_qs, urlencode

import httpx
from oauthlib.oauth1 import Client

from app.application.ports.discogs_oauth_client import DiscogsOAuthClient


class RateLimiter:
    def __init__(self, max_per_minute: int):
        self._min_interval = 60.0 / max_per_minute if max_per_minute > 0 else 0.0
        self._lock = asyncio.Lock()
        self._last_request = 0.0

    async def wait(self) -> None:
        if self._min_interval <= 0:
            return
        async with self._lock:
            now = time.monotonic()
            delay = self._min_interval - (now - self._last_request)
            if delay > 0:
                await asyncio.sleep(delay)
            self._last_request = time.monotonic()


_limiter_cache: Dict[int, RateLimiter] = {}


def _get_shared_limiter(max_per_minute: int) -> RateLimiter:
    limiter = _limiter_cache.get(max_per_minute)
    if limiter:
        return limiter
    limiter = RateLimiter(max_per_minute)
    _limiter_cache[max_per_minute] = limiter
    return limiter


class DiscogsOAuthClientAdapter(DiscogsOAuthClient):
    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        api_base_url: str = "https://api.discogs.com",
        authorize_url: str = "https://www.discogs.com/oauth/authorize",
        user_agent: str = "MyCousinVinyl/1.0",
        timeout_seconds: float = 10.0,
        rate_limit_per_minute: int = 55,
        backoff_seconds: int = 20,
    ):
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._api_base_url = api_base_url.rstrip("/")
        self._authorize_url = authorize_url.rstrip("/")
        self._user_agent = user_agent
        self._timeout = timeout_seconds
        self._limiter = _get_shared_limiter(rate_limit_per_minute)
        self._backoff_seconds = backoff_seconds

    async def get_request_token(self, callback_url: str) -> Dict[str, str]:
        url = f"{self._api_base_url}/oauth/request_token"
        body = {"oauth_callback": callback_url}
        response_text = await self._signed_form_request(
            url,
            body=body,
            token=None,
            token_secret=None,
        )
        parsed = parse_qs(response_text)
        return {
            "oauth_token": parsed.get("oauth_token", [""])[0],
            "oauth_token_secret": parsed.get("oauth_token_secret", [""])[0],
        }

    async def get_access_token(
        self,
        request_token: str,
        request_secret: str,
        verifier: str,
    ) -> Dict[str, str]:
        url = f"{self._api_base_url}/oauth/access_token"
        body = {"oauth_verifier": verifier}
        response_text = await self._signed_form_request(
            url,
            body=body,
            token=request_token,
            token_secret=request_secret,
        )
        parsed = parse_qs(response_text)
        return {
            "oauth_token": parsed.get("oauth_token", [""])[0],
            "oauth_token_secret": parsed.get("oauth_token_secret", [""])[0],
        }

    async def get_identity(self, access_token: str, access_secret: str) -> Dict[str, Any]:
        url = f"{self._api_base_url}/oauth/identity"
        return await self._signed_json_request(
            url,
            token=access_token,
            token_secret=access_secret,
        )

    async def get_collection_items(
        self,
        username: str,
        folder_id: int,
        page: int,
        per_page: int,
        access_token: str,
        access_secret: str | None,
    ) -> Dict[str, Any]:
        url = f"{self._api_base_url}/users/{username}/collection/folders/{folder_id}/releases"
        params = {"page": page, "per_page": per_page}
        if access_secret:
            return await self._signed_json_request(
                url,
                params=params,
                token=access_token,
                token_secret=access_secret,
            )
        return await self._token_json_request(url, params=params, token=access_token)

    async def get_collection_fields(
        self,
        username: str,
        access_token: str,
        access_secret: str | None,
    ) -> Dict[str, Any]:
        url = f"{self._api_base_url}/users/{username}/collection/fields"
        if access_secret:
            return await self._signed_json_request(
                url,
                token=access_token,
                token_secret=access_secret,
            )
        return await self._token_json_request(url, params=None, token=access_token)

    async def get_collection_instance(
        self,
        username: str,
        folder_id: int,
        release_id: int,
        instance_id: int,
        access_token: str,
        access_secret: str | None,
    ) -> Dict[str, Any]:
        url = (
            f"{self._api_base_url}/users/{username}/collection/folders/{folder_id}"
            f"/releases/{release_id}/instances/{instance_id}"
        )
        if access_secret:
            return await self._signed_json_request(
                url,
                token=access_token,
                token_secret=access_secret,
            )
        return await self._token_json_request(url, params=None, token=access_token)

    async def _signed_form_request(
        self,
        url: str,
        body: Dict[str, str],
        token: str | None,
        token_secret: str | None,
    ) -> str:
        client = Client(
            self._consumer_key,
            client_secret=self._consumer_secret,
            resource_owner_key=token,
            resource_owner_secret=token_secret,
            signature_method="HMAC-SHA1",
        )
        body_str = urlencode(body)
        signed_url, headers, signed_body = client.sign(
            url,
            http_method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": self._user_agent,
            },
            body=body_str,
        )
        response = await self._request_with_retry(
            method="POST",
            url=signed_url,
            headers=headers,
            content=signed_body,
        )
        return response.text

    async def _signed_json_request(
        self,
        url: str,
        params: Dict[str, Any] | None = None,
        token: str | None = None,
        token_secret: str | None = None,
    ) -> Dict[str, Any]:
        client = Client(
            self._consumer_key,
            client_secret=self._consumer_secret,
            resource_owner_key=token,
            resource_owner_secret=token_secret,
            signature_method="HMAC-SHA1",
        )
        if params:
            url = str(httpx.URL(url, params=params))
        signed_url, headers, _ = client.sign(
            url,
            http_method="GET",
            headers={"Accept": "application/json", "User-Agent": self._user_agent},
        )
        response = await self._request_with_retry(
            method="GET",
            url=signed_url,
            headers=headers,
        )
        return response.json()

    async def _token_json_request(
        self,
        url: str,
        params: Dict[str, Any] | None,
        token: str,
    ) -> Dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "User-Agent": self._user_agent,
            "Authorization": f"Discogs token={token}",
        }
        response = await self._request_with_retry(
            method="GET",
            url=url,
            headers=headers,
            params=params,
        )
        return response.json()

    def _resolve_backoff_seconds(self, response: httpx.Response) -> int:
        retry_after = response.headers.get("Retry-After")
        delay: Optional[int] = None
        if retry_after:
            try:
                delay = int(retry_after)
            except ValueError:
                delay = None
        if delay is None or delay < self._backoff_seconds:
            delay = self._backoff_seconds
        return delay

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Dict[str, Any] | None = None,
        content: Optional[str] = None,
        max_attempts: int = 3,
    ) -> httpx.Response:
        last_response: Optional[httpx.Response] = None
        for _ in range(max_attempts):
            async with httpx.AsyncClient(timeout=self._timeout) as http_client:
                await self._limiter.wait()
                response = await http_client.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    content=content,
                )
            last_response = response
            if response.status_code == 429:
                await asyncio.sleep(self._resolve_backoff_seconds(response))
                continue
            response.raise_for_status()
            return response
        if last_response is not None:
            last_response.raise_for_status()
        raise RuntimeError("Discogs request failed without a response")
