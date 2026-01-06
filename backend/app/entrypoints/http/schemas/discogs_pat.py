"""
Schemas for Discogs Personal Access Token endpoints.
"""

from pydantic import BaseModel, Field


class DiscogsPatConnectRequest(BaseModel):
    username: str = Field(..., min_length=1)
    token: str = Field(..., min_length=1)
