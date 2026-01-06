"""
Value objects and enums for the domain model.

These are immutable values that represent concepts in the vinyl collection domain.
All enums use string values for database compatibility and clarity.
"""

from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class ArtistType(str):
    """Type of musical artist (lookup-backed)."""
    PERSON = "Person"
    GROUP = "Group"


class ReleaseType(str):
    """Type of album/release (lookup-backed)."""
    STUDIO = "Studio"
    LIVE = "Live"
    COMPILATION = "Compilation"
    EP = "EP"
    SINGLE = "Single"
    BOX_SET = "Box Set"


class VinylFormat(str, Enum):
    """Physical vinyl format."""
    LP = "LP"
    EP = "EP"
    SINGLE = "Single"
    MAXI = "Maxi"
    CD = "CD"


class VinylSpeed(str, Enum):
    """Playback speed in RPM."""
    RPM_33 = "33 1/3"
    RPM_45 = "45"
    RPM_78 = "78"
    NA = "N/A"


class VinylSize(str, Enum):
    """Vinyl disc diameter."""
    SIZE_7 = '7"'
    SIZE_10 = '10"'
    SIZE_12 = '12"'
    CD = "CD"


class EditionType(str):
    """Type of pressing edition (lookup-backed)."""
    STANDARD = "Standard"
    LIMITED = "Limited"
    NUMBERED = "Numbered"
    REISSUE = "Reissue"
    REMASTER = "Remaster"


class SleeveType(str):
    """Album sleeve/jacket type (lookup-backed)."""
    SINGLE = "Single"
    GATEFOLD = "Gatefold"
    BOX = "Box"


class Condition(str, Enum):
    """Record grading condition (Goldmine standard)."""
    MINT = "Mint"
    NEAR_MINT = "NM"
    VG_PLUS = "VG+"
    VG = "VG"
    GOOD = "G"
    POOR = "P"


class MediaType(str, Enum):
    """Type of media asset."""
    IMAGE = "Image"
    VIDEO = "Video"


class ExternalSource(str, Enum):
    """External data source."""
    DISCOGS = "Discogs"
    MUSICBRAINZ = "MusicBrainz"
    SPOTIFY = "Spotify"
    APPLE_MUSIC = "Apple Music"


class DataSource(str, Enum):
    """Source of data entry."""
    USER = "User"
    IMPORT = "Import"
    API = "API"


class VerificationStatus(str, Enum):
    """Data verification status."""
    VERIFIED = "Verified"
    COMMUNITY = "Community"
    UNVERIFIED = "Unverified"


# Collection Sharing Value Objects

@dataclass(frozen=True)
class CollectionSharingSettings:
    """
    Immutable settings for collection sharing visibility.

    These settings control how a user's collection is shared with others.
    """
    enabled: bool = False
    icon_type: str = "mdiAlphaACircle"  # One of: mdiAlpha{X}, mdiAlpha{X}Box, etc.
    icon_fg_color: str = "#FFFFFF"
    icon_bg_color: str = "#1976D2"

    def __post_init__(self):
        """Validate settings after initialization."""
        # Validate hex color format or allow transparent
        if self.icon_fg_color != "transparent":
            if not self.icon_fg_color.startswith('#') or len(self.icon_fg_color) != 7:
                raise ValueError(f"Invalid foreground color format: {self.icon_fg_color}")
        if self.icon_bg_color != "transparent":
            if not self.icon_bg_color.startswith('#') or len(self.icon_bg_color) != 7:
                raise ValueError(f"Invalid background color format: {self.icon_bg_color}")


@dataclass(frozen=True)
class UserOwnerInfo:
    """
    Immutable information about a user who owns a pressing/album.

    Used for displaying ownership in the owners grid.
    """
    user_id: UUID
    display_name: str
    first_name: str
    icon_type: str
    icon_fg_color: str
    icon_bg_color: str
    copy_count: int

    def __post_init__(self):
        """Validate owner info after initialization."""
        if self.copy_count < 1:
            raise ValueError(f"Copy count must be at least 1, got {self.copy_count}")
