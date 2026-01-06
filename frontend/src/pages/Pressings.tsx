/**
 * Pressings page - browse pressings with two-level hierarchy: Artist → Album → Pressing.
 */

import { useState, useEffect, useMemo } from 'react';
import { useMsal } from '@azure/msal-react';
import { pressingsApi } from '@/api/services';
import { PressingDetailResponse } from '@/types/api';
import { Loading, ErrorAlert, Modal, Icon } from '@/components/UI';
import { PressingForm, CollectionItemForm } from '@/components/Forms';
import { PressingWizardModal } from '@/components/Modals';
import { OwnersGrid } from '@/components/CollectionSharing';
import { mdiPencilOutline, mdiTrashCanOutline, mdiMusicBoxOutline, mdiPlus } from '@mdi/js';
import { AlphabetFilterBar } from '@/components/AlphabetFilterBar';
import { getInitialToken } from '@/utils/alpha';
import { usePreferences } from '@/hooks/usePreferences';
import { resolveItemsPerPage } from '@/utils/preferences';
import { useViewControls } from '@/components/Layout/ViewControlsContext';
import { usePressingOwners } from '@/hooks/usePressingOwners';
import './Pressings.css';
import '../styles/Table.css';

// Group pressings by artist, album, and master
interface ArtistGroup {
  artistId: string;
  artistName: string;
  sortName: string;
  artistDiscogsId: number | null;
  albums: AlbumGroup[];
}

interface AlbumGroup {
  albumId: string;
  albumTitle: string;
  releaseYear: number | undefined;
  albumDiscogsId: number | null;
  masters: MasterGroup[];
}

interface MasterGroup {
  masterTitle: string;
  pressings: PressingDetailResponse[];
}

