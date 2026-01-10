/**
 * Collection page - user's vinyl collection grouped by artist.
 */

import { useState, useEffect, useMemo } from 'react';
import { useMsal } from '@azure/msal-react';
import { collectionApi } from '@/api/services';
import { CollectionItemDetailResponse } from '@/types/api';
import { Loading, ErrorAlert, Modal, Icon } from '@/components/UI';
import { CollectionItemForm } from '@/components/Forms';
import { CollectionItemDetailsModal } from '@/components/Modals';
import { OwnersGrid } from '@/components/CollectionSharing';
import { mdiEyeOutline, mdiPencilOutline, mdiTrashCanOutline, mdiPlus } from '@mdi/js';
import { formatDecimal, parseLocaleNumber } from '@/utils/format';
import { AlphabetFilterBar } from '@/components/AlphabetFilterBar';
import { getInitialToken } from '@/utils/alpha';
import { usePreferences } from '@/hooks/usePreferences';
import { resolveItemsPerPage } from '@/utils/preferences';
import { useViewControls } from '@/components/Layout/ViewControlsContext';
import { usePressingOwners } from '@/hooks/usePressingOwners';
import './Collection.css';
import '../styles/Table.css';

// Group collection items by artist
interface ArtistGroup {
  artistId: string;
  artistName: string;
  sortName: string;
  country: string | undefined;
  albums: AlbumGroup[];
}

interface AlbumGroup {
  albumId: string;
  albumTitle: string;
  releaseYear: number | undefined;
  genres: string;
  items: CollectionItemDetailResponse[];
}

