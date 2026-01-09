"""
Unit tests for ArtistService.

Tests business orchestration logic using mocked repositories.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, call
from uuid import uuid4, UUID

from app.application.services.artist_service import ArtistService
from app.domain.entities import Artist
from app.domain.value_objects import ArtistType
from app.domain.events import ArtistCreated, ArtistUpdated, ArtistDeleted, ActivityEvent


@pytest.fixture
def mock_uow():
    """Create a mock Unit of Work."""
    uow = MagicMock()
    uow.artist_repository = AsyncMock()
    uow.outbox_repository = AsyncMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    # Make UoW work as async context manager
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)

    return uow


@pytest.fixture
def artist_service(mock_uow):
    """Create ArtistService with mocked UoW."""
    return ArtistService(uow=mock_uow)


class TestCreateArtist:
    """Test artist creation."""

    @pytest.mark.asyncio
    async def test_create_artist_with_valid_data(self, artist_service, mock_uow):
        """Should create artist and emit event."""
        # Arrange
        artist_data = {
            "name": "The Beatles",
            "type": ArtistType.GROUP,
            "country": "GBR",
        }
        created_artist = Artist(
            id=uuid4(),
            name="The Beatles",
            type=ArtistType.GROUP,
            country="GBR",
        )
        mock_uow.artist_repository.add.return_value = created_artist

        # Act
        result = await artist_service.create_artist(**artist_data)

        # Assert
        assert result.name == "The Beatles"
        assert result.type == ArtistType.GROUP
        assert result.country == "GBR"

        # Verify repository was called
        mock_uow.artist_repository.add.assert_called_once()

        # Verify event was emitted
        assert mock_uow.outbox_repository.add_event.call_count == 2
        events = [call.kwargs for call in mock_uow.outbox_repository.add_event.call_args_list]
        artist_event = next(evt for evt in events if isinstance(evt['event'], ArtistCreated))
        activity_event = next(evt for evt in events if isinstance(evt['event'], ActivityEvent))
        assert artist_event['aggregate_type'] == 'Artist'
        assert artist_event['destination'] == '/topic/artist.created'
        assert activity_event['destination'] == '/topic/system.activity'

        # Verify transaction was committed
        mock_uow.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_artist_with_minimal_data(self, artist_service, mock_uow):
        """Should create artist with only required name field."""
        created_artist = Artist(id=uuid4(), name="Miles Davis")
        mock_uow.artist_repository.add.return_value = created_artist

        result = await artist_service.create_artist(name="Miles Davis")

        assert result.name == "Miles Davis"
        assert result.type == ArtistType.PERSON  # default
        mock_uow.artist_repository.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_artist_with_created_by(self, artist_service, mock_uow):
        """Should track who created the artist."""
        user_id = uuid4()
        created_artist = Artist(
            id=uuid4(),
            name="Bob Dylan",
            created_by=user_id,
        )
        mock_uow.artist_repository.add.return_value = created_artist

        result = await artist_service.create_artist(
            name="Bob Dylan",
            created_by=user_id,
        )

        assert result.created_by == user_id

        # Verify event includes created_by
        events = [call.kwargs['event'] for call in mock_uow.outbox_repository.add_event.call_args_list]
        artist_event = next(evt for evt in events if isinstance(evt, ArtistCreated))
        assert artist_event.created_by == user_id

    @pytest.mark.asyncio
    async def test_create_artist_with_extra_fields(self, artist_service, mock_uow):
        """Should handle additional fields like aliases, notes."""
        created_artist = Artist(
            id=uuid4(),
            name="Prince",
            aliases=["The Artist Formerly Known as Prince", "TAFKAP"],
            notes="Legendary musician",
        )
        mock_uow.artist_repository.add.return_value = created_artist

        result = await artist_service.create_artist(
            name="Prince",
            aliases=["The Artist Formerly Known as Prince", "TAFKAP"],
            notes="Legendary musician",
        )

        assert result.name == "Prince"
        assert len(result.aliases) == 2
        assert result.notes == "Legendary musician"

    @pytest.mark.asyncio
    async def test_create_artist_invalid_name_raises_error(self, artist_service, mock_uow):
        """Should raise ValueError for empty name."""
        with pytest.raises(ValueError, match="Artist name is required"):
            await artist_service.create_artist(name="")


class TestGetArtist:
    """Test retrieving artist by ID."""

    @pytest.mark.asyncio
    async def test_get_existing_artist(self, artist_service, mock_uow):
        """Should return artist when found."""
        artist_id = uuid4()
        expected_artist = Artist(id=artist_id, name="The Beatles")
        mock_uow.artist_repository.get.return_value = expected_artist

        result = await artist_service.get_artist(artist_id)

        assert result is not None
        assert result.id == artist_id
        assert result.name == "The Beatles"
        mock_uow.artist_repository.get.assert_called_once_with(artist_id)

    @pytest.mark.asyncio
    async def test_get_nonexistent_artist(self, artist_service, mock_uow):
        """Should return None when artist not found."""
        artist_id = uuid4()
        mock_uow.artist_repository.get.return_value = None

        result = await artist_service.get_artist(artist_id)

        assert result is None
        mock_uow.artist_repository.get.assert_called_once_with(artist_id)


class TestSearchArtists:
    """Test artist search functionality."""

    @pytest.mark.asyncio
    async def test_search_artists_with_results(self, artist_service, mock_uow):
        """Should return matching artists."""
        artists = [
            Artist(id=uuid4(), name="The Beatles"),
            Artist(id=uuid4(), name="The Rolling Stones"),
        ]
        mock_uow.artist_repository.search.return_value = (artists, 2)

        results, total = await artist_service.search_artists("The", limit=10, offset=0)

        assert len(results) == 2
        assert total == 2
        assert results[0].name == "The Beatles"
        mock_uow.artist_repository.search.assert_called_once_with("The", 10, 0)

    @pytest.mark.asyncio
    async def test_search_artists_no_results(self, artist_service, mock_uow):
        """Should return empty list when no matches."""
        mock_uow.artist_repository.search.return_value = ([], 0)

        results, total = await artist_service.search_artists("XYZ")

        assert len(results) == 0
        assert total == 0

    @pytest.mark.asyncio
    async def test_search_artists_with_pagination(self, artist_service, mock_uow):
        """Should handle pagination parameters."""
        artists = [Artist(id=uuid4(), name="Artist 3")]
        mock_uow.artist_repository.search.return_value = (artists, 10)

        results, total = await artist_service.search_artists(
            "Artist",
            limit=1,
            offset=2
        )

        assert len(results) == 1
        assert total == 10
        mock_uow.artist_repository.search.assert_called_once_with("Artist", 1, 2)


class TestListArtists:
    """Test listing all artists."""

    @pytest.mark.asyncio
    async def test_list_artists_default_params(self, artist_service, mock_uow):
        """Should list artists with default pagination."""
        artists = [
            Artist(id=uuid4(), name="Artist 1"),
            Artist(id=uuid4(), name="Artist 2"),
        ]
        mock_uow.artist_repository.get_all.return_value = (artists, 2)

        results, total = await artist_service.list_artists()

        assert len(results) == 2
        assert total == 2
        mock_uow.artist_repository.get_all.assert_called_once_with(100, 0, "name")

    @pytest.mark.asyncio
    async def test_list_artists_with_custom_pagination(self, artist_service, mock_uow):
        """Should handle custom pagination parameters."""
        artists = [Artist(id=uuid4(), name="Artist 11")]
        mock_uow.artist_repository.get_all.return_value = (artists, 50)

        results, total = await artist_service.list_artists(limit=10, offset=10)

        assert len(results) == 1
        assert total == 50
        mock_uow.artist_repository.get_all.assert_called_once_with(10, 10, "name")

    @pytest.mark.asyncio
    async def test_list_artists_with_custom_sort(self, artist_service, mock_uow):
        """Should handle custom sort parameter."""
        artists = []
        mock_uow.artist_repository.get_all.return_value = (artists, 0)

        await artist_service.list_artists(sort_by="country")

        mock_uow.artist_repository.get_all.assert_called_once_with(100, 0, "country")


class TestUpdateArtist:
    """Test artist update functionality."""

    @pytest.mark.asyncio
    async def test_update_existing_artist(self, artist_service, mock_uow):
        """Should update artist and emit event."""
        artist_id = uuid4()
        existing_artist = Artist(id=artist_id, name="The Beatles")
        updated_artist = Artist(
            id=artist_id,
            name="Beatles",
            country="GBR"
        )

        mock_uow.artist_repository.get.return_value = existing_artist
        mock_uow.artist_repository.update.return_value = updated_artist

        result = await artist_service.update_artist(
            artist_id,
            name="Beatles",
            country="GBR"
        )

        assert result is not None
        assert result.name == "Beatles"
        assert result.country == "GBR"

        # Verify update was called
        mock_uow.artist_repository.update.assert_called_once()

        # Verify event was emitted
        assert mock_uow.outbox_repository.add_event.call_count == 2
        events = [call.kwargs for call in mock_uow.outbox_repository.add_event.call_args_list]
        artist_event = next(evt for evt in events if isinstance(evt['event'], ArtistUpdated))
        activity_event = next(evt for evt in events if isinstance(evt['event'], ActivityEvent))
        assert artist_event['destination'] == '/topic/artist.updated'
        assert activity_event['destination'] == '/topic/system.activity'

        # Verify transaction was committed
        mock_uow.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_nonexistent_artist(self, artist_service, mock_uow):
        """Should return None when artist not found."""
        artist_id = uuid4()
        mock_uow.artist_repository.get.return_value = None

        result = await artist_service.update_artist(artist_id, name="New Name")

        assert result is None
        mock_uow.artist_repository.update.assert_not_called()
        mock_uow.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_artist_partial_fields(self, artist_service, mock_uow):
        """Should update only provided fields."""
        artist_id = uuid4()
        existing_artist = Artist(
            id=artist_id,
            name="The Beatles",
            country="GBR"
        )
        updated_artist = Artist(
            id=artist_id,
            name="The Beatles",
            country="UK"
        )

        mock_uow.artist_repository.get.return_value = existing_artist
        mock_uow.artist_repository.update.return_value = updated_artist

        result = await artist_service.update_artist(artist_id, country="UK")

        assert result.country == "UK"

        # Verify event contains only updated fields
        events = [call.kwargs['event'] for call in mock_uow.outbox_repository.add_event.call_args_list]
        artist_event = next(evt for evt in events if isinstance(evt, ArtistUpdated))
        assert artist_event.updated_fields == {"country": "UK"}

    @pytest.mark.asyncio
    async def test_update_artist_begin_date_clears_active_years(self, artist_service, mock_uow):
        """Should clear active_years so it can be rebuilt from begin/end dates."""
        artist_id = uuid4()
        existing_artist = Artist(
            id=artist_id,
            name="The Beatles",
            begin_date="1960",
            end_date="1970",
            active_years="1960-1970"
        )
        updated_artist = Artist(
            id=artist_id,
            name="The Beatles",
            begin_date="1961",
            end_date="1970",
            active_years=None
        )

        mock_uow.artist_repository.get.return_value = existing_artist
        mock_uow.artist_repository.update.return_value = updated_artist

        result = await artist_service.update_artist(artist_id, begin_date="1961")

        assert result.begin_date == "1961"
        assert existing_artist.active_years is None


class TestDeleteArtist:
    """Test artist deletion."""

    @pytest.mark.asyncio
    async def test_delete_existing_artist(self, artist_service, mock_uow):
        """Should delete artist and emit event."""
        artist_id = uuid4()
        existing_artist = Artist(id=artist_id, name="The Beatles")
        mock_uow.artist_repository.get.return_value = existing_artist

        result = await artist_service.delete_artist(artist_id)

        assert result is True
        mock_uow.artist_repository.delete.assert_called_once_with(artist_id)

        # Verify event was emitted
        assert mock_uow.outbox_repository.add_event.call_count == 2
        events = [call.kwargs for call in mock_uow.outbox_repository.add_event.call_args_list]
        artist_event = next(evt for evt in events if isinstance(evt['event'], ArtistDeleted))
        activity_event = next(evt for evt in events if isinstance(evt['event'], ActivityEvent))
        assert artist_event['destination'] == '/topic/artist.deleted'
        assert activity_event['destination'] == '/topic/system.activity'

        # Verify transaction was committed
        mock_uow.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_artist(self, artist_service, mock_uow):
        """Should return False when artist not found."""
        artist_id = uuid4()
        mock_uow.artist_repository.get.return_value = None

        result = await artist_service.delete_artist(artist_id)

        assert result is False
        mock_uow.artist_repository.delete.assert_not_called()
        mock_uow.commit.assert_not_called()


class TestCheckArtistExists:
    """Test artist existence check."""

    @pytest.mark.asyncio
    async def test_check_existing_artist(self, artist_service, mock_uow):
        """Should return True when artist exists."""
        artist_id = uuid4()
        mock_uow.artist_repository.exists.return_value = True

        result = await artist_service.check_artist_exists(artist_id)

        assert result is True
        mock_uow.artist_repository.exists.assert_called_once_with(artist_id)

    @pytest.mark.asyncio
    async def test_check_nonexistent_artist(self, artist_service, mock_uow):
        """Should return False when artist doesn't exist."""
        artist_id = uuid4()
        mock_uow.artist_repository.exists.return_value = False

        result = await artist_service.check_artist_exists(artist_id)

        assert result is False
        mock_uow.artist_repository.exists.assert_called_once_with(artist_id)


