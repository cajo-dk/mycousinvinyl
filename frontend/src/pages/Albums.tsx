/**
 * Albums page - browse albums grouped by artist with pressing counts.
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useMsal } from '@azure/msal-react';
import { albumsApi } from '@/api/services';
import { AlbumDetailResponse } from '@/types/api';
import { Loading, ErrorAlert, Modal, Icon } from '@/components/UI';
import { AlbumWithPressingForm, AlbumForm } from '@/components/Forms';
import { PressingWizardModal, AlbumDetailsModal, AlbumWizardModal } from '@/components/Modals';
import { OwnersGrid } from '@/components/CollectionSharing';
import { mdiEyeOutline, mdiPencilOutline, mdiTrashCanOutline, mdiMusicBoxOutline, mdiAlbum } from '@mdi/js';
import { AlphabetFilterBar } from '@/components/AlphabetFilterBar';
import { AlbumFiltersPanel, AlbumFilterValues } from '@/components/Search/AlbumFiltersPanel';
import { getInitialToken } from '@/utils/alpha';
import { usePreferences } from '@/hooks/usePreferences';
import { resolveItemsPerPage } from '@/utils/preferences';
import { useViewControls } from '@/components/Layout/ViewControlsContext';
import { useAlbumOwners } from '@/hooks/useAlbumOwners';
import './Albums.css';
import '../styles/Table.css';

// Group albums by artist
interface ArtistGroup {
  artistId: string;
  artistName: string;
  sortName: string;
  albums: AlbumDetailResponse[];
}

export function Albums() {
  const { accounts } = useMsal();
  const currentUserId = (accounts[0]?.idTokenClaims?.oid as string) || accounts[0]?.localAccountId || '';
  const [albums, setAlbums] = useState<AlbumDetailResponse[]>([]);
  const [groupedData, setGroupedData] = useState<ArtistGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<AlbumFilterValues>({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showWizardModal, setShowWizardModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedAlbumId, setSelectedAlbumId] = useState<string | null>(null);
  const [showAddPressingModal, setShowAddPressingModal] = useState(false);
  const [selectedAlbumForPressing, setSelectedAlbumForPressing] = useState<{ id: string; title: string; artistName: string; discogsId: number | null } | null>(null);
  const [showAlbumDetailsModal, setShowAlbumDetailsModal] = useState(false);
  const [selectedAlbumForDetails, setSelectedAlbumForDetails] = useState<string | null>(null);
  const [expandedArtists, setExpandedArtists] = useState<Set<string>>(new Set());
  const [initialFilter, setInitialFilter] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const { preferences } = usePreferences();
  const { setControls } = useViewControls();

  const fetchAlbums = useCallback(async (query?: string) => {
    try {
      setLoading(true);
      setError(null);
      const params: {
        query?: string;
        release_type?: string;
        year_min?: number;
        year_max?: number;
        genre_ids?: string[];
        style_ids?: string[];
        limit: number;
        offset: number;
      } = {
        release_type: filters.releaseType,
        year_min: filters.yearMin,
        year_max: filters.yearMax,
        genre_ids: filters.genreIds,
        style_ids: filters.styleIds,
        limit: 500,
        offset: 0,
      };

      if (query && query.trim().length > 0) {
        params.query = query;
      }

      const response = await albumsApi.getAlbumsWithDetails(params);
      setAlbums(response.items);
      setCurrentPage(1);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        const message = detail.map((e: any) => e.msg || String(e)).join(', ');
        setError(message || 'Failed to load albums');
      } else {
        setError(detail || err.message || 'Failed to load albums');
      }
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const groupAlbums = (albumsToGroup: AlbumDetailResponse[]) => {
    const artistMap = new Map<string, ArtistGroup>();

    albumsToGroup.forEach((album) => {
      const artistKey = album.artist.id;

      if (!artistMap.has(artistKey)) {
        artistMap.set(artistKey, {
          artistId: album.artist.id,
          artistName: album.artist.name,
          sortName: album.artist.sort_name || album.artist.name,
          albums: [],
        });
      }

      const artistGroup = artistMap.get(artistKey)!;
      artistGroup.albums.push(album);
    });

    // Convert to array and sort
    const grouped = Array.from(artistMap.values()).sort((a, b) =>
      a.sortName.localeCompare(b.sortName)
    );

    setGroupedData(grouped);

    // Start collapsed
    setExpandedArtists(new Set());
  };

  useEffect(() => {
    fetchAlbums();
  }, [fetchAlbums]);

  useEffect(() => {
    const storedPerPage = resolveItemsPerPage(preferences, 'albums');
    setItemsPerPage(storedPerPage);
    setCurrentPage(1);
  }, [preferences]);

  const availableInitials = useMemo(() => {
    const initials = new Set<string>();
    albums.forEach((album) => {
      const initial = getInitialToken(album.title);
      if (initial) initials.add(initial);
    });
    return initials;
  }, [albums]);

  const filteredAlbums = useMemo(() => {
    if (!initialFilter) return albums;
    return albums.filter((album) => getInitialToken(album.title) === initialFilter);
  }, [albums, initialFilter]);

  useEffect(() => {
    groupAlbums(filteredAlbums);
  }, [filteredAlbums]);

  useEffect(() => {
    if (initialFilter && !availableInitials.has(initialFilter)) {
      setInitialFilter(null);
    }
  }, [availableInitials, initialFilter]);

  const handleSearch = () => {
    fetchAlbums(searchQuery);
  };

  const handleFilterChange = (newFilters: AlbumFilterValues) => {
    setFilters(newFilters);
  };

  const handleResetFilters = () => {
    setFilters({});
    fetchAlbums(searchQuery);
  };

  const totalPages = Math.ceil(groupedData.length / itemsPerPage);
  const visibleGroups = groupedData.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );
  const visibleAlbumIds = useMemo(() => {
    const albumIds: string[] = [];
    visibleGroups.forEach((artistGroup) => {
      artistGroup.albums.forEach((album) => {
        albumIds.push(album.id);
      });
    });
    return albumIds;
  }, [visibleGroups]);
  const albumOwners = useAlbumOwners(visibleAlbumIds);

  const handleDelete = async (albumId: string, albumTitle: string) => {
    if (!confirm(`Are you sure you want to delete "${albumTitle}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await albumsApi.delete(albumId);
      fetchAlbums(searchQuery);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete album');
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

  const getAlbumInitial = (title: string) => {
    const initial = title.trim().charAt(0);
    return initial ? initial.toUpperCase() : '?';
  };

  useEffect(() => {
    const filtersContent = (
      <>
        <AlbumFiltersPanel
          filters={filters}
          onFilterChange={handleFilterChange}
          onApply={handleSearch}
          onReset={handleResetFilters}
        />
        <div className="nav-filter-section">
          <label>Album Initial</label>
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
      viewKey: 'albums',
      searchPlaceholder: 'Search albums and artists...',
      searchValue: searchQuery,
      onSearchChange: setSearchQuery,
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
    searchQuery,
    setControls,
  ]);

  if (loading && albums.length === 0) {
    return <Loading message="Loading albums..." />;
  }

  return (
    <div className="albums-page">
      <div className="page-header">
        <div>
          <h1>Albums</h1>
          <p className="result-count">
            {filteredAlbums.length} {filteredAlbums.length === 1 ? 'album' : 'albums'} found
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={() => setShowWizardModal(true)}
        >
          <Icon path={mdiAlbum} className="btn-icon" />
          Add Album
        </button>
      </div>

      {error && <ErrorAlert message={error} onRetry={() => fetchAlbums()} />}

      {!loading && filteredAlbums.length === 0 && (
        <div className="no-results">
          <p>No albums found matching your search criteria.</p>
          <p>Try adjusting your search terms.</p>
        </div>
      )}

      <div className="albums-grouped">
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
                ({artistGroup.albums.length} {artistGroup.albums.length === 1 ? 'album' : 'albums'})
              </span>
            </div>

            {expandedArtists.has(artistGroup.artistId) && (
              <div className="albums-list">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Cover</th>
                      <th>Album</th>
                      <th>Year</th>
                      <th>Type</th>
                      <th>Genre</th>
                      <th>Styles</th>
                      <th>Label</th>
                      <th>Pressings</th>
                      <th>Owned</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {artistGroup.albums.map((album) => (
                      <tr key={album.id}>
                        <td className="album-cover-cell">
                          <div className="album-cover">
                            {album.image_url ? (
                              <img src={album.image_url} alt={`${album.title} cover`} />
                            ) : (
                              <span>{getAlbumInitial(album.title)}</span>
                            )}
                          </div>
                        </td>
                        <td className="name-cell">
                          {album.title}
                        </td>
                        <td>{album.release_year || '-'}</td>
                        <td>{album.release_type}</td>
                        <td>{album.genres.join(', ') || '-'}</td>
                        <td>{album.styles.join(', ') || '-'}</td>
                        <td>{album.label || '-'}</td>
                        <td>{album.pressing_count}</td>
                        <td className="owned-cell">
                          <OwnersGrid
                            owners={albumOwners[album.id] || album.owners || []}
                            currentUserId={currentUserId}
                            showEmpty
                          />
                        </td>
                        <td className="actions-cell">
                          <button
                            className="btn-action"
                            onClick={() => {
                              setSelectedAlbumForDetails(album.id);
                              setShowAlbumDetailsModal(true);
                            }}
                            title="View Details"
                            aria-label="View Details"
                          >
                            <Icon path={mdiEyeOutline} />
                          </button>
                          <button
                            className="btn-action"
                            onClick={() => {
                              setSelectedAlbumForPressing({ id: album.id, title: album.title, artistName: album.artist.name, discogsId: album.discogs_id || null });
                              setShowAddPressingModal(true);
                            }}
                            title="Add Pressing"
                            aria-label="Add Pressing"
                          >
                            <Icon path={mdiMusicBoxOutline} />
                          </button>
                          <button
                            className="btn-action"
                            onClick={() => {
                              setSelectedAlbumId(album.id);
                              setShowEditModal(true);
                            }}
                            title="Edit"
                            aria-label="Edit"
                          >
                            <Icon path={mdiPencilOutline} />
                          </button>
                          <button
                            className="btn-action btn-danger"
                            onClick={() => handleDelete(album.id, album.title)}
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
            )}
          </div>
        ))}
      </div>

      {loading && albums.length > 0 && (
        <Loading message="Loading more..." />
      )}

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

      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Add Album"
        size="large"
      >
        <AlbumWithPressingForm
          onSuccess={() => {
            setShowCreateModal(false);
            fetchAlbums(searchQuery);
          }}
          onCancel={() => setShowCreateModal(false)}
        />
      </Modal>

      <AlbumWizardModal
        isOpen={showWizardModal}
        onClose={() => setShowWizardModal(false)}
        onSuccess={() => {
          setShowWizardModal(false);
          fetchAlbums(searchQuery);
        }}
      />

      {selectedAlbumId && (
        <Modal
          isOpen={showEditModal}
          onClose={() => {
            setShowEditModal(false);
            setSelectedAlbumId(null);
          }}
          title="Edit Album"
          size="large"
        >
          <AlbumForm
            albumId={selectedAlbumId}
            onSuccess={() => {
              setShowEditModal(false);
              setSelectedAlbumId(null);
              fetchAlbums(searchQuery);
            }}
            onCancel={() => {
              setShowEditModal(false);
              setSelectedAlbumId(null);
            }}
          />
        </Modal>
      )}

      {selectedAlbumForPressing && (
        <PressingWizardModal
          albumId={selectedAlbumForPressing.id}
          albumTitle={selectedAlbumForPressing.title}
          artistName={selectedAlbumForPressing.artistName}
          discogsId={selectedAlbumForPressing.discogsId}
          isOpen={showAddPressingModal}
          onClose={() => {
            setShowAddPressingModal(false);
            setSelectedAlbumForPressing(null);
          }}
          onSuccess={() => {
            fetchAlbums(searchQuery);
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
    </div>
  );
}
