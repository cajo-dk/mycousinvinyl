/**
 * Modal for searching and selecting Discogs releases for a pressing.
 * Groups releases by master title and allows selection to auto-fill pressing form.
 */

import { useState, useEffect, useMemo } from 'react';
import { Modal } from '../UI/Modal';
import { Loading, ErrorAlert, Icon } from '../UI';
import { discogsApi } from '@/api/services';
import type { DiscogsReleaseSearchResult, DiscogsReleaseDetails } from '@/types/api';
import { mdiInformationBoxOutline } from '@mdi/js';
import './DiscogsReleaseSearchModal.css';

interface DiscogsReleaseSearchModalProps {
  albumId: string;
  isOpen: boolean;
  onClose: () => void;
  onSelectRelease: (release: DiscogsReleaseDetails) => void;
}

interface MasterGroup {
  masterTitle: string;
  masterDiscogId?: number;
  releases: DiscogsReleaseSearchResult[];
}

export function DiscogsReleaseSearchModal({
  albumId,
  isOpen,
  onClose,
  onSelectRelease,
}: DiscogsReleaseSearchModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [releases, setReleases] = useState<DiscogsReleaseSearchResult[]>([]);
  const [expandedMasters, setExpandedMasters] = useState<Set<string>>(new Set());
  const [selectedReleaseId, setSelectedReleaseId] = useState<number | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [openInfoBox, setOpenInfoBox] = useState<{ type: 'master' | 'pressing', id: string | number } | null>(null);

  useEffect(() => {
    if (isOpen && albumId) {
      fetchReleases();
    }
  }, [isOpen, albumId]);

  const fetchReleases = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await discogsApi.getAlbumReleases(albumId);

      // Backend returns only actual releases (masters are used for grouping only)
      setReleases(response.items);

      // Expand all groups by default
      const masterTitles = new Set(response.items.map(r => r.master_title || 'Unknown Master'));
      setExpandedMasters(masterTitles);
    } catch (err: any) {
      console.error('Failed to fetch Discogs releases:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to fetch releases');
    } finally {
      setLoading(false);
    }
  };

  const groupedReleases = useMemo<MasterGroup[]>(() => {
    const groups = new Map<string, MasterGroup>();

    releases.forEach(release => {
      const masterTitle = release.master_title || 'Unknown Master';

      if (!groups.has(masterTitle)) {
        groups.set(masterTitle, {
          masterTitle,
          masterDiscogId: release.master_id,
          releases: [],
        });
      }

      groups.get(masterTitle)!.releases.push(release);
    });

    return Array.from(groups.values()).sort((a, b) =>
      a.masterTitle.localeCompare(b.masterTitle)
    );
  }, [releases]);

  const toggleMaster = (masterTitle: string) => {
    const newExpanded = new Set(expandedMasters);
    if (newExpanded.has(masterTitle)) {
      newExpanded.delete(masterTitle);
    } else {
      newExpanded.add(masterTitle);
    }
    setExpandedMasters(newExpanded);
  };

  const handleSelectRelease = async (releaseId: number) => {
    try {
      setLoadingDetails(true);
      setSelectedReleaseId(releaseId);

      // Fetch full release details
      const releaseDetails = await discogsApi.getRelease(releaseId);

      // Call parent callback with details
      onSelectRelease(releaseDetails);
      onClose();
    } catch (err: any) {
      console.error('Failed to fetch release details:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to fetch release details');
    } finally {
      setLoadingDetails(false);
      setSelectedReleaseId(null);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Search Discogs Releases"
      size="large"
    >
      <div className="discogs-release-search">
        {loading && <Loading message="Fetching releases from Discogs..." />}

        {error && (
          <ErrorAlert
            message={error}
            onRetry={fetchReleases}
          />
        )}

        {!loading && !error && releases.length === 0 && (
          <div className="no-releases">
            <p>No releases found for this album on Discogs.</p>
            <p>Make sure the album has a valid Discogs master ID.</p>
          </div>
        )}

        {!loading && releases.length > 0 && (
          <div className="releases-container">
            <p className="releases-info">
              Found {releases.length} release{releases.length !== 1 ? 's' : ''}
              {' '}in {groupedReleases.length} master group{groupedReleases.length !== 1 ? 's' : ''}
            </p>

            <div className="master-groups">
              {groupedReleases.map(group => {
                // Get master ID from first release in group (they all share same master_id)
                const masterId = group.releases[0]?.master_id;

                return (
                  <div key={group.masterTitle} className="master-group">
                    <div className="master-header">
                      <div
                        className="master-header-main"
                        onClick={() => toggleMaster(group.masterTitle)}
                        style={{ flex: 1, display: 'flex', alignItems: 'center', cursor: 'pointer' }}
                      >
                        <span className="expand-icon">
                          {expandedMasters.has(group.masterTitle) ? '▼' : '▶'}
                        </span>
                        <span className="master-title">{group.masterTitle}</span>
                        <span className="release-count">
                          ({group.releases.length} release{group.releases.length !== 1 ? 's' : ''})
                        </span>
                      </div>
                      {masterId && (
                        <button
                          type="button"
                          className="info-icon-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            setOpenInfoBox(
                              openInfoBox?.type === 'master' && openInfoBox?.id === group.masterTitle
                                ? null
                                : { type: 'master', id: group.masterTitle }
                            );
                          }}
                          style={{ padding: '4px', background: 'none', border: 'none', cursor: 'pointer' }}
                        >
                          <Icon path={mdiInformationBoxOutline} size={18} />
                        </button>
                      )}
                    </div>
                    {openInfoBox?.type === 'master' && openInfoBox?.id === group.masterTitle && masterId && (
                      <div className="info-box" style={{
                        padding: '0.75rem',
                        background: '#f5f5f5',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        marginBottom: '0.5rem',
                        fontSize: '0.9rem'
                      }}>
                        <div><strong>Discogs Master ID:</strong> {masterId}</div>
                        <div><strong>Total Releases:</strong> {group.releases.length}</div>
                        <div style={{ marginTop: '0.5rem' }}>
                          <a
                            href={`https://www.discogs.com/master/${masterId}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: '#007bff', textDecoration: 'none' }}
                          >
                            View on Discogs →
                          </a>
                        </div>
                      </div>
                    )}

                    {expandedMasters.has(group.masterTitle) && (
                      <div className="releases-list">
                        {group.releases.map(release => {
                          const isInfoOpen = openInfoBox?.type === 'pressing' && openInfoBox?.id === release.id;

                          return (
                            <div key={release.id} style={{ position: 'relative' }}>
                              <div
                                className={`release-item ${selectedReleaseId === release.id ? 'selecting' : ''}`}
                                onClick={() => handleSelectRelease(release.id)}
                                style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}
                              >
                                <div style={{ flex: 1 }}>
                                  <div className="release-main">
                                    <span className="release-title">{release.title}</span>
                                    {release.year && <span className="release-year">({release.year})</span>}
                                  </div>
                                  <div className="release-details">
                                    {release.country && <span className="detail-badge">{release.country}</span>}
                                    {release.label && <span className="detail-badge">{release.label}</span>}
                                    {release.format && <span className="detail-badge format">{release.format}</span>}
                                  </div>
                                  {(release.barcode || release.identifiers) && (
                                    <div className="release-identifiers">
                                      {release.barcode && <span className="detail-badge">Barcode: {release.barcode}</span>}
                                      {release.identifiers && <span className="detail-badge">ID: {release.identifiers}</span>}
                                    </div>
                                  )}
                                  {selectedReleaseId === release.id && loadingDetails && (
                                    <div className="selecting-indicator">Loading details...</div>
                                  )}
                                </div>
                                <button
                                  type="button"
                                  className="info-icon-btn"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setOpenInfoBox(isInfoOpen ? null : { type: 'pressing', id: release.id });
                                  }}
                                  style={{
                                    padding: '4px',
                                    background: 'none',
                                    border: 'none',
                                    cursor: 'pointer'
                                  }}
                                >
                                  <Icon path={mdiInformationBoxOutline} size={16} />
                                </button>
                              </div>
                              {isInfoOpen && (
                                <div className="info-box" style={{
                                  padding: '0.75rem',
                                  background: '#f5f5f5',
                                  border: '1px solid #ddd',
                                  borderRadius: '4px',
                                  marginTop: '0.5rem',
                                  fontSize: '0.85rem'
                                }}>
                                  <div style={{ marginBottom: '0.5rem' }}>
                                    <strong>Discogs Release ID:</strong> {release.id}
                                  </div>
                                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                                    {release.year && <div><strong>Year:</strong> {release.year}</div>}
                                    {release.country && <div><strong>Country:</strong> {release.country}</div>}
                                    {release.label && <div><strong>Label:</strong> {release.label}</div>}
                                    {release.catalog_number && <div><strong>Catalog:</strong> {release.catalog_number}</div>}
                                    {release.format && <div><strong>Format:</strong> {release.format}</div>}
                                    {release.barcode && <div><strong>Barcode:</strong> {release.barcode}</div>}
                                  </div>
                                  {release.identifiers && (
                                    <div style={{ marginTop: '0.5rem' }}>
                                      <strong>Other Identifiers:</strong><br />
                                      {release.identifiers}
                                    </div>
                                  )}
                                  <div style={{ marginTop: '0.5rem' }}>
                                    <a
                                      href={`https://www.discogs.com/release/${release.id}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      style={{ color: '#007bff', textDecoration: 'none' }}
                                    >
                                      View on Discogs →
                                    </a>
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
