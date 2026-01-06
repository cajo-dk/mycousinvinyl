/**
 * Modal for viewing collection item details with album context.
 */

import { useEffect, useMemo, useState } from 'react';
import { useMsal } from '@azure/msal-react';
import { Modal } from '../UI/Modal';
import { ErrorAlert, Loading, Icon } from '../UI';
import { albumsApi, artistsApi, lookupApi, pressingsApi, collectionApi } from '@/api/services';
import type {
  AlbumResponse,
  CollectionItemDetailResponse,
  GenreResponse,
  PackagingResponse,
  PressingResponse,
  ReleaseTypeResponse,
  StyleResponse,
} from '@/types/api';
import { OwnersGrid } from '@/components/CollectionSharing';
import { AlbumForm, PressingForm } from '@/components/Forms';
import { PressingListItem } from '@/components/PressingListItem';
import { AddToCollectionModal } from './AddToCollectionModal';
import { PressingWizardModal } from './PressingWizardModal';
import { mdiPencilOutline, mdiPlus, mdiMusicBoxOutline } from '@mdi/js';
import { usePressingOwners } from '@/hooks/usePressingOwners';
import './AlbumDetailsModal.css';
import './CollectionItemDetailsModal.css';

interface CollectionItemDetailsModalProps {
  albumId: string;
  items: CollectionItemDetailResponse[];
  currentUserId?: string;
  isOpen: boolean;
  onClose: () => void;
  onCollectionChange?: () => void;
}

type CollectionPressing = {
  pressing: PressingResponse;
  packaging: PackagingResponse | null;
  item: CollectionItemDetailResponse;
};

