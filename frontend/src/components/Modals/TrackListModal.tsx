import { useCallback, useEffect, useMemo, useState } from 'react';
import { albumsApi, tracksApi } from '@/api/services';
import { TrackResponse } from '@/types/api';
import { Modal, Loading, ErrorAlert } from '@/components/UI';
import './TrackListModal.css';

interface TrackListModalProps {
  isOpen: boolean;
  albumId: string | null;
  albumTitle?: string;
  artistName?: string;
  pressingId?: string;
  onClose: () => void;
}

function formatDuration(duration?: number) {
  if (duration === null || duration === undefined || Number.isNaN(duration)) {
    return '-';
  }
  const minutes = Math.floor(duration / 60);
  const seconds = duration % 60;
  return `${minutes}:${String(seconds).padStart(2, '0')}`;
}

export function TrackListModal({
  isOpen,
  albumId,
  albumTitle,
  artistName,
  pressingId,
  onClose,
}: TrackListModalProps) {
  const [tracks, setTracks] = useState<TrackResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  const loadTracks = useCallback(async () => {
    if (!albumId) {
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const response = await tracksApi.getByAlbum(albumId);
      if (response.length > 0) {
        setTracks(response);
        return;
      }

      // No tracklist yet: import from Discogs on demand.
      setSyncing(true);
      await albumsApi.update(albumId, {
        sync_tracklist_from_discogs: true,
        sync_pressing_id: pressingId,
        sync_artist_name: artistName,
        sync_album_name: albumTitle,
      });
      const refreshed = await tracksApi.getByAlbum(albumId);
      setTracks(refreshed);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load track list');
    } finally {
      setSyncing(false);
      setLoading(false);
    }
  }, [albumId, albumTitle, artistName, pressingId]);

  useEffect(() => {
    if (!isOpen || !albumId) {
      return;
    }
    loadTracks();
  }, [isOpen, loadTracks]);

  const groupedTracks = useMemo(() => {
    const groups = new Map<string, TrackResponse[]>();
    tracks.forEach((track) => {
      const side = (track.side || 'A').toUpperCase();
      const entries = groups.get(side);
      if (entries) {
        entries.push(track);
      } else {
        groups.set(side, [track]);
      }
    });
    return Array.from(groups.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [tracks]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Track List${albumTitle ? ` - ${albumTitle}` : ''}`} size="large">
      <div className="track-list-modal">
        {loading && !syncing && <Loading message="Loading track list..." />}
        {syncing && (
          <div className="track-list-banner">Please wait, importing track list from Discogs...</div>
        )}
        {error && <ErrorAlert message={error} onRetry={loadTracks} />}

        {!loading && !error && tracks.length === 0 && (
          <div className="track-list-empty">No tracks available for this album.</div>
        )}

        {!loading && !error && tracks.length > 0 && (
          <div className="track-list-groups">
            {groupedTracks.map(([side, sideTracks]) => (
              <section key={side} className="track-list-side">
                <h4>Side {side}</h4>
                <table className="data-table track-list-table">
                  <thead>
                    <tr>
                      <th className="col-position">#</th>
                      <th className="col-title">Title</th>
                      <th className="col-duration">Duration</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sideTracks.map((track) => (
                      <tr key={track.id}>
                        <td className="col-position">{track.position || '-'}</td>
                        <td className="col-title">{track.title}</td>
                        <td className="col-duration">{formatDuration(track.duration)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </section>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
}
