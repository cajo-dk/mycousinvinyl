"""
Domain entities for MyCousinVinyl vinyl collection management.

This layer contains core business logic and is security-agnostic.
No authentication or authorization logic belongs here.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from .value_objects import (
    ArtistType,
    ReleaseType,
    VinylFormat,
    VinylSpeed,
    VinylSize,
    EditionType,
    CollectionSharingSettings,
    SleeveType,
    Condition,
    MediaType,
    ExternalSource,
    DataSource,
    VerificationStatus,
)


@dataclass
class DomainEvent:
    """Base class for domain events."""
    event_type: str
    event_version: str
    occurred_at: datetime
    aggregate_id: UUID
    aggregate_type: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# DOMAIN EVENTS
# ============================================================================


@dataclass
class AlbumCreated(DomainEvent):
    """Event raised when an album is created."""

    def __init__(self, album_id: UUID, title: str, primary_artist_id: UUID, **kwargs):
        super().__init__(
            event_type="album.created",
            event_version="1.0.0",
            occurred_at=datetime.utcnow(),
            aggregate_id=album_id,
            aggregate_type="Album",
            payload={
                "album_id": str(album_id),
                "title": title,
                "primary_artist_id": str(primary_artist_id),
                **kwargs
            }
        )


@dataclass
class AlbumUpdated(DomainEvent):
    """Event raised when an album is updated."""

    def __init__(self, album_id: UUID, **kwargs):
        super().__init__(
            event_type="album.updated",
            event_version="1.0.0",
            occurred_at=datetime.utcnow(),
            aggregate_id=album_id,
            aggregate_type="Album",
            payload={"album_id": str(album_id), **kwargs}
        )


@dataclass
class CollectionItemAdded(DomainEvent):
    """Event raised when an item is added to collection."""

    def __init__(self, collection_item_id: UUID, user_id: UUID, pressing_id: UUID, **kwargs):
        super().__init__(
            event_type="collection.item.added",
            event_version="1.0.0",
            occurred_at=datetime.utcnow(),
            aggregate_id=collection_item_id,
            aggregate_type="CollectionItem",
            payload={
                "collection_item_id": str(collection_item_id),
                "user_id": str(user_id),
                "pressing_id": str(pressing_id),
                **kwargs
            }
        )


@dataclass
class CollectionItemUpdated(DomainEvent):
    """Event raised when a collection item is updated."""

    def __init__(self, collection_item_id: UUID, user_id: UUID, **kwargs):
        super().__init__(
            event_type="collection.item.updated",
            event_version="1.0.0",
            occurred_at=datetime.utcnow(),
            aggregate_id=collection_item_id,
            aggregate_type="CollectionItem",
            payload={
                "collection_item_id": str(collection_item_id),
                "user_id": str(user_id),
                **kwargs
            }
        )


@dataclass
class CollectionItemRemoved(DomainEvent):
    """Event raised when a collection item is removed."""

    def __init__(self, collection_item_id: UUID, user_id: UUID, pressing_id: UUID):
        super().__init__(
            event_type="collection.item.removed",
            event_version="1.0.0",
            occurred_at=datetime.utcnow(),
            aggregate_id=collection_item_id,
            aggregate_type="CollectionItem",
            payload={
                "collection_item_id": str(collection_item_id),
                "user_id": str(user_id),
                "pressing_id": str(pressing_id)
            }
        )


# ============================================================================
# DOMAIN ENTITIES
# ============================================================================


@dataclass
class Artist:
    """
    Musical artist or group.

    Business rules:
    - name is required and cannot be empty
    - sort_name auto-generated from name if not provided
    """

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    sort_name: str = ""
    type: ArtistType = ArtistType.PERSON
    country: Optional[str] = None  # ISO 3166-1 alpha-2
    disambiguation: Optional[str] = None
    bio: Optional[str] = None
    image_url: Optional[str] = None
    begin_date: Optional[str] = None
    end_date: Optional[str] = None
    active_years: Optional[str] = None
    album_count: Optional[int] = None
    aliases: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    discogs_id: Optional[int] = None

    # System metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    data_source: DataSource = DataSource.USER
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED

    events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        """Validate and set defaults."""
        if not self.name or not self.name.strip():
            raise ValueError("Artist name is required")

        self.name = self.name.strip()

        # Auto-generate sort_name if not provided
        if not self.sort_name:
            self.sort_name = self._generate_sort_name(self.name)

    @staticmethod
    def _generate_sort_name(name: str) -> str:
        """Generate sort name from display name (e.g., 'The Beatles' -> 'Beatles, The')."""
        name = name.strip()
        articles = ['The', 'A', 'An']

        for article in articles:
            if name.startswith(f"{article} "):
                return f"{name[len(article)+1:]}, {article}"

        return name

    def update(
        self,
        name: Optional[str] = None,
        type: Optional[ArtistType] = None,
        country: Optional[str] = None,
        **kwargs
    ) -> None:
        """Update artist with validation."""
        if name is not None:
            if not name.strip():
                raise ValueError("Artist name cannot be empty")
            self.name = name.strip()
            self.sort_name = self._generate_sort_name(self.name)

        if type is not None:
            self.type = type

        if country is not None:
            self.country = country

        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ['id', 'created_at', 'created_by']:
                setattr(self, key, value)

        self.updated_at = datetime.utcnow()

    def clear_events(self) -> List[DomainEvent]:
        """Clear and return pending domain events."""
        events = self.events.copy()
        self.events.clear()
        return events


@dataclass
class Album:
    """
    Musical album/release (independent of physical pressing).

    Business rules:
    - title and primary_artist_id are required
    - original_release_id cannot reference self
    """

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    primary_artist_id: Optional[UUID] = None
    release_type: ReleaseType = ReleaseType.STUDIO
    original_release_year: Optional[int] = None
    original_release_date: Optional[date] = None
    country_of_origin: Optional[str] = None  # ISO 3166-1 alpha-3
    label: Optional[str] = None
    catalog_number_base: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    original_release_id: Optional[UUID] = None  # For reissues
    discogs_id: Optional[int] = None

    # Many-to-many relationships (managed by repository)
    genre_ids: List[UUID] = field(default_factory=list)
    style_ids: List[UUID] = field(default_factory=list)

    # System metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    data_source: DataSource = DataSource.USER
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED

    events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        """Validate business rules."""
        if not self.title or not self.title.strip():
            raise ValueError("Album title is required")

        if not self.primary_artist_id:
            raise ValueError("Primary artist is required")

        if self.original_release_id and self.original_release_id == self.id:
            raise ValueError("Album cannot reference itself as original release")

        self.title = self.title.strip()

        # Emit creation event
        if not self.events:  # Only on first creation
            self.events.append(AlbumCreated(
                album_id=self.id,
                title=self.title,
                primary_artist_id=self.primary_artist_id
            ))

    def update(self, **kwargs) -> None:
        """Update album with validation."""
        if 'title' in kwargs:
            if not kwargs['title'] or not kwargs['title'].strip():
                raise ValueError("Album title cannot be empty")
            self.title = kwargs['title'].strip()

        if 'primary_artist_id' in kwargs:
            if not kwargs['primary_artist_id']:
                raise ValueError("Primary artist is required")
            self.primary_artist_id = kwargs['primary_artist_id']

        if 'original_release_id' in kwargs:
            if kwargs['original_release_id'] == self.id:
                raise ValueError("Album cannot reference itself as original release")
            self.original_release_id = kwargs['original_release_id']

        # Update remaining fields (skip already-processed and protected fields)
        processed_fields = {'title', 'primary_artist_id', 'original_release_id'}
        protected_fields = {'id', 'created_at', 'created_by', 'events'}
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in processed_fields | protected_fields:
                setattr(self, key, value)

        self.updated_at = datetime.utcnow()
        self.events.append(AlbumUpdated(album_id=self.id, **kwargs))

    def clear_events(self) -> List[DomainEvent]:
        """Clear and return pending domain events."""
        events = self.events.copy()
        self.events.clear()
        return events


@dataclass
class Track:
    """
    Individual track on an album.

    Business rules:
    - album_id, side, position, and title are required
    - position format should be like A1, B2, etc.
    """

    id: UUID = field(default_factory=uuid4)
    album_id: Optional[UUID] = None
    side: str = ""  # A, B, C, D, etc.
    position: str = ""  # 1, 2, 3, etc. (combined with side = A1, B2)
    title: str = ""
    duration: Optional[int] = None  # Duration in seconds
    songwriters: List[str] = field(default_factory=list)
    notes: Optional[str] = None

    # System metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        """Validate business rules."""
        if not self.album_id:
            raise ValueError("Track must belong to an album")

        if not self.side or not self.side.strip():
            raise ValueError("Track side is required")

        if not self.position or not self.position.strip():
            raise ValueError("Track position is required")

        if not self.title or not self.title.strip():
            raise ValueError("Track title is required")

        self.side = self.side.strip().upper()
        self.position = self.position.strip()
        self.title = self.title.strip()

    @property
    def full_position(self) -> str:
        """Get full position (e.g., 'A1', 'B2')."""
        return f"{self.side}{self.position}"

    def clear_events(self) -> List[DomainEvent]:
        """Clear and return pending domain events."""
        events = self.events.copy()
        self.events.clear()
        return events


@dataclass
class Pressing:
    """
    Specific physical vinyl pressing of an album.

    Business rules:
    - album_id, format, speed, and size are required
    - disc_count must be positive
    """

    id: UUID = field(default_factory=uuid4)
    album_id: Optional[UUID] = None
    format: Optional[VinylFormat] = None
    speed_rpm: Optional[VinylSpeed] = None
    size_inches: Optional[VinylSize] = None
    disc_count: int = 1
    pressing_country: Optional[str] = None  # ISO 3166-1 alpha-3
    pressing_year: Optional[int] = None
    pressing_plant: Optional[str] = None
    mastering_engineer: Optional[str] = None
    mastering_studio: Optional[str] = None
    vinyl_color: Optional[str] = None
    label_design: Optional[str] = None
    image_url: Optional[str] = None
    edition_type: EditionType = EditionType.STANDARD
    barcode: Optional[str] = None
    notes: Optional[str] = None
    discogs_release_id: Optional[int] = None
    discogs_master_id: Optional[int] = None
    master_title: Optional[str] = None

    # System metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    data_source: DataSource = DataSource.USER
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED

    events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        """Validate business rules."""
        if not self.album_id:
            raise ValueError("Pressing must belong to an album")

        if not self.format:
            raise ValueError("Vinyl format is required")

        if not self.speed_rpm:
            raise ValueError("Playback speed is required")

        if not self.size_inches:
            raise ValueError("Vinyl size is required")

        if self.disc_count < 1:
            raise ValueError("Disc count must be at least 1")

    def clear_events(self) -> List[DomainEvent]:
        """Clear and return pending domain events."""
        events = self.events.copy()
        self.events.clear()
        return events


@dataclass
class Matrix:
    """
    Matrix/runout codes etched on vinyl pressing (per side).

    Business rules:
    - pressing_id and side are required
    - Unique per pressing and side
    """

    id: UUID = field(default_factory=uuid4)
    pressing_id: Optional[UUID] = None
    side: str = ""  # A, B, C, D, etc.
    matrix_code: Optional[str] = None
    etchings: Optional[str] = None
    stamper_info: Optional[str] = None

    # System metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        """Validate business rules."""
        if not self.pressing_id:
            raise ValueError("Matrix must belong to a pressing")

        if not self.side or not self.side.strip():
            raise ValueError("Side is required")

        self.side = self.side.strip().upper()

    def clear_events(self) -> List[DomainEvent]:
        """Clear and return pending domain events."""
        events = self.events.copy()
        self.events.clear()
        return events


@dataclass
class Packaging:
    """
    Packaging details for a pressing (one-to-one relationship).

    Business rules:
    - pressing_id and sleeve_type are required
    - One packaging per pressing
    """

    id: UUID = field(default_factory=uuid4)
    pressing_id: Optional[UUID] = None
    sleeve_type: Optional[SleeveType] = None
    cover_artist: Optional[str] = None
    includes_inner_sleeve: bool = False
    includes_insert: bool = False
    includes_poster: bool = False
    includes_obi: bool = False
    stickers: Optional[str] = None
    notes: Optional[str] = None

    # System metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        """Validate business rules."""
        if not self.pressing_id:
            raise ValueError("Packaging must belong to a pressing")

        if not self.sleeve_type:
            raise ValueError("Sleeve type is required")

    def clear_events(self) -> List[DomainEvent]:
        """Clear and return pending domain events."""
        events = self.events.copy()
        self.events.clear()
        return events


@dataclass
class CollectionItem:
    """
    User-owned copy of a pressing.

    Business rules:
    - user_id and pressing_id are required
    - Conditions must be valid Condition enum values
    - purchase_price must be >= 0
    - user_rating must be 0-5
    """

    id: UUID = field(default_factory=uuid4)
    user_id: Optional[UUID] = None
    pressing_id: Optional[UUID] = None
    media_condition: Optional[Condition] = None
    sleeve_condition: Optional[Condition] = None
    play_tested: bool = False
    defect_notes: Optional[str] = None
    purchase_price: Optional[Decimal] = None
    purchase_currency: Optional[str] = None  # ISO 4217
    purchase_date: Optional[date] = None
    seller: Optional[str] = None
    storage_location: Optional[str] = None
    play_count: int = 0
    last_played_date: Optional[date] = None
    user_rating: Optional[int] = None  # 0-5
    user_notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    date_added: datetime = field(default_factory=datetime.utcnow)

    # System metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        """Validate business rules."""
        if not self.user_id:
            raise ValueError("Collection item must belong to a user")

        if not self.pressing_id:
            raise ValueError("Collection item must reference a pressing")

        if not self.media_condition:
            raise ValueError("Media condition is required")

        if not self.sleeve_condition:
            raise ValueError("Sleeve condition is required")

        if self.purchase_price is not None and self.purchase_price < 0:
            raise ValueError("Purchase price cannot be negative")

        if self.user_rating is not None and (self.user_rating < 0 or self.user_rating > 5):
            raise ValueError("User rating must be between 0 and 5")

        # Emit creation event
        if not self.events:  # Only on first creation
            self.events.append(CollectionItemAdded(
                collection_item_id=self.id,
                user_id=self.user_id,
                pressing_id=self.pressing_id
            ))

    def update_condition(
        self,
        media_condition: Optional[Condition] = None,
        sleeve_condition: Optional[Condition] = None,
        defect_notes: Optional[str] = None
    ) -> None:
        """Update condition information."""
        if media_condition:
            self.media_condition = media_condition
        if sleeve_condition:
            self.sleeve_condition = sleeve_condition
        if defect_notes is not None:
            self.defect_notes = defect_notes

        self.updated_at = datetime.utcnow()
        self.events.append(CollectionItemUpdated(
            collection_item_id=self.id,
            user_id=self.user_id,
            media_condition=media_condition.value if media_condition else None,
            sleeve_condition=sleeve_condition.value if sleeve_condition else None
        ))

    def update_purchase_info(
        self,
        price: Optional[Decimal] = None,
        currency: Optional[str] = None,
        purchase_date: Optional[date] = None,
        seller: Optional[str] = None
    ) -> None:
        """Update purchase information."""
        if price is not None:
            if price < 0:
                raise ValueError("Purchase price cannot be negative")
            self.purchase_price = price

        if currency:
            self.purchase_currency = currency

        if purchase_date:
            self.purchase_date = purchase_date

        if seller is not None:
            self.seller = seller

        self.updated_at = datetime.utcnow()

    def update_rating(self, rating: int, notes: Optional[str] = None) -> None:
        """Update user rating and notes."""
        if rating < 0 or rating > 5:
            raise ValueError("User rating must be between 0 and 5")

        self.user_rating = rating
        if notes is not None:
            self.user_notes = notes

        self.updated_at = datetime.utcnow()
        self.events.append(CollectionItemUpdated(
            collection_item_id=self.id,
            user_id=self.user_id,
            user_rating=rating
        ))

    def increment_play_count(self) -> None:
        """Increment play count and update last played date."""
        self.play_count += 1
        self.last_played_date = date.today()
        self.updated_at = datetime.utcnow()

    def clear_events(self) -> List[DomainEvent]:
        """Clear and return pending domain events."""
        events = self.events.copy()
        self.events.clear()
        return events


@dataclass
class MediaAsset:
    """
    Media files (images, videos) associated with entities.

    Business rules:
    - entity_type, entity_id, media_type, and url are required
    """

    id: UUID = field(default_factory=uuid4)
    entity_type: str = ""  # Album, Artist, Pressing, CollectionItem
    entity_id: Optional[UUID] = None
    media_type: Optional[MediaType] = None
    url: str = ""
    description: Optional[str] = None
    uploaded_by_user: bool = True

    # System metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        """Validate business rules."""
        if not self.entity_type or not self.entity_type.strip():
            raise ValueError("Entity type is required")

        if not self.entity_id:
            raise ValueError("Entity ID is required")

        if not self.media_type:
            raise ValueError("Media type is required")

        if not self.url or not self.url.strip():
            raise ValueError("URL is required")

        self.entity_type = self.entity_type.strip()
        self.url = self.url.strip()

    def clear_events(self) -> List[DomainEvent]:
        """Clear and return pending domain events."""
        events = self.events.copy()
        self.events.clear()
        return events


@dataclass
class ExternalReference:
    """
    Links to external databases (Discogs, MusicBrainz, etc.).

    Business rules:
    - All fields are required
    - Unique constraint on (entity_type, entity_id, source)
    """

    id: UUID = field(default_factory=uuid4)
    entity_type: str = ""  # Album, Artist, Pressing
    entity_id: Optional[UUID] = None
    source: Optional[ExternalSource] = None
    external_id: str = ""
    url: Optional[str] = None

    # System metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        """Validate business rules."""
        if not self.entity_type or not self.entity_type.strip():
            raise ValueError("Entity type is required")

        if not self.entity_id:
            raise ValueError("Entity ID is required")

        if not self.source:
            raise ValueError("External source is required")

        if not self.external_id or not self.external_id.strip():
            raise ValueError("External ID is required")

        self.entity_type = self.entity_type.strip()
        self.external_id = self.external_id.strip()

    def clear_events(self) -> List[DomainEvent]:
        """Clear and return pending domain events."""
        events = self.events.copy()
        self.events.clear()
        return events


@dataclass
class UserPreferences:
    """
    User preferences and settings.

    Business rules:
    - user_id is required
    - currency must be valid ISO 4217 code
    """

    user_id: Optional[UUID] = None
    currency: str = "DKK"  # ISO 4217
    display_settings: Dict[str, Any] = field(default_factory=dict)

    # System metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        """Validate business rules."""
        if not self.user_id:
            raise ValueError("User ID is required")

        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO 4217 code")

        self.currency = self.currency.upper()

    def update_currency(self, currency: str) -> None:
        """Update preferred currency."""
        if not currency or len(currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO 4217 code")

        self.currency = currency.upper()
        self.updated_at = datetime.utcnow()

    def update_display_settings(self, settings: Dict[str, Any]) -> None:
        """Update display settings."""
        self.display_settings.update(settings)
        self.updated_at = datetime.utcnow()

    def get_collection_sharing_settings(self) -> CollectionSharingSettings:
        """
        Get collection sharing settings from display_settings.

        Returns default settings if not configured.
        """
        sharing_dict = self.display_settings.get('collection_sharing', {})
        return CollectionSharingSettings(
            enabled=sharing_dict.get('enabled', False),
            icon_type=sharing_dict.get('icon_type', 'mdiAlphaACircle'),
            icon_fg_color=sharing_dict.get('icon_fg_color', '#FFFFFF'),
            icon_bg_color=sharing_dict.get('icon_bg_color', '#1976D2')
        )

    def update_collection_sharing_settings(self, settings: CollectionSharingSettings) -> None:
        """
        Update collection sharing settings.

        Validates settings via CollectionSharingSettings value object.
        """
        if 'collection_sharing' not in self.display_settings:
            self.display_settings['collection_sharing'] = {}

        self.display_settings['collection_sharing'] = {
            'enabled': settings.enabled,
            'icon_type': settings.icon_type,
            'icon_fg_color': settings.icon_fg_color,
            'icon_bg_color': settings.icon_bg_color
        }
        self.updated_at = datetime.utcnow()

    def get_user_profile(self) -> Dict[str, str]:
        """
        Get user profile information from display_settings.

        Returns empty dict if not configured.
        """
        return self.display_settings.get('user_profile', {})

    def update_user_profile(self, display_name: str, first_name: str) -> None:
        """
        Update user profile information (for user search).

        This stores the user's name extracted from Azure AD for search functionality.
        """
        if 'user_profile' not in self.display_settings:
            self.display_settings['user_profile'] = {}

        self.display_settings['user_profile'] = {
            'display_name': display_name,
            'first_name': first_name
        }
        self.updated_at = datetime.utcnow()


@dataclass
class SystemSetting:
    """
    Global system setting (key/value).
    """

    key: str = ""
    value: str = ""

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        if not self.key or not self.key.strip():
            raise ValueError("Setting key is required")
        self.key = self.key.strip()


@dataclass
class SystemLogEntry:
    """
    System audit log entry.
    """

    id: UUID = field(default_factory=uuid4)
    user_id: Optional[UUID] = None
    user_name: str = ""
    severity: str = "INFO"
    component: str = ""
    message: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

    events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        if not self.user_name or not self.user_name.strip():
            raise ValueError("User name is required")
        if not self.component or not self.component.strip():
            raise ValueError("Component is required")
        if not self.message or not self.message.strip():
            raise ValueError("Log message is required")
        self.user_name = self.user_name.strip()
        self.component = self.component.strip()
        self.message = self.message.strip()

    def clear_events(self) -> List[DomainEvent]:
        """Clear and return pending domain events."""
        events = self.events.copy()
        self.events.clear()
        return events


@dataclass
class MarketData:
    """
    Market pricing data for pressings (optional, Phase 10+).

    Business rules:
    - pressing_id is required
    """

    id: UUID = field(default_factory=uuid4)
    pressing_id: Optional[UUID] = None
    min_value: Optional[Decimal] = None
    median_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    last_sold_price: Optional[Decimal] = None
    currency: str = "DKK"  # ISO 4217
    availability_status: Optional[str] = None

    # System metadata
    updated_at: datetime = field(default_factory=datetime.utcnow)

    events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        """Validate business rules."""
        if not self.pressing_id:
            raise ValueError("Market data must belong to a pressing")

    def clear_events(self) -> List[DomainEvent]:
        """Clear and return pending domain events."""
        events = self.events.copy()
        self.events.clear()
        return events


@dataclass
class CollectionImport:
    """
    Import job for external collection data (Discogs CSV).
    """

    id: UUID = field(default_factory=uuid4)
    user_id: Optional[UUID] = None
    filename: str = ""
    status: str = "queued"
    total_rows: int = 0
    processed_rows: int = 0
    success_count: int = 0
    error_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_summary: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)

    # System metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not self.user_id:
            raise ValueError("Import must belong to a user")
        if not self.filename or not self.filename.strip():
            raise ValueError("Import filename is required")

    def clear_events(self) -> List[DomainEvent]:
        return []


@dataclass
class CollectionImportRow:
    """
    Single row from an external collection import.
    """

    id: UUID = field(default_factory=uuid4)
    import_id: Optional[UUID] = None
    row_number: int = 0
    status: str = "pending"
    raw_data: Dict[str, Any] = field(default_factory=dict)
    discogs_release_id: Optional[int] = None
    artist_id: Optional[UUID] = None
    album_id: Optional[UUID] = None
    pressing_id: Optional[UUID] = None
    collection_item_id: Optional[UUID] = None
    error_message: Optional[str] = None

    # System metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not self.import_id:
            raise ValueError("Import row must belong to an import")
        if self.row_number < 1:
            raise ValueError("Row number must be >= 1")

    def clear_events(self) -> List[DomainEvent]:
        return []


@dataclass
class DiscogsOAuthRequest:
    """
    Temporary request token for Discogs OAuth flow.
    """

    id: UUID = field(default_factory=uuid4)
    user_id: Optional[UUID] = None
    request_token: str = ""
    request_secret: str = ""
    state: str = ""
    redirect_uri: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.user_id:
            raise ValueError("Discogs OAuth request must belong to a user")
        if not self.request_token:
            raise ValueError("Discogs OAuth request token is required")
        if not self.request_secret:
            raise ValueError("Discogs OAuth request secret is required")
        if not self.state:
            raise ValueError("Discogs OAuth state is required")
        if not self.redirect_uri:
            raise ValueError("Discogs OAuth redirect URI is required")


@dataclass
class DiscogsUserToken:
    """
    Persisted Discogs token for a user (OAuth or PAT).
    """

    user_id: Optional[UUID] = None
    access_token: str = ""
    access_secret: Optional[str] = None
    discogs_username: str = ""
    last_synced_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not self.user_id:
            raise ValueError("Discogs token must belong to a user")
        if not self.access_token:
            raise ValueError("Discogs access token is required")
        if not self.discogs_username:
            raise ValueError("Discogs username is required")