export function CollectionItemDetailsModal({
  albumId,
  items,
  currentUserId,
  isOpen,
  onClose,
  onCollectionChange,
}: CollectionItemDetailsModalProps) {
  const { accounts } = useMsal();
  const [album, setAlbum] = useState<AlbumResponse | null>(null);
  const [artistName, setArtistName] = useState<string>('');
  const [pressingRows, setPressingRows] = useState<CollectionPressing[]>([]);
  const [genreLookup, setGenreLookup] = useState<Record<string, string>>({});
  const [styleLookup, setStyleLookup] = useState<Record<string, string>>({});
  const [releaseTypeLookup, setReleaseTypeLookup] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showEditAlbumModal, setShowEditAlbumModal] = useState(false);
  const [showEditPressingModal, setShowEditPressingModal] = useState(false);
  const [selectedPressingId, setSelectedPressingId] = useState<string | null>(null);
  const [showAddPressingModal, setShowAddPressingModal] = useState(false);
  const [showPressingPickerModal, setShowPressingPickerModal] = useState(false);
  const [pressingPickerPage, setPressingPickerPage] = useState(1);
  const [pressingPickerTotal, setPressingPickerTotal] = useState(0);
  const [pressingPickerItems, setPressingPickerItems] = useState<PressingResponse[]>([]);
  const [pressingPickerLoading, setPressingPickerLoading] = useState(false);
  const [selectedPressingForCollection, setSelectedPressingForCollection] = useState<PressingResponse | null>(null);
  const [showAddToCollectionModal, setShowAddToCollectionModal] = useState(false);
  const [collectionItems, setCollectionItems] = useState<CollectionItemDetailResponse[]>(items);

  const visibleItems = useMemo(
    () => collectionItems.filter((item) => item.album?.id === albumId),
    [albumId, collectionItems]
  );
  const visiblePressingIds = useMemo(
    () => visibleItems.map((item) => item.pressing_id),
    [visibleItems]
  );
  const pressingOwners = usePressingOwners(visiblePressingIds);
  const pressingPickerIds = useMemo(
    () => pressingPickerItems.map((pressing) => pressing.id),
    [pressingPickerItems]
  );
  const pressingPickerOwners = usePressingOwners(pressingPickerIds);

  useEffect(() => {
    if (isOpen && albumId) {
      fetchData();
    }
  }, [albumId, isOpen, visibleItems.length]);

  useEffect(() => {
    setCollectionItems(items);
  }, [items]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [albumData, genresData, stylesData, releaseTypesData] = await Promise.all([
        albumsApi.getById(albumId),
        lookupApi.getAllGenres(),
        lookupApi.getAllStyles(),
        lookupApi.getAllReleaseTypes(),
      ]);

      setAlbum(albumData);

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

      const pressings = await Promise.all(
        visibleItems.map(async (item) => {
          const [pressing, packaging] = await Promise.all([
            pressingsApi.getById(item.pressing_id),
            pressingsApi.getPackaging(item.pressing_id).catch(() => null),
          ]);
          return { pressing, packaging, item };
        })
      );

      setPressingRows(pressings);
    } catch (err: any) {
      console.error('Failed to load collection item details:', err);
      setError(err.response?.data?.detail || 'Failed to load collection item details');
    } finally {
      setLoading(false);
    }
  };

  const fetchAlbumPressings = async (page: number) => {
    if (!albumId) return;
    try {
      setPressingPickerLoading(true);
      const limit = pressingPickerPageSize;
      const offset = (page - 1) * pressingPickerPageSize;
      const response = await pressingsApi.getByAlbum(albumId, { limit, offset });
      setPressingPickerItems(response.items);
      setPressingPickerTotal(response.total);
    } catch (err) {
      console.error('Failed to load album pressings:', err);
    } finally {
      setPressingPickerLoading(false);
    }
  };

  const refreshCollectionItems = async () => {
    try {
      const response = await collectionApi.getCollectionWithDetails({ limit: 500, offset: 0 });
      setCollectionItems(response.items);
    } catch (err) {
      console.error('Failed to refresh collection items:', err);
    }
  };

  useEffect(() => {
    if (!showPressingPickerModal) return;
    fetchAlbumPressings(pressingPickerPage);
  }, [albumId, pressingPickerPage, showPressingPickerModal]);

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

  const getCollectionValue = (value?: string | null) => {
    if (!value) return '-';
    const trimmed = value.trim();
    return trimmed ? trimmed : '-';
  };

  const currentUserName = accounts[0]?.name || 'Unknown';
  const albumUpdatedAt = album?.updated_at
    ? new Date(album.updated_at).toLocaleString()
    : '-';
  const pressingPickerPageSize = 5;
  const pressingPickerTotalPages = Math.max(1, Math.ceil(pressingPickerTotal / pressingPickerPageSize));

  const formatPressingDescription = (pressing: PressingResponse) => {
    const year = pressing.release_year ?? pressing.pressing_year ?? '-';
    const country = getCountryName(pressing.country ?? pressing.pressing_country);
    return `${year} ${country} ${pressing.size_inches} ${pressing.format}`;
  };

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} title="Collection Item Details" size="large">
        {loading && <Loading message="Loading collection item details..." />}

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
                <div className="album-details-title-row">
                  <h3>{album.title}</h3>
                  <button
                    type="button"
                    className="btn-action album-details-edit"
                    onClick={() => setShowEditAlbumModal(true)}
                    aria-label="Edit Album"
                    title="Edit Album"
                  >
                    <Icon path={mdiPencilOutline} />
                  </button>
                </div>
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
                  <div>
                    <span className="album-details-label">Last Update</span>
                    <div className="collection-item-updated">
                      <span>{albumUpdatedAt}</span>
                      <span className="collection-item-updated-by">{currentUserName}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="album-details-notes">
              <span className="album-details-label">Notes</span>
              <span>{getAlbumNotes(album) || '-'}</span>
            </div>

            <div>
              <div className="collection-items-header">
                <h4>Items in Collection ({visibleItems.length})</h4>
                <button
                  type="button"
                  className="btn-primary"
                  onClick={() => {
                    setPressingPickerPage(1);
                    setShowPressingPickerModal(true);
                  }}
                >
                  <Icon path={mdiPlus} className="btn-icon" />
                  Add Pressing
                </button>
              </div>

              {pressingRows.length === 0 ? (
                <div className="collection-items-empty">
                  <p>No collection items found for this album.</p>
                </div>
              ) : (
                <div>
                {pressingRows.map(({ pressing, packaging, item }) => {
                  const formatDetails = `${pressing.size_inches} ${pressing.format} at ${pressing.speed_rpm} RPM`;
                  const coverUrl = pressing.image_url || item.pressing_image_url || album.image_url;
                  const discCount = pressing.disc_count ?? '-';
                    const pressingPlant = pressing.pressing_plant || '-';
                  const masteringEngineer = pressing.mastering_engineer || '-';
                  const masteringStudio = pressing.mastering_studio || '-';
                  const labelDesign = pressing.label_design || '-';
                  const vinylColor = pressing.vinyl_color ?? '-';
                  const editionType = pressing.edition_type ?? '-';
                  const sleeveType = packaging?.sleeve_type ?? '-';
                  const discogsReleaseId = pressing.discogs_release_id || '-';
                  const discogsMasterId = pressing.discogs_master_id || '-';
                  const barcode = pressing.barcode || '-';
                    const notes = pressing.notes || '-';
                    const country = getCountryName(pressing.country ?? pressing.pressing_country);
                    const releaseYear = pressing.release_year ?? pressing.pressing_year ?? '-';
                    const updatedAt = pressing.updated_at
                      ? new Date(pressing.updated_at).toLocaleString()
                      : '-';

                    return (
                      <div key={item.id} className="collection-item-card">
                        <div className="collection-item-card-header">
                          <span className="collection-item-card-title">Pressing Details</span>
                          <button
                            type="button"
                            className="btn-action"
                            onClick={() => {
                              setSelectedPressingId(pressing.id);
                              setShowEditPressingModal(true);
                            }}
                            aria-label="Edit Pressing"
                            title="Edit Pressing"
                          >
                            <Icon path={mdiPencilOutline} />
                          </button>
                        </div>
                        <div className="collection-item-card-main">
                          <div className="collection-item-cover-stack">
                            <div className="collection-item-cover">
                              {coverUrl ? (
                                <img src={coverUrl} alt="Pressing cover" />
                              ) : (
                                <span>No cover</span>
                              )}
                            </div>
                            {currentUserId && (
                              <OwnersGrid
                                owners={pressingOwners[item.pressing_id] || []}
                                currentUserId={currentUserId}
                                showEmpty
                                className="owners-grid-large"
                              />
                            )}
                          </div>
                          <div className="collection-item-details-grid">
                            <div><span className="collection-item-label">Format</span>{formatDetails}</div>
                            <div><span className="collection-item-label">Disc Count</span>{discCount}</div>
                            <div><span className="collection-item-label">Release Year</span>{releaseYear}</div>
                            <div><span className="collection-item-label">Country</span>{country}</div>
                            <div><span className="collection-item-label">Pressing Plant</span>{pressingPlant}</div>
                            <div><span className="collection-item-label">Mastering Engineer</span>{masteringEngineer}</div>
                            <div><span className="collection-item-label">Mastering Studio</span>{masteringStudio}</div>
                            <div><span className="collection-item-label">Vinyl Color</span>{vinylColor}</div>
                          <div><span className="collection-item-label">Label Design</span>{labelDesign}</div>
                          <div><span className="collection-item-label">Discogs Release ID</span>{discogsReleaseId}</div>
                          <div><span className="collection-item-label">Discogs Master ID</span>{discogsMasterId}</div>
                          <div><span className="collection-item-label">Edition Type</span>{editionType}</div>
                          <div><span className="collection-item-label">Sleeve Type</span>{sleeveType}</div>
                          <div>
                            <span className="collection-item-label">Last Update</span>
                            <div className="collection-item-updated">
                              <span>{updatedAt}</span>
                              <span className="collection-item-updated-by">{currentUserName}</span>
                            </div>
                          </div>
                          <div>
                            <span className="collection-item-label">Barcode / Identifiers</span>
                            <span className="collection-item-truncate">{barcode}</span>
                          </div>
                          <div className="collection-item-detail-span">
                            <span className="collection-item-label">Notes</span>
                            <span className="collection-item-truncate">{notes}</span>
                          </div>
                          </div>
                        </div>
                        <div className="collection-item-divider" />
                        <div className="collection-item-meta-grid">
                          <div>
                            <span className="collection-item-label">Notes</span>
                            <span>{getCollectionValue(item.notes)}</span>
                          </div>
                          <div>
                            <span className="collection-item-label">Defect Notes</span>
                            <span>{getCollectionValue(item.defect_notes)}</span>
                          </div>
                          <div>
                            <span className="collection-item-label">Storage Location</span>
                            <span>{getCollectionValue(item.location)}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>
      {album && (
        <Modal
          isOpen={showEditAlbumModal}
          onClose={() => setShowEditAlbumModal(false)}
          title="Edit Album"
          size="large"
        >
          <AlbumForm
            albumId={album.id}
            onSuccess={() => {
              setShowEditAlbumModal(false);
              fetchData();
              onCollectionChange?.();
            }}
            onCancel={() => setShowEditAlbumModal(false)}
          />
        </Modal>
      )}

      {selectedPressingId && (
        <Modal
          isOpen={showEditPressingModal}
          onClose={() => {
            setShowEditPressingModal(false);
            setSelectedPressingId(null);
          }}
          title="Edit Pressing"
          size="large"
        >
          <PressingForm
            pressingId={selectedPressingId}
            onSuccess={() => {
              setShowEditPressingModal(false);
              setSelectedPressingId(null);
              fetchData();
              onCollectionChange?.();
            }}
            onCancel={() => {
              setShowEditPressingModal(false);
              setSelectedPressingId(null);
            }}
          />
        </Modal>
      )}
      <Modal
        isOpen={showPressingPickerModal}
        onClose={() => setShowPressingPickerModal(false)}
        title="Add Pressing to Collection"
        size="large"
      >
        <div className="collection-pressing-picker">
          <div className="collection-pressing-picker-header">
            <div>
              <h4>Pressings ({pressingPickerTotal})</h4>
              <p>Select an existing pressing or create a new one.</p>
            </div>
            <button
              type="button"
              className="btn-primary"
              onClick={() => setShowAddPressingModal(true)}
            >
              <Icon path={mdiMusicBoxOutline} className="btn-icon" />
              Create New Pressing
            </button>
          </div>

          {pressingPickerLoading ? (
            <Loading message="Loading pressings..." />
          ) : (
            <div className="collection-pressing-picker-list">
              {pressingPickerItems.length === 0 ? (
                <div className="collection-items-empty">
                  <p>No pressings found for this album.</p>
                </div>
              ) : (
                pressingPickerItems.map((pressing) => (
                  <PressingListItem
                    key={pressing.id}
                    pressing={pressing}
                    onAddToCollection={(pressingId) => {
                      const selected = pressingPickerItems.find((item) => item.id === pressingId) || null;
                      setSelectedPressingForCollection(selected);
                      setShowAddToCollectionModal(true);
                    }}
                    fallbackImageUrl={album?.image_url}
                    owners={pressingPickerOwners[pressing.id] || []}
                    currentUserId={currentUserId}
                  />
                ))
              )}
            </div>
          )}

          {pressingPickerTotalPages > 1 && (
            <div className="collection-pressing-picker-pagination">
              <button
                type="button"
                className="pagination-button"
                onClick={() => setPressingPickerPage((prev) => Math.max(1, prev - 1))}
                disabled={pressingPickerPage === 1}
              >
                Previous
              </button>
              <span>
                Page {pressingPickerPage} of {pressingPickerTotalPages}
              </span>
              <button
                type="button"
                className="pagination-button"
                onClick={() => setPressingPickerPage((prev) => Math.min(pressingPickerTotalPages, prev + 1))}
                disabled={pressingPickerPage === pressingPickerTotalPages}
              >
                Next
              </button>
            </div>
          )}
        </div>
      </Modal>

      {selectedPressingForCollection && (
        <AddToCollectionModal
          pressingId={selectedPressingForCollection.id}
          pressingDescription={formatPressingDescription(selectedPressingForCollection)}
          isOpen={showAddToCollectionModal}
          onClose={() => {
            setShowAddToCollectionModal(false);
            setSelectedPressingForCollection(null);
          }}
          onSuccess={() => {
            setShowAddToCollectionModal(false);
            setSelectedPressingForCollection(null);
            setShowPressingPickerModal(false);
            refreshCollectionItems();
            fetchData();
            onCollectionChange?.();
          }}
        />
      )}

      {album && (
        <PressingWizardModal
          albumId={albumId}
          albumTitle={album.title}
          artistName={artistName}
          discogsId={album.discogs_id}
          isOpen={showAddPressingModal}
          onClose={() => setShowAddPressingModal(false)}
          onSuccess={() => {
            setShowAddPressingModal(false);
            fetchData();
            fetchAlbumPressings(pressingPickerPage);
            onCollectionChange?.();
          }}
        />
      )}
    </>
  );
}
