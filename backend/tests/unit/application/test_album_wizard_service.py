"""
Unit tests for AlbumWizardService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.application.services.album_wizard_service import AlbumWizardService
from app.domain.entities import Artist, Album


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.artist_repository = AsyncMock()
    uow.album_repository = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow


@pytest.fixture
def mock_client():
    return AsyncMock()


@pytest.fixture
def service(mock_uow, mock_client):
    return AlbumWizardService(uow=mock_uow, wizard_client=mock_client)


@pytest.mark.asyncio
async def test_analyze_cover_calls_client(service, mock_client):
    mock_client.analyze_cover.return_value = {"artist": "A", "album": "B", "image": True}
    result = await service.analyze_cover("data:image/png;base64,abc")
    assert result["artist"] == "A"
    mock_client.analyze_cover.assert_called_once()


@pytest.mark.asyncio
async def test_match_album_no_artist_returns_no_artist_match(service):
    result = await service.match_album(None, "Album")
    assert result.match_status == "no_artist_match"


@pytest.mark.asyncio
async def test_match_album_exact_artist_and_album(service, mock_uow):
    artist = Artist(id=uuid4(), name="The Beatles")
    album = Album(id=uuid4(), title="Revolver", primary_artist_id=artist.id)
    mock_uow.artist_repository.get_by_name.return_value = artist
    mock_uow.album_repository.get_by_title_and_artist.return_value = album

    result = await service.match_album("The Beatles", "Revolver")

    assert result.match_status == "match_found"
    assert result.artist == artist
    assert result.album == album


@pytest.mark.asyncio
async def test_match_album_falls_back_to_artist_search(service, mock_uow):
    artist = Artist(id=uuid4(), name="Miles Davis")
    mock_uow.artist_repository.get_by_name.return_value = None
    mock_uow.artist_repository.search.return_value = ([artist], 1)
    mock_uow.album_repository.get_by_title_and_artist.return_value = None
    mock_uow.album_repository.search_by_title_and_artist.return_value = []

    result = await service.match_album("Miles", "Kind of Blue")

    assert result.match_status == "no_album_match"
    assert result.artist == artist


@pytest.mark.asyncio
async def test_match_album_uses_popular_album_when_needed(service, mock_uow):
    artist = Artist(id=uuid4(), name="Prince")
    album = Album(id=uuid4(), title="Purple Rain", primary_artist_id=artist.id)
    mock_uow.artist_repository.get_by_name.return_value = artist
    mock_uow.album_repository.get_by_title_and_artist.side_effect = [None, album]

    result = await service.match_album("Prince", "Unknown Album", popular_album="Purple Rain")

    assert result.match_status == "match_found"
    assert result.album == album
