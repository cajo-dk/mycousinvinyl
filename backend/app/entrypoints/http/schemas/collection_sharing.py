"""
Pydantic schemas for collection sharing endpoints.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator
import re


class CollectionSharingSettingsUpdate(BaseModel):
    """Schema for updating collection sharing settings."""

    enabled: Optional[bool] = Field(None, description="Enable/disable collection sharing")
    icon_type: Optional[str] = Field(
        None,
        description="MDI icon type (e.g., mdiAlphaACircle, mdiAlphaABox, etc.)"
    )
    icon_fg_color: Optional[str] = Field(None, description="Icon foreground color (hex)")
    icon_bg_color: Optional[str] = Field(None, description="Icon background color (hex)")

    @field_validator('icon_fg_color', 'icon_bg_color')
    @classmethod
    def validate_hex_color(cls, v: Optional[str]) -> Optional[str]:
        """Validate hex color format or 'transparent'."""
        if v is None:
            return v

        if not isinstance(v, str):
            raise ValueError("Color must be a string")

        # Allow 'transparent' as a special value
        if v.lower() == 'transparent':
            return 'transparent'

        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError(
                f"Invalid hex color format: {v}. Must be in format #RRGGBB or 'transparent'"
            )

        return v

    @field_validator('icon_type')
    @classmethod
    def validate_icon_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate MDI icon type format."""
        if v is None:
            return v

        if not isinstance(v, str):
            raise ValueError("Icon type must be a string")

        # Validate it's an MDI alpha icon variant
        valid_patterns = [
            r'^mdiAlpha[A-Z]$',  # mdiAlphaA, mdiAlphaB, etc.
            r'^mdiAlpha[A-Z]Box$',  # mdiAlphaABox, etc.
            r'^mdiAlpha[A-Z]BoxOutline$',  # mdiAlphaABoxOutline, etc.
            r'^mdiAlpha[A-Z]Circle$',  # mdiAlphaACircle, etc.
            r'^mdiAlpha[A-Z]CircleOutline$',  # mdiAlphaACircleOutline, etc.
        ]

        if not any(re.match(pattern, v) for pattern in valid_patterns):
            raise ValueError(
                f"Invalid icon type: {v}. Must be an MDI alpha icon variant "
                "(e.g., mdiAlphaA, mdiAlphaABox, mdiAlphaACircle, etc.)"
            )

        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "enabled": True,
                "icon_type": "mdiAlphaACircle",
                "icon_fg_color": "#FFFFFF",
                "icon_bg_color": "#1976D2"
            }
        }
    }


class CollectionSharingSettingsResponse(BaseModel):
    """Schema for collection sharing settings response."""

    enabled: bool = Field(..., description="Collection sharing is enabled")
    icon_type: str = Field(..., description="MDI icon type")
    icon_fg_color: str = Field(..., description="Icon foreground color (hex)")
    icon_bg_color: str = Field(..., description="Icon background color (hex)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "enabled": True,
                "icon_type": "mdiAlphaACircle",
                "icon_fg_color": "#FFFFFF",
                "icon_bg_color": "#1976D2"
            }
        }
    }


class UserOwnerInfoResponse(BaseModel):
    """Schema for user owner information."""

    user_id: str = Field(..., description="User UUID")
    display_name: str = Field(..., description="User's display name")
    first_name: str = Field(..., description="User's first name")
    icon_type: str = Field(..., description="MDI icon type")
    icon_fg_color: str = Field(..., description="Icon foreground color (hex)")
    icon_bg_color: str = Field(..., description="Icon background color (hex)")
    copy_count: int = Field(..., description="Number of copies owned", ge=0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "display_name": "Alex Rasmussen",
                "first_name": "Alex",
                "icon_type": "mdiAlphaACircle",
                "icon_fg_color": "#FFFFFF",
                "icon_bg_color": "#1976D2",
                "copy_count": 1
            }
        }
    }


class FollowUserRequest(BaseModel):
    """Schema for following a user."""

    user_id: str = Field(..., description="UUID of the user to follow")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    }


class FollowsListResponse(BaseModel):
    """Schema for list of followed users."""

    follows: List[UserOwnerInfoResponse] = Field(
        ..., description="List of followed users"
    )
    count: int = Field(..., description="Number of followed users", ge=0, le=3)

    model_config = {
        "json_schema_extra": {
            "example": {
                "follows": [
                    {
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "display_name": "Alex Rasmussen",
                        "first_name": "Alex",
                        "icon_type": "mdiAlphaACircle",
                        "icon_fg_color": "#FFFFFF",
                        "icon_bg_color": "#1976D2",
                        "copy_count": 0
                    }
                ],
                "count": 1
            }
        }
    }


class UserSearchResponse(BaseModel):
    """Schema for user search results."""

    users: List[UserOwnerInfoResponse] = Field(..., description="List of matching users")
    count: int = Field(..., description="Number of results", ge=0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "users": [
                    {
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "display_name": "Alex Rasmussen",
                        "first_name": "Alex",
                        "icon_type": "mdiAlphaACircle",
                        "icon_fg_color": "#FFFFFF",
                        "icon_bg_color": "#1976D2",
                        "copy_count": 0
                    }
                ],
                "count": 1
            }
        }
    }


class ItemOwnersResponse(BaseModel):
    """Schema for item (pressing/album) owners."""

    owners: List[UserOwnerInfoResponse] = Field(
        ..., description="List of owners (current user + followed users)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "owners": [
                    {
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "display_name": "Alex Rasmussen",
                        "first_name": "Alex",
                        "icon_type": "mdiAlphaACircle",
                        "icon_fg_color": "#FFFFFF",
                        "icon_bg_color": "#1976D2",
                        "copy_count": 1
                    }
                ]
            }
        }
    }


class PressingOwnersBatchRequest(BaseModel):
    """Schema for batch pressing owners request."""

    pressing_ids: List[str] = Field(
        ..., description="List of pressing UUIDs"
    )


class PressingOwnersBatchResponse(BaseModel):
    """Schema for batch pressing owners response."""

    owners_by_pressing: Dict[str, List[UserOwnerInfoResponse]] = Field(
        ..., description="Owners keyed by pressing UUID"
    )


class AlbumOwnersBatchRequest(BaseModel):
    """Schema for batch album owners request."""

    album_ids: List[str] = Field(
        ..., description="List of album UUIDs"
    )


class AlbumOwnersBatchResponse(BaseModel):
    """Schema for batch album owners response."""

    owners_by_album: Dict[str, List[UserOwnerInfoResponse]] = Field(
        ..., description="Owners keyed by album UUID"
    )
