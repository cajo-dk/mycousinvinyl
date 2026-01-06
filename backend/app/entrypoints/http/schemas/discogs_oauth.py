"""
Schemas for Discogs OAuth endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DiscogsOAuthStartRequest(BaseModel):
    redirect_uri: Optional[str] = None


class DiscogsOAuthStartResponse(BaseModel):
    authorization_url: str


class DiscogsOAuthStatusResponse(BaseModel):
    connected: bool
    username: Optional[str] = None
    last_synced_at: Optional[datetime] = None
