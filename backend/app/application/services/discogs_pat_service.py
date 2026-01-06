"""
Service for storing Discogs Personal Access Tokens (PAT).
"""

from uuid import UUID

from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities import DiscogsUserToken


class DiscogsPatService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def connect_pat(self, user_id: UUID, username: str, token: str) -> DiscogsUserToken:
        cleaned_username = (username or "").strip()
        cleaned_token = (token or "").strip()
        if not cleaned_username:
            raise ValueError("Discogs username is required")
        if not cleaned_token:
            raise ValueError("Discogs personal access token is required")

        discogs_token = DiscogsUserToken(
            user_id=user_id,
            access_token=cleaned_token,
            access_secret=None,
            discogs_username=cleaned_username,
        )

        async with self.uow:
            await self.uow.discogs_user_token_repository.upsert(discogs_token)
            await self.uow.commit()

        return discogs_token
