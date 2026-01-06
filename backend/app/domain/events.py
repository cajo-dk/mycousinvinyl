"""
Domain events.

Domain events represent things that have happened in the system.
They are immutable facts about state changes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""
    event_id: UUID = field(default_factory=uuid4)
    event_type: str = field(init=False)
    event_version: str = "1.0.0"
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        # Set event_type based on class name
        object.__setattr__(self, 'event_type', self.__class__.__name__)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            'event_id': str(self.event_id),
            'event_type': self.event_type,
            'event_version': self.event_version,
            'occurred_at': self.occurred_at.isoformat(),
            **self._payload()
        }

    def _payload(self) -> Dict[str, Any]:
        """Return event-specific payload. Override in subclasses."""
        return {}


# ============================================================================
# ARTIST EVENTS
# ============================================================================

@dataclass(frozen=True)
class ArtistCreated(DomainEvent):
    """Event raised when an artist is created."""
    artist_id: UUID = field(default=None)
    name: str = field(default='')
    artist_type: str = field(default='')
    created_by: UUID | None = field(default=None)

    def _payload(self) -> Dict[str, Any]:
        return {
            'artist_id': str(self.artist_id),
            'name': self.name,
            'artist_type': self.artist_type,
            'created_by': str(self.created_by) if self.created_by else None
        }


@dataclass(frozen=True)
class ArtistUpdated(DomainEvent):
    """Event raised when an artist is updated."""
    artist_id: UUID = field(default=None)
    updated_fields: Dict[str, Any] = field(default_factory=dict)

    def _payload(self) -> Dict[str, Any]:
        return {
            'artist_id': str(self.artist_id),
            'updated_fields': self.updated_fields
        }


@dataclass(frozen=True)
class ArtistDeleted(DomainEvent):
    """Event raised when an artist is deleted."""
    artist_id: UUID = field(default=None)

    def _payload(self) -> Dict[str, Any]:
        return {
            'artist_id': str(self.artist_id)
        }


# ============================================================================
# ALBUM EVENTS
# ============================================================================

@dataclass(frozen=True)
class AlbumCreated(DomainEvent):
    """Event raised when an album is created."""
    album_id: UUID = field(default=None)
    title: str = field(default='')
    artist_id: UUID = field(default=None)
    release_type: str = field(default='')
    created_by: UUID | None = field(default=None)

    def _payload(self) -> Dict[str, Any]:
        return {
            'album_id': str(self.album_id),
            'title': self.title,
            'artist_id': str(self.artist_id),
            'release_type': self.release_type,
            'created_by': str(self.created_by) if self.created_by else None
        }


@dataclass(frozen=True)
class AlbumUpdated(DomainEvent):
    """Event raised when an album is updated."""
    album_id: UUID = field(default=None)
    updated_fields: Dict[str, Any] = field(default_factory=dict)

    def _payload(self) -> Dict[str, Any]:
        return {
            'album_id': str(self.album_id),
            'updated_fields': self.updated_fields
        }


@dataclass(frozen=True)
class AlbumDeleted(DomainEvent):
    """Event raised when an album is deleted."""
    album_id: UUID = field(default=None)

    def _payload(self) -> Dict[str, Any]:
        return {
            'album_id': str(self.album_id)
        }


# ============================================================================
# PRESSING EVENTS
# ============================================================================

@dataclass(frozen=True)
class PressingCreated(DomainEvent):
    """Event raised when a pressing is created."""
    pressing_id: UUID = field(default=None)
    album_id: UUID = field(default=None)
    format: str = field(default='')
    country: str | None = field(default=None)
    created_by: UUID | None = field(default=None)

    def _payload(self) -> Dict[str, Any]:
        return {
            'pressing_id': str(self.pressing_id),
            'album_id': str(self.album_id),
            'format': self.format,
            'country': self.country,
            'created_by': str(self.created_by) if self.created_by else None
        }


@dataclass(frozen=True)
class PressingUpdated(DomainEvent):
    """Event raised when a pressing is updated."""
    pressing_id: UUID = field(default=None)
    updated_fields: Dict[str, Any] = field(default_factory=dict)

    def _payload(self) -> Dict[str, Any]:
        return {
            'pressing_id': str(self.pressing_id),
            'updated_fields': self.updated_fields
        }


@dataclass(frozen=True)
class PressingDeleted(DomainEvent):
    """Event raised when a pressing is deleted."""
    pressing_id: UUID = field(default=None)

    def _payload(self) -> Dict[str, Any]:
        return {
            'pressing_id': str(self.pressing_id)
        }


@dataclass(frozen=True)
class PressingMasterImportRequested(DomainEvent):
    """Event raised when a master pressing import is requested."""
    pressing_id: UUID = field(default=None)
    discogs_master_id: int | None = field(default=None)
    created_by: UUID | None = field(default=None)

    def _payload(self) -> Dict[str, Any]:
        return {
            'pressing_id': str(self.pressing_id),
            'discogs_master_id': self.discogs_master_id,
            'created_by': str(self.created_by) if self.created_by else None
        }


# ============================================================================
# COLLECTION EVENTS
# ============================================================================

@dataclass(frozen=True)
class CollectionItemAdded(DomainEvent):
    """Event raised when an item is added to a collection."""
    collection_item_id: UUID = field(default=None)
    user_id: UUID = field(default=None)
    pressing_id: UUID = field(default=None)
    media_condition: str = field(default='')
    sleeve_condition: str = field(default='')

    def _payload(self) -> Dict[str, Any]:
        return {
            'collection_item_id': str(self.collection_item_id),
            'user_id': str(self.user_id),
            'pressing_id': str(self.pressing_id),
            'media_condition': self.media_condition,
            'sleeve_condition': self.sleeve_condition
        }


@dataclass(frozen=True)
class CollectionItemUpdated(DomainEvent):
    """Event raised when a collection item is updated."""
    collection_item_id: UUID = field(default=None)
    user_id: UUID = field(default=None)
    updated_fields: Dict[str, Any] = field(default_factory=dict)

    def _payload(self) -> Dict[str, Any]:
        return {
            'collection_item_id': str(self.collection_item_id),
            'user_id': str(self.user_id),
            'updated_fields': self.updated_fields
        }


@dataclass(frozen=True)
class CollectionItemRemoved(DomainEvent):
    """Event raised when an item is removed from a collection."""
    collection_item_id: UUID = field(default=None)
    user_id: UUID = field(default=None)
    pressing_id: UUID = field(default=None)

    def _payload(self) -> Dict[str, Any]:
        return {
            'collection_item_id': str(self.collection_item_id),
            'user_id': str(self.user_id),
            'pressing_id': str(self.pressing_id)
        }


@dataclass(frozen=True)
class CollectionItemPlayed(DomainEvent):
    """Event raised when a collection item is played."""
    collection_item_id: UUID = field(default=None)
    user_id: UUID = field(default=None)
    play_count: int = field(default=0)
    played_at: datetime = field(default_factory=datetime.utcnow)

    def _payload(self) -> Dict[str, Any]:
        return {
            'collection_item_id': str(self.collection_item_id),
            'user_id': str(self.user_id),
            'play_count': self.play_count,
            'played_at': self.played_at.isoformat()
        }


@dataclass(frozen=True)
class CollectionItemRated(DomainEvent):
    """Event raised when a collection item is rated."""
    collection_item_id: UUID = field(default=None)
    user_id: UUID = field(default=None)
    rating: int = field(default=0)

    def _payload(self) -> Dict[str, Any]:
        return {
            'collection_item_id': str(self.collection_item_id),
            'user_id': str(self.user_id),
            'rating': self.rating
        }


# ============================================================================
# ACTIVITY EVENTS
# ============================================================================

@dataclass(frozen=True)
class ActivityEvent(DomainEvent):
    """Event published to the activity feed for UI notifications."""
    operation: str = field(default='')
    entity_type: str = field(default='')
    entity_id: UUID | None = field(default=None)
    pressing_id: UUID | None = field(default=None)
    album_id: UUID | None = field(default=None)
    summary: str = field(default='')
    user_id: UUID | None = field(default=None)
    user_name: str | None = field(default=None)
    user_email: str | None = field(default=None)

    def _payload(self) -> Dict[str, Any]:
        return {
            'operation': self.operation,
            'entity_type': self.entity_type,
            'entity_id': str(self.entity_id) if self.entity_id else None,
            'pressing_id': str(self.pressing_id) if self.pressing_id else None,
            'album_id': str(self.album_id) if self.album_id else None,
            'summary': self.summary,
            'user_id': str(self.user_id) if self.user_id else None,
            'user_name': self.user_name,
            'user_email': self.user_email
        }