class TestTransactionBehavior:
    """Test UnitOfWork transaction handling."""

    @pytest.mark.asyncio
    async def test_create_uses_transaction(self, artist_service, mock_uow):
        """Should use UoW transaction for create."""
        created_artist = Artist(id=uuid4(), name="Test Artist")
        mock_uow.artist_repository.add.return_value = created_artist

        await artist_service.create_artist(name="Test Artist")

        # Verify UoW context manager was used
        mock_uow.__aenter__.assert_called_once()
        mock_uow.__aexit__.assert_called_once()

        # Verify commit was called
        mock_uow.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_uses_transaction(self, artist_service, mock_uow):
        """Should use UoW transaction for update."""
        artist_id = uuid4()
        existing_artist = Artist(id=artist_id, name="Old Name")
        updated_artist = Artist(id=artist_id, name="New Name")

        mock_uow.artist_repository.get.return_value = existing_artist
        mock_uow.artist_repository.update.return_value = updated_artist

        await artist_service.update_artist(artist_id, name="New Name")

        mock_uow.__aenter__.assert_called_once()
        mock_uow.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_uses_transaction(self, artist_service, mock_uow):
        """Should use UoW transaction for delete."""
        artist_id = uuid4()
        existing_artist = Artist(id=artist_id, name="Test Artist")
        mock_uow.artist_repository.get.return_value = existing_artist

        await artist_service.delete_artist(artist_id)

        mock_uow.__aenter__.assert_called_once()
        mock_uow.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_operations_use_transaction(self, artist_service, mock_uow):
        """Should use UoW transaction for read operations."""
        artist_id = uuid4()
        mock_uow.artist_repository.get.return_value = None

        await artist_service.get_artist(artist_id)

        # Verify UoW context manager was used (but no commit for read-only)
        mock_uow.__aenter__.assert_called_once()
        mock_uow.commit.assert_not_called()