export function Pressings() {
  const { accounts } = useMsal();
  const currentUserId = (accounts[0]?.idTokenClaims?.oid as string) || accounts[0]?.localAccountId || '';
  const [pressings, setPressings] = useState<PressingDetailResponse[]>([]);
  const [groupedData, setGroupedData] = useState<ArtistGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showAddToCollectionModal, setShowAddToCollectionModal] = useState(false);
  const [selectedPressingId, setSelectedPressingId] = useState<string | null>(null);
  const [selectedAlbumForPressing, setSelectedAlbumForPressing] = useState<{ id: string; title: string; artistName: string; artistDiscogsId: number | null; albumDiscogsId: number | null } | null>(null);
  const [showPressingWizardModal, setShowPressingWizardModal] = useState(false);
  const [expandedArtists, setExpandedArtists] = useState<Set<string>>(new Set());
  const [expandedAlbums, setExpandedAlbums] = useState<Set<string>>(new Set());
  const [expandedMasters, setExpandedMasters] = useState<Set<string>>(new Set());
  const [masterPressingPages, setMasterPressingPages] = useState<Record<string, number>>({});
  const [initialFilter, setInitialFilter] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const { preferences } = usePreferences();
  const { setControls } = useViewControls();

  const fetchPressings = async (query?: string) => {
    try {
      setLoading(true);
      setError(null);

      // Only include query parameter if it has a value
      const params: {
        query?: string;
        limit: number;
        offset: number;
      } = {
        limit: 500,
        offset: 0,
      };

      if (query && query.trim().length > 0) {
        params.query = query;
      }

      const response = await pressingsApi.getPressingsWithDetails(params);
      setPressings(response.items);
      setCurrentPage(1);
    } catch (err: any) {
      console.error('Failed to load pressings:', err);

      // Handle validation errors (422) which return detail as an array
      let errorMessage = 'Failed to load pressings';
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          // Pydantic validation error format
          errorMessage = detail.map((e: any) => {
            const field = e.loc ? e.loc.join('.') : 'unknown';
            return `${field}: ${e.msg}`;
          }).join(', ');
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const groupPressings = (pressingsToGroup: PressingDetailResponse[]) => {
    const artistMap = new Map<string, ArtistGroup>();

    pressingsToGroup.forEach((pressing) => {
      const artistKey = pressing.artist.id;

      if (!artistMap.has(artistKey)) {
        artistMap.set(artistKey, {
          artistId: pressing.artist.id,
          artistName: pressing.artist.name,
          sortName: pressing.artist.sort_name || pressing.artist.name,
          artistDiscogsId: pressing.artist.discogs_id || null,
          albums: [],
        });
      }

      const artistGroup = artistMap.get(artistKey)!;
      let albumGroup = artistGroup.albums.find((a) => a.albumId === pressing.album.id);

      if (!albumGroup) {
        albumGroup = {
          albumId: pressing.album.id,
          albumTitle: pressing.album.title,
          releaseYear: pressing.album.release_year,
          albumDiscogsId: pressing.album.discogs_id || null,
          masters: [],
        };
        artistGroup.albums.push(albumGroup);
      }

      // Group by master_title (or "Unknown Master" if not set)
      const masterTitle = pressing.master_title || 'Individual Pressings';
      let masterGroup = albumGroup.masters.find((m) => m.masterTitle === masterTitle);

      if (!masterGroup) {
        masterGroup = {
          masterTitle,
          pressings: [],
        };
        albumGroup.masters.push(masterGroup);
      }

      masterGroup.pressings.push(pressing);
    });

    // Convert to array and sort
    const grouped = Array.from(artistMap.values()).sort((a, b) =>
      a.sortName.localeCompare(b.sortName)
    );

    setGroupedData(grouped);

    // Start collapsed
    setExpandedArtists(new Set());
    setExpandedAlbums(new Set());
    setExpandedMasters(new Set());
  };

  useEffect(() => {
    fetchPressings();
  }, []);

  useEffect(() => {
    const storedPerPage = resolveItemsPerPage(preferences, 'pressings');
    setItemsPerPage(storedPerPage);
    setCurrentPage(1);
  }, [preferences]);

  const availableInitials = useMemo(() => {
    const initials = new Set<string>();
    pressings.forEach((pressing) => {
      const initial = getInitialToken(pressing.artist?.sort_name || pressing.artist?.name);
      if (initial) initials.add(initial);
    });
    return initials;
  }, [pressings]);

  const filteredPressings = useMemo(() => {
    if (!initialFilter) return pressings;
    return pressings.filter(
      (pressing) => getInitialToken(pressing.artist?.sort_name || pressing.artist?.name) === initialFilter
    );
  }, [pressings, initialFilter]);

  useEffect(() => {
    groupPressings(filteredPressings);
    setMasterPressingPages({});
  }, [filteredPressings]);

  useEffect(() => {
    if (initialFilter && !availableInitials.has(initialFilter)) {
      setInitialFilter(null);
    }
  }, [availableInitials, initialFilter]);

  const handleSearch = () => {
    fetchPressings(searchQuery);
  };

  const totalPages = Math.ceil(groupedData.length / itemsPerPage);
  const visibleGroups = groupedData.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );
  const visiblePressingIds = useMemo(() => {
    const pressingIds: string[] = [];
    visibleGroups.forEach((artistGroup) => {
      artistGroup.albums.forEach((albumGroup) => {
        albumGroup.masters.forEach((masterGroup) => {
          masterGroup.pressings.forEach((pressing) => {
            pressingIds.push(pressing.id);
          });
        });
      });
    });
    return pressingIds;
  }, [visibleGroups]);
  const pressingOwners = usePressingOwners(visiblePressingIds);

  const handleDelete = async (pressingId: string, albumTitle: string) => {
    if (!confirm(`Are you sure you want to delete this pressing of "${albumTitle}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await pressingsApi.delete(pressingId);
      fetchPressings(searchQuery);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete pressing');
    }
  };

  const toggleArtist = (artistId: string) => {
    const newExpanded = new Set(expandedArtists);
    if (newExpanded.has(artistId)) {
      newExpanded.delete(artistId);
    } else {
      newExpanded.add(artistId);
    }
    setExpandedArtists(newExpanded);
  };

  const toggleAlbum = (albumId: string) => {
    const newExpanded = new Set(expandedAlbums);
    if (newExpanded.has(albumId)) {
      newExpanded.delete(albumId);
    } else {
      newExpanded.add(albumId);
    }
    setExpandedAlbums(newExpanded);
  };

  const toggleMaster = (albumId: string, masterTitle: string) => {
    const masterKey = `${albumId}:${masterTitle}`;
    const newExpanded = new Set(expandedMasters);
    if (newExpanded.has(masterKey)) {
      newExpanded.delete(masterKey);
    } else {
      newExpanded.add(masterKey);
    }
    setExpandedMasters(newExpanded);
  };

  const getMasterPressingPage = (albumId: string, masterTitle: string) => {
    const masterKey = `${albumId}:${masterTitle}`;
    return masterPressingPages[masterKey] || 1;
  };

  const updateMasterPressingPage = (albumId: string, masterTitle: string, nextPage: number) => {
    const masterKey = `${albumId}:${masterTitle}`;
    setMasterPressingPages((prev) => ({
      ...prev,
      [masterKey]: nextPage,
    }));
  };

  const getPressingCover = (pressing: PressingDetailResponse) => {
    return pressing.image_url || pressing.album.image_url || '';
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

  useEffect(() => {
    const filtersContent = (
      <div className="nav-filter-section">
        <label>Artist Initial</label>
        <AlphabetFilterBar
          active={initialFilter}
          available={availableInitials}
          onSelect={setInitialFilter}
          className="alphabet-filter--panel"
        />
      </div>
    );

    setControls({
      viewKey: 'pressings',
      searchPlaceholder: 'Search pressings, albums, and artists...',
      searchValue: searchQuery,
      onSearchChange: setSearchQuery,
      onSearchSubmit: handleSearch,
      filtersContent,
    });

    return () => setControls(null);
  }, [availableInitials, handleSearch, initialFilter, searchQuery, setControls]);

  if (loading && pressings.length === 0) {
    return <Loading message="Loading pressings..." />;
  }

  return (
    <div className="pressings-page">
      <div className="page-header">
        <div>
          <h1>Pressings</h1>
          <p className="result-count">
            {filteredPressings.length} {filteredPressings.length === 1 ? 'pressing' : 'pressings'} found
          </p>
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={() => fetchPressings()} />}

      {!loading && filteredPressings.length === 0 && (
        <div className="no-results">
          <p>No pressings found matching your search criteria.</p>
          <p>Try adjusting your search terms.</p>
        </div>
      )}

      <div className="pressings-grouped">
        {visibleGroups.map((artistGroup) => (
          <div key={artistGroup.artistId} className="artist-group">
            <div
              className="artist-header"
              onClick={() => toggleArtist(artistGroup.artistId)}
            >
              <span className="expand-icon">
                {expandedArtists.has(artistGroup.artistId) ? '▼' : '▶'}
              </span>
              <h2>{artistGroup.artistName}</h2>
              <span className="artist-count">
                ({artistGroup.albums.reduce((sum, album) =>
                  sum + album.masters.reduce((masterSum, master) => masterSum + master.pressings.length, 0), 0)}{' '}
                {artistGroup.albums.reduce((sum, album) =>
                  sum + album.masters.reduce((masterSum, master) => masterSum + master.pressings.length, 0), 0) === 1
                  ? 'pressing'
                  : 'pressings'})
              </span>
            </div>

            {expandedArtists.has(artistGroup.artistId) && (
              <div className="albums-list">
                {artistGroup.albums.map((albumGroup) => (
                  <div key={albumGroup.albumId} className="album-section">
                    <div
                      className="album-header"
                      style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                    >
                      <span
                        className="expand-icon"
                        onClick={() => toggleAlbum(albumGroup.albumId)}
                        style={{ cursor: 'pointer' }}
                      >
                        {expandedAlbums.has(albumGroup.albumId) ? '▼' : '▶'}
                      </span>
                      <h3
                        onClick={() => toggleAlbum(albumGroup.albumId)}
                        style={{ cursor: 'pointer', flex: 1 }}
                      >
                        {albumGroup.albumTitle}
                      </h3>
                      {albumGroup.releaseYear && (
                        <span className="album-year">({albumGroup.releaseYear})</span>
                      )}
                      <span className="pressing-count">
                        {albumGroup.masters.reduce((sum, master) => sum + master.pressings.length, 0)}{' '}
                        {albumGroup.masters.reduce((sum, master) => sum + master.pressings.length, 0) === 1 ? 'pressing' : 'pressings'}
                      </span>
                      <button
                        className="btn-action"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedAlbumForPressing({
                            id: albumGroup.albumId,
                            title: albumGroup.albumTitle,
                            artistName: artistGroup.artistName,
                            artistDiscogsId: artistGroup.artistDiscogsId,
                            albumDiscogsId: albumGroup.albumDiscogsId
                          });
                          setShowPressingWizardModal(true);
                        }}
                        title="Add Pressing to this Album"
                        style={{ background: '#007bff', color: 'white', borderColor: '#007bff' }}
                        aria-label="Add Pressing to this Album"
                      >
                        <Icon path={mdiMusicBoxOutline} />
                      </button>
                    </div>

                    {expandedAlbums.has(albumGroup.albumId) && (
                      <div className="masters-list">
                        {albumGroup.masters.length === 1 ? (
                          (() => {
                            const masterGroup = albumGroup.masters[0];
                            const perMasterPageSize = 10;
                            const masterPage = getMasterPressingPage(albumGroup.albumId, masterGroup.masterTitle);
                            const totalMasterPages = Math.max(
                              1,
                              Math.ceil(masterGroup.pressings.length / perMasterPageSize)
                            );
                            const startIndex = (masterPage - 1) * perMasterPageSize;
                            const visiblePressings = masterGroup.pressings.slice(
                              startIndex,
                              startIndex + perMasterPageSize
                            );

                            return (
                              <>
                                <table className="data-table pressing-table">
                        <thead>
                          <tr>
                            <th>Cover</th>
                            <th>Format</th>
                            <th>Speed</th>
                            <th>Size</th>
                            <th>Country</th>
                            <th>Year</th>
                            <th>Color</th>
                            <th>Type</th>
                            <th>Sleeve Type</th>
                            <th>Owned</th>
                            <th>Actions</th>
                          </tr>
                        </thead>
                          <tbody>
                            {visiblePressings.map((pressing) => {
                              const coverUrl = getPressingCover(pressing);
                              return (
                                <tr key={pressing.id}>
                                  <td className="pressing-cover-cell">
                                    <div className="pressing-cover">
                                      {coverUrl ? (
                                        <img src={coverUrl} alt="Pressing cover" />
                                      ) : (
                                        <span>?</span>
                                      )}
                                    </div>
                                  </td>
                                  <td>
                                    {pressing.format}
                                    {pressing.is_master && (
                                      <span className="pressing-master-badge">Master</span>
                                    )}
                                  </td>
                                  <td>{pressing.speed_rpm} RPM</td>
                                  <td>{pressing.size_inches}</td>
                                  <td>{getCountryName(pressing.country)}</td>
                                  <td>{pressing.release_year || '-'}</td>
                                  <td>{pressing.vinyl_color || '-'}</td>
                                  <td>{pressing.edition_type || '-'}</td>
                                  <td>{pressing.sleeve_type || '-'}</td>
                                  <td className="owned-cell">
                                    <OwnersGrid
                                      owners={pressingOwners[pressing.id] || []}
                                      currentUserId={currentUserId}
                                      showEmpty
                                      className="owners-grid-large"
                                    />
                                  </td>
                                  <td className="actions-cell">
                                    <button
                                      className="btn-action"
                                      onClick={() => {
                                        setSelectedPressingId(pressing.id);
                                        setShowEditModal(true);
                                      }}
                                      title="Edit"
                                      aria-label="Edit"
                                    >
                                      <Icon path={mdiPencilOutline} />
                                    </button>
                                    <button
                                      className="btn-action btn-success"
                                      onClick={() => {
                                        setSelectedPressingId(pressing.id);
                                        setShowAddToCollectionModal(true);
                                      }}
                                      title="Add to Collection"
                                      aria-label="Add to Collection"
                                    >
                                      <Icon path={mdiPlus} />
                                    </button>
                                    <button
                                      className="btn-action btn-danger"
                                      onClick={() => handleDelete(pressing.id, albumGroup.albumTitle)}
                                      title="Delete"
                                      aria-label="Delete"
                                    >
                                      <Icon path={mdiTrashCanOutline} />
                                    </button>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                                </table>
                                {totalMasterPages > 1 && (
                                  <div className="pagination" style={{ marginTop: '0.75rem' }}>
                                    <div className="pagination-controls">
                                      <button
                                        onClick={() => updateMasterPressingPage(albumGroup.albumId, masterGroup.masterTitle, Math.max(1, masterPage - 1))}
                                        disabled={masterPage === 1}
                                        className="pagination-button"
                                      >
                                        Previous
                                      </button>
                                      <div className="pagination-info">
                                        Page {masterPage} of {totalMasterPages}
                                      </div>
                                      <button
                                        onClick={() => updateMasterPressingPage(albumGroup.albumId, masterGroup.masterTitle, Math.min(totalMasterPages, masterPage + 1))}
                                        disabled={masterPage === totalMasterPages}
                                        className="pagination-button"
                                      >
                                        Next
                                      </button>
                                    </div>
                                  </div>
                                )}
                              </>
                            );
                          })()
                        ) : (
                          albumGroup.masters.map((masterGroup) => {
                            const perMasterPageSize = 10;
                            const masterPage = getMasterPressingPage(albumGroup.albumId, masterGroup.masterTitle);
                            const totalMasterPages = Math.max(
                              1,
                              Math.ceil(masterGroup.pressings.length / perMasterPageSize)
                            );
                            const startIndex = (masterPage - 1) * perMasterPageSize;
                            const visiblePressings = masterGroup.pressings.slice(
                              startIndex,
                              startIndex + perMasterPageSize
                            );
                            const masterKey = `${albumGroup.albumId}:${masterGroup.masterTitle}`;

                            return (
                              <div key={masterKey} className="master-section">
                                <div
                                  className="master-header"
                                  onClick={() => toggleMaster(albumGroup.albumId, masterGroup.masterTitle)}
                                >
                                  <span className="expand-icon">
                                    {expandedMasters.has(masterKey) ? '▼' : '▶'}
                                  </span>
                                  <h4 className="master-title"><strong>MASTER:</strong> {masterGroup.masterTitle}</h4>
                                  <span className="master-count">
                                    ({masterGroup.pressings.length}{' '}
                                    {masterGroup.pressings.length === 1 ? 'pressing' : 'pressings'})
                                  </span>
                                </div>

                                {expandedMasters.has(masterKey) && (
                                  <>
                                <table className="data-table pressing-table">
                        <thead>
                          <tr>
                            <th>Cover</th>
                            <th>Format</th>
                            <th>Speed</th>
                            <th>Size</th>
                            <th>Country</th>
                            <th>Year</th>
                            <th>Color</th>
                            <th>Type</th>
                            <th>Sleeve Type</th>
                            <th>Owned</th>
                            <th>Actions</th>
                          </tr>
                        </thead>
                          <tbody>
                            {visiblePressings.map((pressing) => {
                              const coverUrl = getPressingCover(pressing);
                              return (
                                <tr key={pressing.id}>
                                  <td className="pressing-cover-cell">
                                    <div className="pressing-cover">
                                      {coverUrl ? (
                                        <img src={coverUrl} alt="Pressing cover" />
                                      ) : (
                                        <span>?</span>
                                      )}
                                    </div>
                                  </td>
                                  <td>
                                    {pressing.format}
                                    {pressing.is_master && (
                                      <span className="pressing-master-badge">Master</span>
                                    )}
                                  </td>
                                  <td>{pressing.speed_rpm} RPM</td>
                                  <td>{pressing.size_inches}</td>
                                  <td>{getCountryName(pressing.country)}</td>
                                  <td>{pressing.release_year || '-'}</td>
                                  <td>{pressing.vinyl_color || '-'}</td>
                                  <td>{pressing.edition_type || '-'}</td>
                                  <td>{pressing.sleeve_type || '-'}</td>
                                  <td className="owned-cell">
                                    <OwnersGrid
                                      owners={pressingOwners[pressing.id] || []}
                                      currentUserId={currentUserId}
                                      showEmpty
                                      className="owners-grid-large"
                                    />
                                  </td>
                                  <td className="actions-cell">
                                    <button
                                      className="btn-action"
                                      onClick={() => {
                                        setSelectedPressingId(pressing.id);
                                        setShowEditModal(true);
                                      }}
                                      title="Edit"
                                      aria-label="Edit"
                                    >
                                      <Icon path={mdiPencilOutline} />
                                    </button>
                                    <button
                                      className="btn-action btn-success"
                                      onClick={() => {
                                        setSelectedPressingId(pressing.id);
                                        setShowAddToCollectionModal(true);
                                      }}
                                      title="Add to Collection"
                                      aria-label="Add to Collection"
                                    >
                                      <Icon path={mdiPlus} />
                                    </button>
                                    <button
                                      className="btn-action btn-danger"
                                      onClick={() => handleDelete(pressing.id, albumGroup.albumTitle)}
                                      title="Delete"
                                      aria-label="Delete"
                                    >
                                      <Icon path={mdiTrashCanOutline} />
                                    </button>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                                </table>
                                {totalMasterPages > 1 && (
                                  <div className="pagination" style={{ marginTop: '0.75rem' }}>
                                    <div className="pagination-controls">
                                      <button
                                        onClick={() => updateMasterPressingPage(albumGroup.albumId, masterGroup.masterTitle, Math.max(1, masterPage - 1))}
                                        disabled={masterPage === 1}
                                        className="pagination-button"
                                      >
                                        Previous
                                      </button>
                                      <div className="pagination-info">
                                        Page {masterPage} of {totalMasterPages}
                                      </div>
                                      <button
                                        onClick={() => updateMasterPressingPage(albumGroup.albumId, masterGroup.masterTitle, Math.min(totalMasterPages, masterPage + 1))}
                                        disabled={masterPage === totalMasterPages}
                                        className="pagination-button"
                                      >
                                        Next
                                      </button>
                                    </div>
                                  </div>
                                )}
                                  </>
                                )}
                              </div>
                            );
                          })
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {loading && pressings.length > 0 && <Loading message="Loading more..." />}

      {totalPages > 1 && !loading && (
        <div className="pagination">
          <div className="pagination-controls">
            <button
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="pagination-button"
            >
              Previous
            </button>
            <div className="pagination-info">
              Page {currentPage} of {totalPages}
            </div>
            <button
              onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="pagination-button"
            >
              Next
            </button>
          </div>
          <div className="items-per-page">
            <span>Per page</span>
            <select
              value={itemsPerPage}
              onChange={(e) => {
                setItemsPerPage(Number(e.target.value));
                setCurrentPage(1);
              }}
            >
              {[10, 25, 50, 100].map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {selectedAlbumForPressing && (
        <Modal
          isOpen={showCreateModal}
          onClose={() => {
            setShowCreateModal(false);
            setSelectedAlbumForPressing(null);
          }}
          title="Add Pressing"
          size="large"
        >
          <PressingForm
            albumId={selectedAlbumForPressing.id}
            albumTitle={selectedAlbumForPressing.title}
            showAddToCollection
            onSuccess={() => {
              setShowCreateModal(false);
              setSelectedAlbumForPressing(null);
              fetchPressings(searchQuery);
            }}
            onCancel={() => {
              setShowCreateModal(false);
              setSelectedAlbumForPressing(null);
            }}
          />
        </Modal>
      )}

      {selectedPressingId && (
        <>
          <Modal
            isOpen={showEditModal}
            onClose={() => {
              setShowEditModal(false);
              setSelectedPressingId(null);
            }}
            title="Edit Pressing"
            size="large"
          >
            <PressingForm
              pressingId={selectedPressingId}
              onSuccess={() => {
                setShowEditModal(false);
                setSelectedPressingId(null);
                fetchPressings(searchQuery);
              }}
              onCancel={() => {
                setShowEditModal(false);
                setSelectedPressingId(null);
              }}
            />
          </Modal>

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
              }}
              onCancel={() => {
                setShowAddToCollectionModal(false);
                setSelectedPressingId(null);
              }}
            />
          </Modal>
        </>
      )}

      {selectedAlbumForPressing && (
        <PressingWizardModal
          isOpen={showPressingWizardModal}
          onClose={() => {
            setShowPressingWizardModal(false);
            setSelectedAlbumForPressing(null);
          }}
          onSuccess={() => {
            setShowPressingWizardModal(false);
            setSelectedAlbumForPressing(null);
            fetchPressings(searchQuery);
          }}
          albumId={selectedAlbumForPressing.id}
          albumTitle={selectedAlbumForPressing.title}
          artistName={selectedAlbumForPressing.artistName}
          discogsId={selectedAlbumForPressing.albumDiscogsId}
          artistDiscogsId={selectedAlbumForPressing.artistDiscogsId}
        />
      )}
    </div>
  );
}