export function Collection() {
  const { accounts } = useMsal();
  const currentUserId = (accounts[0]?.idTokenClaims?.oid as string) || accounts[0]?.localAccountId || '';
  const [items, setItems] = useState<CollectionItemDetailResponse[]>([]);
  const [groupedData, setGroupedData] = useState<ArtistGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [showAlbumDetailsModal, setShowAlbumDetailsModal] = useState(false);
  const [selectedAlbumId, setSelectedAlbumId] = useState<string | null>(null);
  const [selectedAlbumItems, setSelectedAlbumItems] = useState<CollectionItemDetailResponse[]>([]);
  const [expandedArtists, setExpandedArtists] = useState<Set<string>>(new Set());
  const [initialFilter, setInitialFilter] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [playIncrementing, setPlayIncrementing] = useState<Set<string>>(new Set());
  const { preferences } = usePreferences();
  const { setControls } = useViewControls();

  const fetchCollection = async (query?: string) => {
    const cleanedQuery = query?.trim();
    try {
      setLoading(true);
      setError(null);
      const response = await collectionApi.getCollectionWithDetails({
        ...(cleanedQuery ? { query: cleanedQuery } : {}),
        limit: 500,
        offset: 0,
      });
      setItems(response.items);
      if (selectedAlbumId) {
        setSelectedAlbumItems(response.items.filter((item) => item.album?.id === selectedAlbumId));
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((entry: any) => entry.msg || 'Invalid request').join(', '));
      } else {
        setError(detail || 'Failed to load collection');
      }
    } finally {
      setLoading(false);
    }
  };

  const groupItems = (itemsToGroup: CollectionItemDetailResponse[]) => {
    const artistMap = new Map<string, ArtistGroup>();

    itemsToGroup.forEach((item) => {
      const artistKey = item.artist.id;

      if (!artistMap.has(artistKey)) {
        artistMap.set(artistKey, {
          artistId: item.artist.id,
          artistName: item.artist.name,
          sortName: item.artist.sort_name || item.artist.name,
          country: item.artist.country,
          albums: [],
        });
      }

      const artistGroup = artistMap.get(artistKey)!;
      let albumGroup = artistGroup.albums.find((a) => a.albumId === item.album.id);

      if (!albumGroup) {
        albumGroup = {
          albumId: item.album.id,
          albumTitle: item.album.title,
          releaseYear: item.album.release_year,
          genres: item.album.genres.join(', ') || '-',
          items: [],
        };
        artistGroup.albums.push(albumGroup);
      }

      albumGroup.items.push(item);
    });

    // Convert to array and sort
    const grouped = Array.from(artistMap.values()).sort((a, b) =>
      a.sortName.localeCompare(b.sortName)
    );

    setGroupedData(grouped);
  };

  useEffect(() => {
    fetchCollection();
  }, []);

  useEffect(() => {
    const storedPerPage = resolveItemsPerPage(preferences, 'collection');
    setItemsPerPage(storedPerPage);
    setCurrentPage(1);
  }, [preferences]);

  const availableInitials = useMemo(() => {
    const initials = new Set<string>();
    items.forEach((item) => {
      const initial = getInitialToken(item.artist?.sort_name || item.artist?.name);
      if (initial) initials.add(initial);
    });
    return initials;
  }, [items]);

  const filteredItems = useMemo(() => {
    if (!initialFilter) return items;
    return items.filter(
      (item) => getInitialToken(item.artist?.sort_name || item.artist?.name) === initialFilter
    );
  }, [items, initialFilter]);

  useEffect(() => {
    groupItems(filteredItems);
  }, [filteredItems]);

  useEffect(() => {
    if (initialFilter && !availableInitials.has(initialFilter)) {
      setInitialFilter(null);
    }
  }, [availableInitials, initialFilter]);

  const handleSearch = () => {
    fetchCollection(searchQuery);
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
        albumGroup.items.forEach((item) => {
          pressingIds.push(item.pressing_id);
        });
      });
    });
    return pressingIds;
  }, [visibleGroups]);
  const pressingOwners = usePressingOwners(visiblePressingIds);

  const handleDelete = async (itemId: string, albumTitle: string) => {
    if (!confirm(`Are you sure you want to remove "${albumTitle}" from your collection? This action cannot be undone.`)) {
      return;
    }

    const previousExpanded = new Set(expandedArtists);
    try {
      await collectionApi.removeItem(itemId);
      fetchCollection(searchQuery);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to remove item from collection');
      setExpandedArtists(previousExpanded);
    }
  };

  const handleIncrementPlay = async (albumId: string) => {
    if (playIncrementing.has(albumId)) {
      return;
    }
    if (!confirm('Log a play for this album?')) {
      return;
    }
    setPlayIncrementing((prev) => new Set(prev).add(albumId));
    try {
      await collectionApi.incrementAlbumPlayCount(albumId);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to increment play count');
    } finally {
      setPlayIncrementing((prev) => {
        const next = new Set(prev);
        next.delete(albumId);
        return next;
      });
    }
  };

  const openAlbumDetails = (album: AlbumGroup) => {
    setSelectedAlbumId(album.albumId);
    setSelectedAlbumItems(album.items);
    setShowAlbumDetailsModal(true);
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

  const getCollectionCover = (item: CollectionItemDetailResponse) => {
    return item.pressing_image_url || item.album.image_url || '';
  };

  const formatPrice = (price: number | undefined, currency: string | undefined) => {
    if (price === null || price === undefined) return '-';
    const numPrice = typeof price === 'string' ? parseLocaleNumber(price) : price;
    if (numPrice === null) return '-';
    if (Number.isNaN(numPrice)) return '-';
    return `${currency || 'USD'} ${formatDecimal(numPrice)}`;
  };

  const formatEstimatedPrice = (item: CollectionItemDetailResponse) => {
    const marketData = item.market_data;

    if (!marketData || marketData.median_value === null) {
      return <span className="price-pending">-</span>;
    }

    const currency = marketData.currency || 'USD';
    const minPrice = marketData.min_value !== null ? formatDecimal(marketData.min_value) : '-';
    const medianPrice = marketData.median_value !== null ? formatDecimal(marketData.median_value) : '-';
    const maxPrice = marketData.max_value !== null ? formatDecimal(marketData.max_value) : '-';

    return (
      <div className="estimated-price">
        <span className="price-line">Min: {currency} {minPrice}</span>
        <span className="price-line price-median">Avg: {currency} {medianPrice}</span>
        <span className="price-line">Max: {currency} {maxPrice}</span>
      </div>
    );
  };

  const formatAlbumTitle = (
    albumTitle: string,
    item: CollectionItemDetailResponse,
    genres: string
  ) => {
    const updatedDate = item.market_data?.updated_at
      ? new Date(item.market_data.updated_at).toLocaleDateString('en-GB')
      : null;

    return (
      <div className="album-title-cell">
        <span className="album-title">{albumTitle}</span>
        <span className="album-genre-mobile">{genres || '-'}</span>
        {updatedDate && (
          <span className="album-updated">Updated {updatedDate}</span>
        )}
      </div>
    );
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
      viewKey: 'collection',
      searchPlaceholder: 'Search your collection...',
      searchValue: searchQuery,
      onSearchChange: setSearchQuery,
      onSearchSubmit: handleSearch,
      filtersContent,
    });

    return () => setControls(null);
  }, [availableInitials, handleSearch, initialFilter, searchQuery, setControls]);

  if (loading && items.length === 0) {
    return <Loading message="Loading your collection..." />;
  }

  return (
    <div className="collection">
      <div className="collection-header">
        <h1>My Collection</h1>
        <p>{filteredItems.length} albums</p>
      </div>

      {error && <ErrorAlert message={error} onRetry={() => fetchCollection()} />}

      {!loading && items.length === 0 && (
        <div className="no-results">
          <p>No albums in your collection yet.</p>
          <p>Start adding albums to build your vinyl collection!</p>
        </div>
      )}

      <div className="collection-grouped">
        {visibleGroups.map((artistGroup) => (
          <div key={artistGroup.artistId} className="artist-group">
            <div
              className="artist-header"
              onClick={() => toggleArtist(artistGroup.artistId)}
            >
              <span className="expand-icon">
                {expandedArtists.has(artistGroup.artistId) ? 'v' : '>'}
              </span>
              <h2>{artistGroup.artistName}</h2>
              <span className="artist-count">
                ({artistGroup.albums.reduce((sum, album) => sum + album.items.length, 0)} albums)
              </span>
            </div>

            {expandedArtists.has(artistGroup.artistId) && (
              <div className="albums-list">
                <table className="data-table album-table">
                  <thead>
                    <tr>
                      <th className="col-cover">Cover</th>
                      <th className="col-album">Album</th>
                      <th className="col-year">Year</th>
                      <th className="col-genre">Genre</th>
                      <th className="col-purchase">Purchase Price</th>
                      <th className="col-est">Est. Sales Price</th>
                      <th className="col-condition">Condition (Media/Sleeve)</th>
                      <th className="col-owned">Owned</th>
                      <th className="col-play">Play</th>
                      <th className="col-actions">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {artistGroup.albums.map((album) => (
                      album.items.map((item, index) => {
                        const coverUrl = getCollectionCover(item);
                        return (
                          <tr key={item.id}>
                            <td className="collection-cover-cell col-cover">
                              <button
                                type="button"
                                className="collection-cover-button"
                                onClick={() => openAlbumDetails(album)}
                                title="View Details"
                                aria-label={`View ${album.albumTitle}`}
                              >
                                <div className="collection-cover">
                                  {coverUrl ? (
                                    <img src={coverUrl} alt="Pressing cover" />
                                  ) : (
                                    <span>?</span>
                                  )}
                                </div>
                              </button>
                            </td>
                            <td className="name-cell col-album">
                              {formatAlbumTitle(album.albumTitle, item, album.genres)}
                            </td>
                            {index === 0 && (
                              <>
                                <td rowSpan={album.items.length} className="col-year">{album.releaseYear || '-'}</td>
                                <td rowSpan={album.items.length} className="col-genre">{album.genres}</td>
                              </>
                            )}
                            <td className="col-purchase">{formatPrice(item.purchase_price, item.purchase_currency)}</td>
                            <td className="col-est">{formatEstimatedPrice(item)}</td>
                            <td className="col-condition">{item.media_condition} / {item.sleeve_condition}</td>
                            <td className="owned-cell col-owned">
                              <OwnersGrid
                                owners={pressingOwners[item.pressing_id] || []}
                                currentUserId={currentUserId}
                                showEmpty
                                className="owners-grid-large"
                              />
                            </td>
                            {index === 0 && (
                              <td rowSpan={album.items.length} className="col-play">
                                <button
                                  className="btn-action btn-action-play"
                                  onClick={() => handleIncrementPlay(album.albumId)}
                                  disabled={playIncrementing.has(album.albumId)}
                                  title="Add play"
                                  aria-label="Add play"
                                >
                                  <Icon path={mdiPlus} size={16} />
                                  <span className="play-count-label">1</span>
                                </button>
                              </td>
                            )}
                            <td className="actions-cell col-actions">
                              <button
                                className="btn-action btn-action-view"
                                onClick={() => openAlbumDetails(album)}
                                title="View Details"
                                aria-label="View Details"
                              >
                                <Icon path={mdiEyeOutline} />
                              </button>
                              <button
                                className="btn-action btn-action-edit"
                                onClick={() => {
                                  setSelectedItemId(item.id);
                                  setShowEditModal(true);
                                }}
                                title="Edit"
                                aria-label="Edit"
                              >
                                <Icon path={mdiPencilOutline} />
                              </button>
                              <button
                                className="btn-action btn-danger btn-action-delete"
                                onClick={() => handleDelete(item.id, album.albumTitle)}
                                title="Delete"
                                aria-label="Delete"
                              >
                                <Icon path={mdiTrashCanOutline} />
                              </button>
                            </td>
                          </tr>
                        );
                      })
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ))}
      </div>

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

      {loading && items.length > 0 && (
        <Loading message="Loading more..." />
      )}

      {selectedItemId && (
        <Modal
          isOpen={showEditModal}
          onClose={() => {
            setShowEditModal(false);
            setSelectedItemId(null);
          }}
          title="Edit Collection Item"
          size="medium"
        >
          <CollectionItemForm
            collectionItemId={selectedItemId}
            onSuccess={() => {
              setShowEditModal(false);
              setSelectedItemId(null);
              fetchCollection(searchQuery);
            }}
            onCancel={() => {
              setShowEditModal(false);
              setSelectedItemId(null);
            }}
          />
        </Modal>
      )}

      {selectedAlbumId && (
        <CollectionItemDetailsModal
          albumId={selectedAlbumId}
          items={selectedAlbumItems}
          currentUserId={currentUserId}
          isOpen={showAlbumDetailsModal}
          onClose={() => {
            setShowAlbumDetailsModal(false);
            setSelectedAlbumId(null);
            setSelectedAlbumItems([]); 
          }}
          onCollectionChange={() => fetchCollection(searchQuery)}
        />
      )}
    </div>
  );
}
