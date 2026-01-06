/**
 * Modal for viewing album details with list of pressings and actions.
 */

import { useState, useEffect, useMemo } from 'react';
import { useMsal } from '@azure/msal-react';
import { Modal } from '../UI/Modal';
import { Loading, ErrorAlert, Icon } from '../UI';
import { PressingListItem } from '../PressingListItem';
import { PressingWizardModal } from './PressingWizardModal';
import { CollectionItemForm } from '../Forms';
import { albumsApi, artistsApi, lookupApi, pressingsApi } from '@/api/services';
import {
  AlbumResponse,
  PressingResponse,
  GenreResponse,
  StyleResponse,
  ReleaseTypeResponse,
} from '@/types/api';
import { mdiMusicBoxOutline } from '@mdi/js';
import { usePressingOwners } from '@/hooks/usePressingOwners';
import '../Forms/Form.css';
import './AlbumDetailsModal.css';

interface AlbumDetailsModalProps {
  albumId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function AlbumDetailsModal({ albumId, isOpen, onClose }: AlbumDetailsModalProps) {
  const { accounts } = useMsal();
  const currentUserId = (accounts[0]?.idTokenClaims?.oid as string) || accounts[0]?.localAccountId || '';
  const [album, setAlbum] = useState<AlbumResponse | null>(null);
  const [pressings, setPressings] = useState<PressingResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [genreLookup, setGenreLookup] = useState<Record<string, string>>({});
  const [styleLookup, setStyleLookup] = useState<Record<string, string>>({});
  const [releaseTypeLookup, setReleaseTypeLookup] = useState<Record<string, string>>({});
  const [artistName, setArtistName] = useState<string>('');
  const [expandedMasters, setExpandedMasters] = useState<Set<string>>(new Set());

  // Nested modal states
  const [showAddPressingModal, setShowAddPressingModal] = useState(false);
  const [showAddToCollectionModal, setShowAddToCollectionModal] = useState(false);
  const [selectedPressingId, setSelectedPressingId] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && albumId) {
      fetchData();
    }
  }, [isOpen, albumId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [albumData, pressingsData, genresData, stylesData, releaseTypesData] = await Promise.all([
        albumsApi.getById(albumId),
        pressingsApi.getByAlbum(albumId, { limit: 100 }),
        lookupApi.getAllGenres(),
        lookupApi.getAllStyles(),
        lookupApi.getAllReleaseTypes(),
      ]);

      setAlbum(albumData);
      setPressings(pressingsData.items);
      setArtistName('');
      if (genresData.length > 0) {
        const map: Record<string, string> = {};
        genresData.forEach((genre: GenreResponse) => {
          map[genre.id] = genre.name;
        });
        setGenreLookup(map);
      }
      if (stylesData.length > 0) {
        const map: Record<string, string> = {};
        stylesData.forEach((style: StyleResponse) => {
          map[style.id] = style.name;
        });
        setStyleLookup(map);
      }
      if (releaseTypesData.length > 0) {
        const map: Record<string, string> = {};
        releaseTypesData.forEach((releaseType: ReleaseTypeResponse) => {
          map[releaseType.code] = releaseType.name;
        });
        setReleaseTypeLookup(map);
      }

      const artistId = albumData.artist_id || albumData.primary_artist_id;
      if (artistId) {
        try {
          const artist = await artistsApi.getById(artistId);
          setArtistName(artist.name);
        } catch (artistErr) {
          console.error('Failed to load artist details:', artistErr);
          setArtistName('-');
        }
      } else {
        setArtistName('-');
      }
    } catch (err: any) {
      console.error('Failed to load album details:', err);
      setError(err.response?.data?.detail || 'Failed to load album details');
    } finally {
      setLoading(false);
    }
  };

  const visiblePressingIds = useMemo(
    () => pressings.map((pressing) => pressing.id),
    [pressings]
  );
  const pressingOwners = usePressingOwners(visiblePressingIds);

  const handleAddToCollection = (pressingId: string) => {
    setSelectedPressingId(pressingId);
    setShowAddToCollectionModal(true);
  };

  const handlePressingSuccess = () => {
    setShowAddPressingModal(false); // Close the modal
    fetchData(); // Refresh pressings list
  };

  const handleCollectionSuccess = () => {
    // Could show a success message or refresh collection count
  };

  const getAlbumReleaseYear = (value: AlbumResponse) => {
    return value.release_year ?? value.original_release_year ?? '-';
  };

  const getAlbumCatalogNumber = (value: AlbumResponse) => {
    return value.catalog_number ?? value.catalog_number_base ?? '-';
  };

  const getAlbumNotes = (value: AlbumResponse) => {
    return value.notes ?? value.description ?? '';
  };

  const getAlbumGenres = (value: AlbumResponse) => {
    if (value.genres?.length) {
      return value.genres.map((genre) => genre.name).join(', ');
    }
    if (value.genre_ids?.length) {
      const names = value.genre_ids.map((id) => genreLookup[id]).filter(Boolean);
      if (names.length) {
        return names.join(', ');
      }
    }
    return '-';
  };

  const getAlbumStyles = (value: AlbumResponse) => {
    if (value.styles?.length) {
      return value.styles.map((style) => style.name).join(', ');
    }
    if (value.style_ids?.length) {
      const names = value.style_ids.map((id) => styleLookup[id]).filter(Boolean);
      if (names.length) {
        return names.join(', ');
      }
    }
    return '-';
  };

  const getAlbumReleaseType = (value: AlbumResponse) => {
    const releaseType = value.release_type;
    if (!releaseType) return '-';
    return releaseTypeLookup[releaseType] || releaseType;
  };

  const getAlbumInitial = (value: AlbumResponse) => {
    const title = value.title || '';
    const initial = title.trim().charAt(0);
    return initial ? initial.toUpperCase() : '?';
  };

  const getCountryName = (code: string | undefined): string => {
    if (!code) return '-';
    const countries: Record<string, string> = {
      'US': 'United States',
      'GB': 'United Kingdom',
      'CA': 'Canada',
      'AU': 'Australia',
      'DE': 'Germany',
      'FR': 'France',
      'IT': 'Italy',
      'ES': 'Spain',
      'JP': 'Japan',
      'KR': 'South Korea',
      'CN': 'China',
      'BR': 'Brazil',
      'MX': 'Mexico',
      'AR': 'Argentina',
      'SE': 'Sweden',
      'NO': 'Norway',
      'DK': 'Denmark',
      'FI': 'Finland',
      'NL': 'Netherlands',
      'BE': 'Belgium',
      'AT': 'Austria',
      'CH': 'Switzerland',
      'IE': 'Ireland',
      'NZ': 'New Zealand',
      'ZA': 'South Africa',
      'IN': 'India',
      'RU': 'Russia',
      'PL': 'Poland',
      'CZ': 'Czech Republic',
      'GR': 'Greece',
      'PT': 'Portugal',
      'IS': 'Iceland',
    };
    return countries[code] || code;
  };

  const masterGroups = useMemo(() => {
    const groups = new Map<string, PressingResponse[]>();
    pressings.forEach((pressing) => {
      const masterTitle = pressing.master_title || 'Individual Pressings';
      const entries = groups.get(masterTitle);
      if (entries) {
        entries.push(pressing);
      } else {
        groups.set(masterTitle, [pressing]);
      }
    });
    return groups;
  }, [pressings]);

  const masterTitles = useMemo(() => {
    return Array.from(masterGroups.keys()).sort((a, b) => a.localeCompare(b));
  }, [masterGroups]);

  const showMasterGroups = masterTitles.length > 1;

  useEffect(() => {
    setExpandedMasters(new Set());
  }, [pressings]);

  const toggleMasterGroup = (masterTitle: string) => {
    setExpandedMasters((prev) => {
      const next = new Set(prev);
      if (next.has(masterTitle)) {
        next.delete(masterTitle);
      } else {
        next.add(masterTitle);
      }
      return next;
    });
  };

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} title="Album Details" size="large">
        {loading && <Loading message="Loading album details..." />}

        {error && <ErrorAlert message={error} onRetry={fetchData} />}

        {!loading && !error && album && (
          <div className="album-details">
            <div className="album-details-header">
              <div className="album-details-image">
                {album.image_url ? (
                  <img src={album.image_url} alt={`${album.title} cover`} />
                ) : (
                  <span className="album-details-placeholder">{getAlbumInitial(album)}</span>
                )}
              </div>
              <div className="album-details-info">
                <h3>{album.title}</h3>
                <div className="album-details-meta">
                  <div>
                    <span className="album-details-label">Artist</span>
                    <span>{artistName || '-'}</span>
                  </div>
                  <div>
                    <span className="album-details-label">Release Type</span>
                    <span>{getAlbumReleaseType(album)}</span>
                  </div>
                  <div>
                    <span className="album-details-label">Release Year</span>
                    <span>{getAlbumReleaseYear(album)}</span>
                  </div>
                  <div>
                    <span className="album-details-label">Country</span>
                    <span>{getCountryName(album.country_of_origin)}</span>
                  </div>
                  <div>
                    <span className="album-details-label">Label</span>
                    <span>{album.label || '-'}</span>
                  </div>
                  <div>
                    <span className="album-details-label">Catalog #</span>
                    <span>{getAlbumCatalogNumber(album)}</span>
                  </div>
                  <div>
                    <span className="album-details-label">Genres</span>
                    <span>{getAlbumGenres(album)}</span>
                  </div>
                  <div>
                    <span className="album-details-label">Styles</span>
                    <span>{getAlbumStyles(album)}</span>
                  </div>
                  <div>
                    <span className="album-details-label">Discogs ID</span>
                    <span>{album.discogs_id || '-'}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="album-details-notes">
              <span className="album-details-label">Notes</span>
              <span>{getAlbumNotes(album) || '-'}</span>
            </div>

            {/* Pressings Section */}
            <div>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1rem'
              }}>
                <h4 style={{ margin: 0, color: '#fff' }}>
                  Pressings ({pressings.length})
                </h4>
                <button
                  className="btn-primary"
                  onClick={() => setShowAddPressingModal(true)}
                  style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
                >
                  <Icon path={mdiMusicBoxOutline} className="btn-icon" />
                  Add New Pressing
                </button>
              </div>

              {pressings.length === 0 ? (
                <div style={{
                  padding: '2rem',
                  textAlign: 'center',
                  background: '#2a2a2a',
                  borderRadius: '4px',
                  color: '#999',
                  border: '1px solid #444'
                }}>
                  <p>No pressings found for this album.</p>
                </div>
              ) : (
                <div>
                  {showMasterGroups ? (
                    masterTitles.map((masterTitle) => {
                      const isExpanded = expandedMasters.has(masterTitle);
                      return (
                        <div key={masterTitle} style={{ marginBottom: '1.5rem' }}>
                          <div
                            role="button"
                            aria-expanded={isExpanded}
                            onClick={() => toggleMasterGroup(masterTitle)}
                            style={{
                              margin: '0 0 0.75rem',
                              color: '#fff',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.5rem',
                            }}
                          >
                            <span>{isExpanded ? '▼' : '▶'}</span>
                            <h5 style={{ margin: 0 }}>
                              <strong>MASTER:</strong> {masterTitle}
                            </h5>
                          </div>
                          {isExpanded &&
                            masterGroups.get(masterTitle)?.map((pressing) => (
                              <PressingListItem
                                key={pressing.id}
                                pressing={pressing}
                                onAddToCollection={handleAddToCollection}
                                fallbackImageUrl={album.image_url}
                                owners={pressingOwners[pressing.id] || []}
                                currentUserId={currentUserId}
                              />
                            ))}
                        </div>
                      );
                    })
                  ) : (
                    pressings.map((pressing) => (
                      <PressingListItem
                        key={pressing.id}
                        pressing={pressing}
                        onAddToCollection={handleAddToCollection}
                        fallbackImageUrl={album.image_url}
                        owners={pressingOwners[pressing.id] || []}
                        currentUserId={currentUserId}
                      />
                    ))
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>

      {/* Nested Modals */}
      {album && (
        <PressingWizardModal
          albumId={albumId}
          albumTitle={album.title}
          artistName={artistName}
          discogsId={album.discogs_id}
          isOpen={showAddPressingModal}
          onClose={() => setShowAddPressingModal(false)}
          onSuccess={handlePressingSuccess}
        />
      )}

      {selectedPressingId && (
        <Modal
          isOpen={showAddToCollectionModal}
          onClose={() => {
            setShowAddToCollectionModal(false);
            setSelectedPressingId(null);
          }}
          title="Add to Collection"
          size="medium"
        >
          <CollectionItemForm
            pressingId={selectedPressingId}
            onSuccess={() => {
              setShowAddToCollectionModal(false);
              setSelectedPressingId(null);
              handleCollectionSuccess();
            }}
            onCancel={() => {
              setShowAddToCollectionModal(false);
              setSelectedPressingId(null);
            }}
          />
        </Modal>
      )}
    </>
  );
}
