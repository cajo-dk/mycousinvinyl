import { Fragment, useCallback, useEffect, useMemo, useState } from 'react';
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
  discogsReleaseId?: number;
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
  discogsReleaseId,
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
      const hasPerformerData = response.some((track) => (track.performers || []).length > 0);
      const shouldRefreshFromDiscogs = response.length === 0 || (!!discogsReleaseId && !hasPerformerData);

      if (!shouldRefreshFromDiscogs) {
        setTracks(response);
        return;
      }

      // Tracklist missing or missing performer data: import from Discogs on demand.
      setSyncing(true);
      await albumsApi.update(albumId, {
        sync_tracklist_from_discogs: true,
        sync_pressing_id: pressingId,
        sync_discogs_release_id: discogsReleaseId,
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
  }, [albumId, albumTitle, artistName, pressingId, discogsReleaseId]);

  useEffect(() => {
    if (!isOpen || !albumId) {
      return;
    }
    loadTracks();
  }, [isOpen, loadTracks]);

  const groupedTracks = useMemo(() => {
    const byParent = new Map<string, TrackResponse[]>();
    const rootsBySide = new Map<string, TrackResponse[]>();
    const sorted = [...tracks].sort((a, b) => a.layout_order - b.layout_order);

    sorted.forEach((track) => {
      const parentId = track.parent_track_id;
      if (parentId) {
        const children = byParent.get(parentId) || [];
        children.push(track);
        byParent.set(parentId, children);
        return;
      }
      const side = (track.side || 'A').toUpperCase();
      const roots = rootsBySide.get(side) || [];
      roots.push(track);
      rootsBySide.set(side, roots);
    });

    return Array.from(rootsBySide.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([side, rootNodes]) => ({ side, rootNodes, byParent }));
  }, [tracks]);

  const renderTrackRows = useCallback((track: TrackResponse, byParent: Map<string, TrackResponse[]>, depth = 0) => {
    const children = byParent.get(track.id) || [];
    const artistText = track.performers?.length ? track.performers.join(', ') : '-';

    if (track.layout_type === 'heading') {
      return (
        <Fragment key={track.id}>
          <tr key={track.id} className="track-row-heading">
            <td className="col-heading" colSpan={4}>{track.title}</td>
          </tr>
          {children.map((child) => renderTrackRows(child, byParent, 1))}
        </Fragment>
      );
    }

    const rowClass = track.layout_type === 'subtrack' ? 'track-row-subtrack' : 'track-row-track';
    return (
      <Fragment key={track.id}>
        <tr key={track.id} className={rowClass}>
          <td className="col-position">{track.position || '-'}</td>
          <td className={`col-title depth-${Math.min(depth, 3)}`}>{track.title}</td>
          <td className="col-performers">{artistText}</td>
          <td className="col-duration">{formatDuration(track.duration)}</td>
        </tr>
        {children.map((child) => renderTrackRows(child, byParent, depth + 1))}
      </Fragment>
    );
  }, []);

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
            {groupedTracks.map((group) => (
              <section key={group.side} className="track-list-side">
                <h4>Side {group.side}</h4>
                <table className="data-table track-list-table">
                  <thead>
                    <tr>
                      <th className="col-position">#</th>
                      <th className="col-title">Title</th>
                      <th className="col-performers">Performed By</th>
                      <th className="col-duration">Duration</th>
                    </tr>
                  </thead>
                  <tbody>
                    {group.rootNodes.map((track) => renderTrackRows(track, group.byParent))}
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
