/**
 * Artists page - browse and search artists with advanced filters.
 */

import { useState, useEffect, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { artistsApi, albumsApi } from '@/api/services';
import { AlbumDetailResponse, ArtistResponse } from '@/types/api';
import { Loading, ErrorAlert, Modal, Icon } from '@/components/UI';
import { ArtistFiltersPanel, ArtistFilterValues } from '@/components/Search/ArtistFiltersPanel';
import { ArtistForm } from '@/components/Forms';
import { AlbumDetailsModal, AlbumWizardModal, PressingWizardModal } from '@/components/Modals';
import { AlphabetFilterBar } from '@/components/AlphabetFilterBar';
import { getInitialToken } from '@/utils/alpha';
import { formatDate, formatDateTime } from '@/utils/format';
import { usePreferences } from '@/hooks/usePreferences';
import { resolveItemsPerPage } from '@/utils/preferences';
import { useViewControls } from '@/components/Layout/ViewControlsContext';
import {
  mdiEyeOutline,
  mdiPencilOutline,
  mdiTrashCanOutline,
  mdiAccountMusicOutline,
  mdiAlbum,
  mdiMusicBoxOutline,
} from '@mdi/js';
import './Artists.css';
import '../styles/Table.css';

export function Artists() {
  const [artists, setArtists] = useState<ArtistResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [filters, setFilters] = useState<ArtistFilterValues>({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [showAlbumModal, setShowAlbumModal] = useState(false);
  const [selectedArtistId, setSelectedArtistId] = useState<string | null>(null);
  const [selectedArtist, setSelectedArtist] = useState<ArtistResponse | null>(null);
  const [selectedArtistForAlbum, setSelectedArtistForAlbum] = useState<{ id: string; name: string; discogsId: number | null } | null>(null);
  const [artistAlbums, setArtistAlbums] = useState<AlbumDetailResponse[]>([]);
  const [artistAlbumsLoading, setArtistAlbumsLoading] = useState(false);
  const [artistAlbumsError, setArtistAlbumsError] = useState<string | null>(null);
  const [showAlbumDetailsModal, setShowAlbumDetailsModal] = useState(false);
  const [selectedAlbumForDetails, setSelectedAlbumForDetails] = useState<string | null>(null);
  const [showPressingWizardModal, setShowPressingWizardModal] = useState(false);
  const [selectedAlbumForPressing, setSelectedAlbumForPressing] = useState<{ id: string; title: string; artistName: string; artistDiscogsId: number | null; albumDiscogsId: number | null } | null>(null);
  const [initialFilter, setInitialFilter] = useState<string | null>(null);
  const { preferences } = usePreferences();
  const { setControls } = useViewControls();
  const location = useLocation();
  const navigate = useNavigate();

  const fetchArtists = async (options?: { resetPage?: boolean }) => {
    try {
      setLoading(true);
      setError(null);

      const response = await artistsApi.search({
        query: filters.query,
        artist_type: filters.artistType,
        country: filters.country,
        limit: 500,
        offset: 0,
      });

      setArtists(response.items);
      if (options?.resetPage ?? true) {
        setCurrentPage(1);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load artists');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArtists({ resetPage: true });
  }, []);

  useEffect(() => {
    const storedPerPage = resolveItemsPerPage(preferences, 'artists');
    setItemsPerPage(storedPerPage);
    setCurrentPage(1);
  }, [preferences]);

  useEffect(() => {
    if (showViewModal && selectedArtist) {
      fetchArtistAlbums(selectedArtist.id);
    }
  }, [showViewModal, selectedArtist?.id]);

  const fetchArtistAlbums = async (artistId: string) => {
    try {
      setArtistAlbumsLoading(true);
      setArtistAlbumsError(null);
      const response = await albumsApi.getAlbumsWithDetails({ artist_id: artistId, limit: 200, offset: 0 });
      const sorted = [...response.items].sort((a, b) => {
        const yearA = a.release_year || 0;
        const yearB = b.release_year || 0;
        if (yearA !== yearB) return yearA - yearB;
        return a.title.localeCompare(b.title);
      });
      setArtistAlbums(sorted);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        const message = detail.map((e: any) => e.msg || String(e)).join(', ');
        setArtistAlbumsError(message || 'Failed to load albums');
      } else {
        setArtistAlbumsError(detail || err.message || 'Failed to load albums');
      }
    } finally {
      setArtistAlbumsLoading(false);
    }
  };

  const handleSearch = () => {
    fetchArtists({ resetPage: true });
  };

  const handleFilterChange = (newFilters: ArtistFilterValues) => {
    setFilters(newFilters);
  };

  const handleResetFilters = () => {
    setFilters({});
    fetchArtists({ resetPage: true });
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDelete = async (artistId: string, artistName: string) => {
    if (!confirm(`Are you sure you want to delete "${artistName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await artistsApi.delete(artistId);
      fetchArtists({ resetPage: false });
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete artist');
    }
  };

  // Common country code to name mappings
  const getCountryName = (code: string | undefined): string => {
    if (!code) return '—';
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

  const formatActiveDates = (beginDate: string | undefined, endDate: string | undefined): string => {
    const formatYear = (dateStr: string | undefined): string => {
      if (!dateStr) return '';
      // Extract year from various date formats (YYYY-MM-DD, YYYY-MM, YYYY)
      const match = dateStr.match(/^(\d{4})/);
      return match ? match[1] : dateStr;
    };

    const start = formatYear(beginDate) || '?';
    const end = endDate ? formatYear(endDate) : 'Present';

    return `${start} / ${end}`;
  };

  const getArtistType = (artist: ArtistResponse): string => {
    return artist.artist_type || artist.type || '-';
  };

  const getArtistInitial = (artist: ArtistResponse): string => {
    const name = artist.sort_name || artist.name || '';
    const initial = name.trim().charAt(0);
    return initial ? initial.toUpperCase() : '?';
  };

  const formatValue = (value?: string | number | null) => {
    if (value === null || value === undefined || value === '') {
      return '-';
    }
    return String(value);
  };

  const getAlbumGenres = (album: AlbumDetailResponse) => {
    return album.genres.length ? album.genres.join(', ') : '-';
  };

  const getAlbumStyles = (album: AlbumDetailResponse) => {
    return album.styles.length ? album.styles.join(', ') : '-';
  };

  const openViewModal = (artist: ArtistResponse) => {
    setSelectedArtist(artist);
    setShowViewModal(true);
  };

  useEffect(() => {
    const navState = location.state as { selectedArtistId?: string } | null;
    if (!navState?.selectedArtistId) {
      return;
    }

    const targetId = navState.selectedArtistId;
    const existing = artists.find((artist) => artist.id === targetId);
    if (existing) {
      openViewModal(existing);
      navigate('/artists', { replace: true, state: {} });
      return;
    }

    const loadArtist = async () => {
      try {
        const artist = await artistsApi.getById(targetId);
        openViewModal(artist);
      } catch (err) {
        console.error('Failed to load artist for navigation:', err);
      } finally {
        navigate('/artists', { replace: true, state: {} });
      }
    };

    loadArtist();
  }, [artists, location.state, navigate]);

  const availableInitials = useMemo(() => {
    const initials = new Set<string>();
    artists.forEach((artist) => {
      const initial = getInitialToken(artist.sort_name || artist.name);
      if (initial) initials.add(initial);
    });
    return initials;
  }, [artists]);

  const filteredArtists = useMemo(() => {
    const filtered = !initialFilter
      ? artists
      : artists.filter((artist) => getInitialToken(artist.sort_name || artist.name) === initialFilter);

    // Sort by sort_name (or name if sort_name is not present)
    return [...filtered].sort((a, b) => {
      const nameA = (a.sort_name || a.name || '').toLowerCase();
      const nameB = (b.sort_name || b.name || '').toLowerCase();
      return nameA.localeCompare(nameB);
    });
  }, [artists, initialFilter]);

  useEffect(() => {
    if (initialFilter && !availableInitials.has(initialFilter)) {
      setInitialFilter(null);
    }
  }, [availableInitials, initialFilter]);

  const totalPages = Math.ceil(filteredArtists.length / itemsPerPage);
  const visibleArtists = filteredArtists.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  useEffect(() => {
    const filtersContent = (
      <>
        <ArtistFiltersPanel
          filters={filters}
          onFilterChange={handleFilterChange}
          onApply={handleSearch}
          onReset={handleResetFilters}
        />
        <div className="nav-filter-section">
          <label>Artist Initial</label>
          <AlphabetFilterBar
            active={initialFilter}
            available={availableInitials}
            onSelect={setInitialFilter}
            className="alphabet-filter--panel"
          />
        </div>
      </>
    );

    setControls({
      viewKey: 'artists',
      searchPlaceholder: 'Search artists by name...',
      searchValue: filters.query || '',
      onSearchChange: (value) => setFilters((prev) => ({ ...prev, query: value })),
      onSearchSubmit: handleSearch,
      filtersContent,
    });

    return () => setControls(null);
  }, [
    availableInitials,
    filters,
    handleSearch,
    handleResetFilters,
    initialFilter,
    setControls,
  ]);

  if (loading && artists.length === 0) {
    return <Loading message="Loading artists..." />;
  }

  return (
    <div className="artists-page">
      <div className="page-header">
        <div>
          <h1>Artists</h1>
          <p className="result-count">
            {filteredArtists.length} {filteredArtists.length === 1 ? 'artist' : 'artists'} found
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={() => setShowCreateModal(true)}
        >
          <Icon path={mdiAccountMusicOutline} className="btn-icon" />
          Add Artist
        </button>
      </div>

      {error && <ErrorAlert message={error} onRetry={fetchArtists} />}

      {!loading && filteredArtists.length === 0 && (
        <div className="no-results">
          <p>No artists found matching your search criteria.</p>
          <p>Try adjusting your filters or search terms.</p>
        </div>
      )}

      <div className="artists-grid">
        {visibleArtists.map((artist) => (
          <div key={artist.id} className="artist-card">
            <div className="artist-card-header">
              <div className="artist-card-image">
                {artist.image_url ? (
                  <img src={artist.image_url} alt={`${artist.name} artwork`} />
                ) : (
                  <span className="artist-card-placeholder">{getArtistInitial(artist)}</span>
                )}
              </div>
              <div>
                <h3>{artist.name}</h3>
                <div className="artist-meta">
                  <span className="artist-type">{getArtistType(artist)}</span>
                  <span className="artist-country">{getCountryName(artist.country)}</span>
                </div>
              </div>
            </div>
            <div className="artist-card-stats">
              <span>{artist.album_count ?? 0} albums</span>
              <span>{formatActiveDates(artist.begin_date, artist.end_date)}</span>
            </div>
            {artist.bio && <p className="artist-bio">{artist.bio}</p>}
            <div className="artist-card-actions">
              <button
                className="btn-action"
                onClick={() => openViewModal(artist)}
                title="View"
                aria-label="View"
              >
                <Icon path={mdiEyeOutline} />
              </button>
              <button
                className="btn-action"
                onClick={() => {
                  setSelectedArtistForAlbum({ id: artist.id, name: artist.name, discogsId: artist.discogs_id || null });
                  setShowAlbumModal(true);
                }}
                title="Create Album"
                aria-label="Create Album"
              >
                <Icon path={mdiAlbum} />
              </button>
              <button
                className="btn-action"
                onClick={() => {
                  setSelectedArtistId(artist.id);
                  setShowEditModal(true);
                }}
                title="Edit"
                aria-label="Edit"
              >
                <Icon path={mdiPencilOutline} />
              </button>
              <button
                className="btn-action btn-danger"
                onClick={() => handleDelete(artist.id, artist.name)}
                title="Delete"
                aria-label="Delete"
              >
                <Icon path={mdiTrashCanOutline} />
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="table-container artists-table">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Country</th>
              <th>Albums</th>
              <th>Active Dates</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {visibleArtists.map((artist) => (
              <tr key={artist.id}>
                <td className="name-cell">
                  <div className="artist-row-name">
                    <div className="artist-row-thumb">
                      {artist.image_url ? (
                        <img src={artist.image_url} alt={`${artist.name} artwork`} />
                      ) : (
                        <span className="artist-row-placeholder">{getArtistInitial(artist)}</span>
                      )}
                    </div>
                    <span>{artist.name}</span>
                  </div>
                </td>
                <td>{getArtistType(artist)}</td>
                <td>{getCountryName(artist.country)}</td>
                <td>{artist.album_count ?? 0}</td>
                <td>{formatActiveDates(artist.begin_date, artist.end_date)}</td>
                <td className="actions-cell">
                  <button
                    className="btn-action"
                    onClick={() => openViewModal(artist)}
                    title="View"
                    aria-label="View"
                  >
                    <Icon path={mdiEyeOutline} />
                  </button>
                  <button
                    className="btn-action"
                    onClick={() => {
                      setSelectedArtistForAlbum({ id: artist.id, name: artist.name, discogsId: artist.discogs_id || null });
                      setShowAlbumModal(true);
                    }}
                    title="Create Album"
                    aria-label="Create Album"
                  >
                    <Icon path={mdiAlbum} />
                  </button>
                  <button
                    className="btn-action"
                    onClick={() => {
                      setSelectedArtistId(artist.id);
                      setShowEditModal(true);
                    }}
                    title="Edit"
                    aria-label="Edit"
                  >
                    <Icon path={mdiPencilOutline} />
                  </button>
                  <button
                    className="btn-action btn-danger"
                    onClick={() => handleDelete(artist.id, artist.name)}
                    title="Delete"
                    aria-label="Delete"
                  >
                    <Icon path={mdiTrashCanOutline} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {loading && <Loading message="Loading..." />}

      {totalPages > 1 && !loading && (
        <div className="pagination">
          <div className="pagination-controls">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="pagination-button"
            >
              Previous
            </button>
            <div className="pagination-info">
              Page {currentPage} of {totalPages}
            </div>
            <button
              onClick={() => handlePageChange(currentPage + 1)}
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

      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Add New Artist"
        size="large"
      >
        <ArtistForm
          onSuccess={() => {
            setShowCreateModal(false);
            fetchArtists({ resetPage: false });
          }}
          onCancel={() => setShowCreateModal(false)}
        />
      </Modal>

      {selectedArtistId && (
        <Modal
          isOpen={showEditModal}
          onClose={() => {
            setShowEditModal(false);
            setSelectedArtistId(null);
          }}
          title="Edit Artist"
          size="large"
        >
          <ArtistForm
            artistId={selectedArtistId}
            onSuccess={() => {
              setShowEditModal(false);
              setSelectedArtistId(null);
              fetchArtists({ resetPage: false });
            }}
            onCancel={() => {
              setShowEditModal(false);
              setSelectedArtistId(null);
            }}
          />
        </Modal>
      )}

      {selectedArtist && (
        <Modal
          isOpen={showViewModal}
          onClose={() => {
            setShowViewModal(false);
            setSelectedArtist(null);
            setArtistAlbums([]);
            setArtistAlbumsError(null);
          }}
          title={selectedArtist.name}
          size="large"
        >
          <div className="artist-view">
            <div className="artist-view-media">
              <div className="artist-view-image">
                {selectedArtist.image_url ? (
                  <img src={selectedArtist.image_url} alt={`${selectedArtist.name} artwork`} />
                ) : (
                  <span className="artist-view-placeholder">{getArtistInitial(selectedArtist)}</span>
                )}
              </div>
            </div>
            <div className="artist-view-details">
              <div className="artist-view-row">
                <span className="artist-view-label">Name</span>
                <span>{formatValue(selectedArtist.name)}</span>
              </div>
              <div className="artist-view-row">
                <span className="artist-view-label">Sort Name</span>
                <span>{formatValue(selectedArtist.sort_name)}</span>
              </div>
              <div className="artist-view-row">
                <span className="artist-view-label">Type</span>
                <span>{getArtistType(selectedArtist)}</span>
              </div>
              <div className="artist-view-row">
                <span className="artist-view-label">Country</span>
                <span>{getCountryName(selectedArtist.country)}</span>
              </div>
              <div className="artist-view-row">
                <span className="artist-view-label">Begin Date</span>
                <span>{formatDate(selectedArtist.begin_date)}</span>
              </div>
              <div className="artist-view-row">
                <span className="artist-view-label">End Date</span>
                <span>{formatDate(selectedArtist.end_date)}</span>
              </div>
              <div className="artist-view-row">
                <span className="artist-view-label">Albums</span>
                <span>{selectedArtist.album_count ?? 0}</span>
              </div>
              <div className="artist-view-row">
                <span className="artist-view-label">Disambiguation</span>
                <span>{formatValue(selectedArtist.disambiguation)}</span>
              </div>
              <div className="artist-view-row">
                <span className="artist-view-label">Data Source</span>
                <span>{formatValue(selectedArtist.data_source)}</span>
              </div>
              <div className="artist-view-row">
                <span className="artist-view-label">Created</span>
                <span>{formatDateTime(selectedArtist.created_at)}</span>
              </div>
              <div className="artist-view-row">
                <span className="artist-view-label">Updated</span>
                <span>{formatDateTime(selectedArtist.updated_at)}</span>
              </div>
            </div>
            <div className="artist-view-bio-block">
              <div className="artist-view-bio-label">Bio</div>
              <div className="artist-view-bio-text">{formatValue(selectedArtist.bio)}</div>
            </div>
          </div>
          <div className="artist-view-actions">
            <button
              className="btn-primary"
              onClick={() => {
                setShowViewModal(false);
                setSelectedArtist(null);
                setSelectedArtistId(selectedArtist.id);
                setShowEditModal(true);
              }}
            >
              <Icon path={mdiPencilOutline} className="btn-icon" />
              Edit Artist
            </button>
            <button
              className="btn-secondary"
              onClick={() => {
                setSelectedArtistForAlbum({ id: selectedArtist.id, name: selectedArtist.name, discogsId: selectedArtist.discogs_id || null });
                setShowViewModal(false);
                setSelectedArtist(null);
                setShowAlbumModal(true);
              }}
            >
              <Icon path={mdiAlbum} className="btn-icon" />
              Create Album
            </button>
          </div>
          <div className="artist-view-albums">
            <div className="artist-view-albums-header">
              <h4>Albums</h4>
              <span className="artist-view-albums-count">
                {artistAlbums.length}
              </span>
            </div>
            {artistAlbumsLoading && (
              <div className="artist-view-albums-status">Loading albums...</div>
            )}
            {artistAlbumsError && (
              <ErrorAlert message={artistAlbumsError} onRetry={() => fetchArtistAlbums(selectedArtist.id)} />
            )}
            {!artistAlbumsLoading && !artistAlbumsError && artistAlbums.length === 0 && (
              <div className="artist-view-albums-status">No albums found for this artist.</div>
            )}
            {!artistAlbumsLoading && !artistAlbumsError && artistAlbums.length > 0 && (
              <div className="artist-view-albums-table">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Album</th>
                      <th>Year</th>
                      <th>Type</th>
                      <th>Genre</th>
                      <th>Styles</th>
                      <th>Pressings</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {artistAlbums.map((album) => (
                      <tr key={album.id}>
                        <td className="name-cell">
                          {album.in_user_collection && <span style={{ color: '#ffd700', marginRight: '0.5rem' }}>★</span>}
                          {album.title}
                        </td>
                        <td>{album.release_year || '-'}</td>
                        <td>{album.release_type || '-'}</td>
                        <td>{getAlbumGenres(album)}</td>
                        <td>{getAlbumStyles(album)}</td>
                        <td>{album.pressing_count || 0}</td>
                        <td className="actions-cell">
                          <button
                            className="btn-action"
                            onClick={() => {
                              setSelectedAlbumForPressing({
                                id: album.id,
                                title: album.title,
                                artistName: selectedArtist!.name,
                                artistDiscogsId: selectedArtist!.discogs_id || null,
                                albumDiscogsId: album.discogs_id || null
                              });
                              setShowPressingWizardModal(true);
                            }}
                            title="Add Pressing"
                            aria-label="Add Pressing"
                          >
                            <Icon path={mdiMusicBoxOutline} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </Modal>
      )}

      {selectedArtistForAlbum && (
        <AlbumWizardModal
          initialArtistId={selectedArtistForAlbum.id}
          initialArtistName={selectedArtistForAlbum.name}
          initialArtistDiscogsId={selectedArtistForAlbum.discogsId}
          isOpen={showAlbumModal}
          onClose={() => {
            setShowAlbumModal(false);
            setSelectedArtistForAlbum(null);
          }}
          onSuccess={() => {
            setShowAlbumModal(false);
            setSelectedArtistForAlbum(null);
            fetchArtists({ resetPage: false });
          }}
        />
      )}

      {selectedAlbumForDetails && (
        <AlbumDetailsModal
          albumId={selectedAlbumForDetails}
          isOpen={showAlbumDetailsModal}
          onClose={() => {
            setShowAlbumDetailsModal(false);
            setSelectedAlbumForDetails(null);
          }}
        />
      )}

      {selectedAlbumForPressing && (
        <PressingWizardModal
          albumId={selectedAlbumForPressing.id}
          albumTitle={selectedAlbumForPressing.title}
          artistName={selectedAlbumForPressing.artistName}
          discogsId={selectedAlbumForPressing.albumDiscogsId}
          isOpen={showPressingWizardModal}
          onClose={() => {
            setShowPressingWizardModal(false);
            setSelectedAlbumForPressing(null);
          }}
          onSuccess={() => {
            setShowPressingWizardModal(false);
            setSelectedAlbumForPressing(null);
            if (selectedArtist) {
              fetchArtistAlbums(selectedArtist.id);
            }
          }}
        />
      )}
    </div>
  );
}
