"""Unit tests for DiscogsTracklistSyncService normalization."""

from unittest.mock import MagicMock

from app.application.services.discogs_tracklist_sync_service import DiscogsTracklistSyncService


def _build_service() -> DiscogsTracklistSyncService:
    return DiscogsTracklistSyncService(
        album_service=MagicMock(),
        discogs_service=MagicMock(),
        track_service=MagicMock(),
    )


def test_normalize_discogs_tracklist_supports_heading_track_and_subtrack() -> None:
    service = _build_service()
    raw = [
        {"type_": "heading", "title": "Suite One"},
        {
            "type_": "track",
            "position": "A1",
            "title": "Main Theme",
            "duration": "4:32",
            "artists": [{"name": "Various"}, {"name": "Artist A"}],
            "sub_tracks": [
                {"title": "Part I", "duration": "1:00", "artists": [{"name": "Artist B"}]},
                {"title": "Part II", "duration": "1:10"},
            ],
        },
    ]

    normalized = service._normalize_discogs_tracklist(raw)

    assert len(normalized) == 4
    assert normalized[0]["layout_type"] == "heading"
    assert normalized[1]["layout_type"] == "track"
    assert normalized[1]["performers"] == ["Various", "Artist A"]
    assert normalized[1]["parent_index"] == 0
    assert normalized[2]["layout_type"] == "subtrack"
    assert normalized[2]["parent_index"] == 1
    assert normalized[2]["performers"] == ["Artist B"]
    assert normalized[3]["layout_type"] == "subtrack"
    assert normalized[3]["performers"] == ["Various", "Artist A"]


def test_normalize_discogs_tracklist_makes_positions_unique() -> None:
    service = _build_service()
    raw = [
        {"type_": "track", "position": "A1", "title": "Song 1"},
        {"type_": "track", "position": "A1", "title": "Song 2"},
    ]

    normalized = service._normalize_discogs_tracklist(raw)

    assert normalized[0]["side"] == "A"
    assert normalized[0]["position"] == "1"
    assert normalized[1]["side"] == "A"
    assert normalized[1]["position"] != normalized[0]["position"]
