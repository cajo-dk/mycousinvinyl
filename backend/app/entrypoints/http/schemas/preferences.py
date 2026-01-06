"""
User preferences API schemas.

SECURITY NOTE: user_id is never included in request schemas - it's always
extracted from the authenticated user context.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, computed_field

from app.entrypoints.http.schemas.collection_sharing import CollectionSharingSettingsResponse


class PreferencesUpdateCurrency(BaseModel):
    """Schema for updating preferred currency."""
    currency: str = Field(..., min_length=3, max_length=3, example="DKK", description="ISO 4217 currency code")


class PreferencesUpdateDisplay(BaseModel):
    """Schema for updating display settings."""
    display_settings: Dict[str, Any] = Field(
        ...,
        example={
            "theme": "dark",
            "items_per_page": 50,
            "default_sort": "date_added_desc",
            "show_prices": True
        },
        description="Flexible key-value pairs for UI preferences"
    )


class PreferencesUpdate(BaseModel):
    """Schema for updating multiple preferences at once."""
    currency: Optional[str] = Field(None, min_length=3, max_length=3, example="DKK")
    display_settings: Optional[Dict[str, Any]] = Field(
        None,
        example={"theme": "dark", "items_per_page": 50}
    )


class PreferencesResponse(BaseModel):
    """Schema for user preferences responses."""
    user_id: UUID
    currency: str = Field(..., example="DKK")
    display_settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def collection_sharing(self) -> CollectionSharingSettingsResponse:
        """Extract collection sharing settings from display_settings."""
        sharing_dict = self.display_settings.get('collection_sharing', {})
        return CollectionSharingSettingsResponse(
            enabled=sharing_dict.get('enabled', False),
            icon_type=sharing_dict.get('icon_type', 'mdiAlphaACircle'),
            icon_fg_color=sharing_dict.get('icon_fg_color', '#FFFFFF'),
            icon_bg_color=sharing_dict.get('icon_bg_color', '#1976D2')
        )

    class Config:
        from_attributes = True
