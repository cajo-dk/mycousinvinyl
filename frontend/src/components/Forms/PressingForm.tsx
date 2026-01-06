/**
 * Pressing creation form with optional "Add to Collection" functionality.
 */

import { useState, useEffect, FormEvent } from 'react';
import { pressingsApi, albumsApi, lookupApi, collectionApi, discogsApi } from '@/api/services';
import { AlbumResponse, CountryResponse, PackagingResponse, VinylFormat, VinylSpeed, VinylSize, EditionTypeResponse, SleeveTypeResponse, Condition, CollectionItemCreate, DiscogsReleaseSearchResult, DiscogsReleaseDetails } from '@/types/api';
import { usePreferences } from '@/hooks/usePreferences';
import { parseLocaleNumber } from '@/utils/format';
import { DiscogsReleaseSearchModal } from '@/components/Modals';
import './Form.css';

interface PressingFormProps {
  pressingId?: string;
  albumId?: string; // Optional: pre-select an album
  albumTitle?: string; // Optional: display album title
  showAddToCollection?: boolean; // Optional: show "Add to Collection" checkbox (default: false)
  onSuccess: () => void;
  onCancel: () => void;
}

// Backend enum options
const VINYL_FORMAT_OPTIONS = [
  { value: VinylFormat.LP, label: 'LP' },
  { value: VinylFormat.EP, label: 'EP' },
  { value: VinylFormat.SINGLE, label: 'Single' },
  { value: VinylFormat.MAXI, label: 'Maxi Single' },
  { value: VinylFormat.CD, label: 'CD' },
];

const VINYL_SPEED_OPTIONS = [
  { value: VinylSpeed.RPM_33, label: '33 1/3 RPM' },
  { value: VinylSpeed.RPM_45, label: '45 RPM' },
  { value: VinylSpeed.RPM_78, label: '78 RPM' },
];

const VINYL_SIZE_OPTIONS = [
  { value: VinylSize.SIZE_7, label: '7"' },
  { value: VinylSize.SIZE_10, label: '10"' },
  { value: VinylSize.SIZE_12, label: '12"' },
];

const CD_SPEED_OPTIONS = [{ value: VinylSpeed.NA, label: 'N/A' }];
const CD_SIZE_OPTIONS = [{ value: VinylSize.CD, label: 'CD' }];

const CONDITION_OPTIONS = [
  { value: Condition.MINT, label: 'Mint (M)' },
  { value: Condition.NEAR_MINT, label: 'Near Mint (NM)' },
  { value: Condition.VG_PLUS, label: 'Very Good Plus (VG+)' },
  { value: Condition.VG, label: 'Very Good (VG)' },
  { value: Condition.GOOD, label: 'Good (G)' },
  { value: Condition.POOR, label: 'Poor (P)' },
];

export function PressingForm({ pressingId, albumId, albumTitle, showAddToCollection = false, onSuccess, onCancel }: PressingFormProps) {
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(!!pressingId);
  const [error, setError] = useState<string | null>(null);
  const [albums, setAlbums] = useState<AlbumResponse[]>([]);
  const [countries, setCountries] = useState<CountryResponse[]>([]);
  const [editionTypes, setEditionTypes] = useState<EditionTypeResponse[]>([]);
  const [sleeveTypes, setSleeveTypes] = useState<SleeveTypeResponse[]>([]);
  const [packaging, setPackaging] = useState<PackagingResponse | null>(null);
  const [imageTouched, setImageTouched] = useState(false);
  const [addToCollection, setAddToCollection] = useState(showAddToCollection);
  const [discogsResults, setDiscogsResults] = useState<DiscogsReleaseSearchResult[]>([]);
  const [discogsLoading, setDiscogsLoading] = useState(false);
  const [discogsError, setDiscogsError] = useState<string | null>(null);
  const [discogsSelectedId, setDiscogsSelectedId] = useState<number | null>(null);
  const [importMasterReleases, setImportMasterReleases] = useState(false);
  const [albumDiscogsId, setAlbumDiscogsId] = useState<number | null>(null);
  const [showDiscogsModal, setShowDiscogsModal] = useState(false);
  const isEditMode = !!pressingId;
  const { preferences } = usePreferences();

  const [formData, setFormData] = useState({
    album_id: albumId || '',
    format: VinylFormat.LP,
    speed_rpm: VinylSpeed.RPM_33,
    size_inches: VinylSize.SIZE_12,
    disc_count: '1',
    country: '',
    release_year: '',
    pressing_plant: '',
    mastering_engineer: '',
    mastering_studio: '',
    vinyl_color: '',
    label_design: '',
    image_url: '',
    edition_type: '',
    sleeve_type: '',
    barcode: '',
    notes: '',
    discogs_release_id: null as number | null,
    discogs_master_id: null as number | null,
    master_title: '',
    // Collection fields
    media_condition: Condition.NEAR_MINT,
    sleeve_condition: Condition.NEAR_MINT,
    purchase_price: '',
    purchase_currency: 'USD',
    purchase_date: '',
    location: '',
  });

  // Load lookup data and pressing data on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        if (albumId) {
          const album = await albumsApi.getById(albumId);
          setAlbumDiscogsId(album.discogs_id ?? null);
        }

        // Only load albums if not pre-selected
        const promises: Promise<any>[] = [
          lookupApi.getAllCountries(),
          lookupApi.getAllEditionTypes(),
          lookupApi.getAllSleeveTypes(),
        ];
        if (!albumId) {
          promises.unshift(albumsApi.search({ limit: 1000 }));
        }

        const results = await Promise.all(promises);

        if (!albumId) {
          setAlbums(results[0].items);
          setCountries(results[1]);
          setEditionTypes(results[2]);
          setSleeveTypes(results[3]);
        } else {
          setCountries(results[0]);
          setEditionTypes(results[1]);
          setSleeveTypes(results[2]);
        }

        // Load existing pressing if in edit mode
        if (pressingId) {
          const [pressing, packaging] = await Promise.all([
            pressingsApi.getById(pressingId),
            pressingsApi.getPackaging(pressingId).catch(() => null),
          ]);
          setPackaging(packaging);
          setImageTouched(false);
          setFormData((prev) => ({
            ...prev,
            album_id: pressing.album_id || '',
            format: pressing.format || VinylFormat.LP,
            speed_rpm: pressing.speed_rpm || VinylSpeed.RPM_33,
            size_inches: pressing.size_inches || VinylSize.SIZE_12,
            disc_count: pressing.disc_count?.toString() || '1',
            country: pressing.country || pressing.pressing_country || '',
            release_year: (pressing.release_year ?? pressing.pressing_year)?.toString() || '',
            pressing_plant: pressing.pressing_plant || '',
            mastering_engineer: pressing.mastering_engineer || '',
            mastering_studio: pressing.mastering_studio || '',
            vinyl_color: pressing.vinyl_color || '',
            label_design: pressing.label_design || '',
            image_url: pressing.image_url || '',
            edition_type: pressing.edition_type || '',
            sleeve_type: packaging?.sleeve_type || '',
            barcode: pressing.barcode || '',
            notes: pressing.notes || '',
            discogs_release_id: pressing.discogs_release_id ?? null,
            discogs_master_id: pressing.discogs_master_id ?? null,
            master_title: pressing.master_title || '',
          }));
          if (!albumId && pressing.album_id) {
            const album = await albumsApi.getById(pressing.album_id);
            setAlbumDiscogsId(album.discogs_id ?? null);
          }
        }
      } catch (err: any) {
        console.error('Failed to load data:', err);
        setError(err.response?.data?.detail || 'Failed to load form data. Please try again.');
      } finally {
        setInitialLoading(false);
      }
    };
    loadData();
  }, [pressingId, albumId]);

  useEffect(() => {
    if (preferences?.currency) {
      setFormData((prev) => ({ ...prev, purchase_currency: preferences.currency }));
    }
  }, [preferences?.currency]);

  useEffect(() => {
    if (albumId) {
      resetDiscogsState();
      return;
    }
    if (!albums.length) {
      return;
    }
    const selected = albums.find((album) => album.id === formData.album_id);
    setAlbumDiscogsId(selected?.discogs_id ?? null);
    if (!isEditMode) {
      setFormData((prev) => ({
        ...prev,
        discogs_release_id: null,
        discogs_master_id: null,
        master_title: '',
      }));
    }
    resetDiscogsState();
  }, [albumId, albums, formData.album_id, isEditMode]);

  const resetDiscogsState = () => {
    setDiscogsResults([]);
    setDiscogsError(null);
    setDiscogsSelectedId(null);
    setImportMasterReleases(false);
  };

  const closeDiscogsResults = () => {
    setDiscogsResults([]);
    setDiscogsError(null);
    setDiscogsSelectedId(null);
  };

  const getSelectedAlbumDiscogsId = () => {
    if (albumId) {
      return albumDiscogsId;
    }
    const selected = albums.find((album) => album.id === formData.album_id);
    return selected?.discogs_id ?? null;
  };

  const mapDiscogsFormat = (details: DiscogsReleaseDetails) => {
    const tokens = [
      ...(details.formats || []),
      ...(details.format_descriptions || []),
    ].map((value) => value.toLowerCase());
    const combined = tokens.join(' ');

    if (combined.includes('cd')) return VinylFormat.CD;
    if (combined.includes('ep')) return VinylFormat.EP;
    if (combined.includes('single')) return VinylFormat.SINGLE;
    if (combined.includes('maxi')) return VinylFormat.MAXI;
    return VinylFormat.LP;
  };

  const mapDiscogsSpeed = (details: DiscogsReleaseDetails) => {
    const tokens = [
      ...(details.formats || []),
      ...(details.format_descriptions || []),
    ].map((value) => value.toLowerCase());
    const combined = tokens.join(' ');

    if (combined.includes('cd')) return VinylSpeed.NA;
    if (combined.includes('78')) return VinylSpeed.RPM_78;
    if (combined.includes('45')) return VinylSpeed.RPM_45;
    return VinylSpeed.RPM_33;
  };

  const mapDiscogsSize = (details: DiscogsReleaseDetails) => {
    const tokens = [
      ...(details.formats || []),
      ...(details.format_descriptions || []),
    ].map((value) => value.toLowerCase());
    const combined = tokens.join(' ');

    if (combined.includes('cd')) return VinylSize.CD;
    if (combined.includes('7"')) return VinylSize.SIZE_7;
    if (combined.includes('10"')) return VinylSize.SIZE_10;
    return VinylSize.SIZE_12;
  };

  const resolveCountryCode = (value: string | undefined | null) => {
    if (!value) return '';
    const trimmed = value.trim();
    if (trimmed.length === 2) {
      const code = trimmed.toUpperCase();
      return countries.some((country) => country.code === code) ? code : '';
    }
    const match = countries.find(
      (country) => country.name.toLowerCase() === trimmed.toLowerCase()
    );
    return match?.code || '';
  };

  const resolveEditionType = async (value: string | undefined | null) => {
    if (!value) return null;
    const trimmed = value.trim();
    if (!trimmed) return null;
    const existing = editionTypes.find(
      (type) =>
        type.code.toLowerCase() === trimmed.toLowerCase() ||
        type.name.toLowerCase() === trimmed.toLowerCase()
    );
    if (existing) {
      return existing.code;
    }
    try {
      const created = await lookupApi.createEditionType({ code: trimmed, name: trimmed });
      setEditionTypes((prev) => [...prev, created]);
      return created.code;
    } catch (err) {
      console.warn('Failed to create edition type from Discogs:', err);
      return null;
    }
  };

  const applyDiscogsRelease = async (details: DiscogsReleaseDetails) => {
    const countryCode = resolveCountryCode(details.country);
    const identifiers = details.identifiers || details.barcode || '';
    const resolvedEditionType = await resolveEditionType(details.edition_type || 'Standard');
    const vinylColor = details.vinyl_color || 'Black';
    setFormData((prev) => ({
      ...prev,
      format: mapDiscogsFormat(details),
      speed_rpm: mapDiscogsSpeed(details),
      size_inches: mapDiscogsSize(details),
      disc_count: details.disc_count ? String(details.disc_count) : prev.disc_count,
      release_year: details.year ? String(details.year) : prev.release_year,
      country: countryCode || prev.country,
      pressing_plant: details.pressing_plant || prev.pressing_plant,
      mastering_engineer: details.mastering_engineer || prev.mastering_engineer,
      mastering_studio: details.mastering_studio || prev.mastering_studio,
      vinyl_color: vinylColor || prev.vinyl_color,
      label_design: details.label || prev.label_design,
      edition_type: resolvedEditionType || prev.edition_type,
      sleeve_type: details.sleeve_type || prev.sleeve_type,
      barcode: identifiers || prev.barcode,
      image_url: details.image_url || prev.image_url,
      discogs_release_id: details.id,
      discogs_master_id: details.master_id || prev.discogs_master_id,
      master_title: details.master_title || prev.master_title,
    }));
    setImageTouched(true);
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    if (name === 'format') {
      setFormData((prev) => {
        if (value === VinylFormat.CD) {
          return {
            ...prev,
            format: VinylFormat.CD,
            speed_rpm: VinylSpeed.NA,
            size_inches: VinylSize.CD,
          };
        }
        const nextSpeed = prev.speed_rpm === VinylSpeed.NA ? VinylSpeed.RPM_33 : prev.speed_rpm;
        const nextSize = prev.size_inches === VinylSize.CD ? VinylSize.SIZE_12 : prev.size_inches;
        return {
          ...prev,
          format: value as VinylFormat,
          speed_rpm: nextSpeed,
          size_inches: nextSize,
        };
      });
      return;
    }
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const result = typeof reader.result === 'string' ? reader.result : '';
      setFormData((prev) => ({
        ...prev,
        image_url: result,
      }));
      setImageTouched(true);
    };
    reader.readAsDataURL(file);
  };

  const handleImageRemove = () => {
    setFormData((prev) => ({
      ...prev,
      image_url: '',
    }));
    setImageTouched(true);
  };

  const handleDiscogsSearch = async () => {
    const discogsId = getSelectedAlbumDiscogsId();
    if (!discogsId) {
      setDiscogsError('Select an album with a Discogs ID to search releases.');
      return;
    }

    setDiscogsLoading(true);
    setDiscogsError(null);
    setDiscogsSelectedId(null);
    setImportMasterReleases(false);
    try {
      const response = await discogsApi.getMasterReleases(discogsId, 1, 10);
      setDiscogsResults(response.items);
      if (response.items.length === 0) {
        setDiscogsError('No releases found for this master.');
      }
    } catch (err: any) {
      setDiscogsError(err.response?.data?.detail || err.message || 'Discogs lookup failed.');
    } finally {
      setDiscogsLoading(false);
    }
  };

  const handleDiscogsSelect = async (result: DiscogsReleaseSearchResult) => {
    setDiscogsSelectedId(result.id);
    setImportMasterReleases(false);
    if (result.type === 'master') {
      setFormData((prev) => ({
        ...prev,
        discogs_master_id: result.id,
        discogs_release_id: null,
      }));
      return;
    }

    try {
      setDiscogsLoading(true);
      const details = await discogsApi.getRelease(result.id);
      await applyDiscogsRelease(details);
      closeDiscogsResults();
    } catch (err: any) {
      setDiscogsError(err.response?.data?.detail || err.message || 'Discogs release lookup failed.');
    } finally {
      setDiscogsLoading(false);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.album_id) {
      setError('Album is required');
      return;
    }

    const discCount = parseInt(formData.disc_count);
    if (isNaN(discCount) || discCount < 1 || discCount > 10) {
      setError('Disc count must be between 1 and 10');
      return;
    }

    setLoading(true);

    try {
      const payload: any = {
        album_id: formData.album_id,
        format: formData.format,
        speed_rpm: formData.speed_rpm,
        size_inches: formData.size_inches,
        disc_count: discCount,
      };

      // Add optional fields if provided
      if (formData.country) payload.country = formData.country;
      if (formData.release_year) {
        const year = parseInt(formData.release_year);
        if (!isNaN(year)) {
          payload.release_year = year;
        }
      }
      if (formData.pressing_plant) payload.pressing_plant = formData.pressing_plant;
      if (formData.mastering_engineer) payload.mastering_engineer = formData.mastering_engineer;
      if (formData.mastering_studio) payload.mastering_studio = formData.mastering_studio;
      if (formData.vinyl_color) payload.vinyl_color = formData.vinyl_color;
      if (formData.label_design) payload.label_design = formData.label_design;
      if (formData.image_url && (!isEditMode || imageTouched)) {
        payload.image_url = formData.image_url;
      } else if (isEditMode && imageTouched && !formData.image_url) {
        payload.image_url = null;
      }
      if (formData.edition_type) payload.edition_type = formData.edition_type;
      if (formData.barcode) payload.barcode = formData.barcode;
      if (formData.notes) payload.notes = formData.notes;
      if (formData.discogs_release_id) payload.discogs_release_id = formData.discogs_release_id;
      if (formData.discogs_master_id) payload.discogs_master_id = formData.discogs_master_id;
      if (formData.master_title) payload.master_title = formData.master_title;
      if (!isEditMode && importMasterReleases) {
        payload.import_master_releases = true;
      }

      if (isEditMode && pressingId) {
        await pressingsApi.update(pressingId, payload);
        if (formData.sleeve_type) {
          const packagingPayload = packaging ? {
            pressing_id: pressingId,
            sleeve_type: formData.sleeve_type,
            has_inner_sleeve: packaging.has_inner_sleeve,
            inner_sleeve_description: packaging.inner_sleeve_description,
            has_insert: packaging.has_insert,
            insert_description: packaging.insert_description,
            has_poster: packaging.has_poster,
            poster_description: packaging.poster_description,
            sticker_info: packaging.sticker_info,
            notes: packaging.notes,
          } : {
            pressing_id: pressingId,
            sleeve_type: formData.sleeve_type,
            has_inner_sleeve: false,
            has_insert: false,
            has_poster: false,
          };
          const updatedPackaging = await pressingsApi.upsertPackaging(pressingId, packagingPayload);
          setPackaging(updatedPackaging);
        }
        onSuccess();
      } else {
        // Step 1: Create pressing
        const pressing = await pressingsApi.create(payload);

        if (formData.sleeve_type) {
          const createdPackaging = await pressingsApi.upsertPackaging(pressing.id, {
            pressing_id: pressing.id,
            sleeve_type: formData.sleeve_type,
            has_inner_sleeve: false,
            has_insert: false,
            has_poster: false,
          });
          setPackaging(createdPackaging);
        }

        // Step 2: Add to collection if checkbox is checked
        if (addToCollection && showAddToCollection) {
          try {
            const collectionPayload: CollectionItemCreate = {
              pressing_id: pressing.id,
              media_condition: formData.media_condition,
              sleeve_condition: formData.sleeve_condition,
            };

            // Add optional collection fields if provided
          if (formData.purchase_price) {
            const price = parseLocaleNumber(formData.purchase_price);
            if (price !== null && price >= 0) {
              collectionPayload.purchase_price = price;
            }
          }
            if (formData.purchase_currency) collectionPayload.purchase_currency = formData.purchase_currency;
            if (formData.purchase_date) collectionPayload.purchase_date = formData.purchase_date;
            if (formData.location) collectionPayload.location = formData.location;

            await collectionApi.addItem(collectionPayload);
          } catch (collectionErr: any) {
            // Pressing was created but collection add failed
            console.error('Failed to add to collection:', collectionErr);
            const errorMsg = collectionErr.response?.data?.detail || collectionErr.message;
            setError(
              `Pressing created successfully (ID: ${pressing.id}) but failed to add to collection: ${errorMsg}. ` +
              `You can add it to your collection later.`
            );
            setLoading(false);
            return; // Don't call onSuccess yet, let user dismiss the error
          }
        }

        onSuccess();
      }
    } catch (err: any) {
      console.error(`Failed to ${isEditMode ? 'update' : 'create'} pressing:`, err);

      // Handle validation errors (422) which return detail as an array
      let errorMessage = `Failed to ${isEditMode ? 'update' : 'create'} pressing`;
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

  const speedOptions = formData.format === VinylFormat.CD ? CD_SPEED_OPTIONS : VINYL_SPEED_OPTIONS;
  const sizeOptions = formData.format === VinylFormat.CD ? CD_SIZE_OPTIONS : VINYL_SIZE_OPTIONS;

  if (initialLoading) {
    return <div className="form-loading">Loading pressing data...</div>;
  }

  return (
    <>
    <form className="form" onSubmit={handleSubmit}>
      {error && <div className="form-error">{error}</div>}

      {albumId && albumTitle ? (
        <div
          className="form-info"
          style={{ marginBottom: '1rem', padding: '0.75rem', background: '#2a2a2a', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}
        >
          <div><strong>Album:</strong> {albumTitle}</div>
          <button
            type="button"
            className="btn-secondary discogs-button"
            onClick={handleDiscogsSearch}
            disabled={!getSelectedAlbumDiscogsId() || discogsLoading}
          >
            {discogsLoading ? 'Searching...' : 'Discogs'}
          </button>
        </div>
      ) : (
        <div className="form-group">
          <label htmlFor="album_id">
            Album <span className="required">*</span>
          </label>
          <div className="form-field-with-action">
            <select
              id="album_id"
              name="album_id"
              value={formData.album_id}
              onChange={handleChange}
              required
            >
              <option value="">Select an album...</option>
              {albums.map((album) => (
                <option key={album.id} value={album.id}>
                  {album.title} ({album.release_year ?? album.original_release_year ?? 'Unknown'})
                </option>
              ))}
            </select>
            <button
              type="button"
              className="btn-secondary discogs-button"
              onClick={() => setShowDiscogsModal(true)}
              disabled={!formData.album_id || !albumDiscogsId}
              title={!albumDiscogsId ? "Album must have a Discogs ID" : "Search Discogs releases"}
            >
              Search Releases
            </button>
          </div>
          <small>The album this pressing belongs to</small>
        </div>
      )}

      {discogsError && <div className="form-hint-error">{discogsError}</div>}
      {discogsResults.length > 0 && (
        <div className="discogs-results">
          <div className="discogs-results-header">Select Release</div>
          <div className="discogs-results-list">
            {discogsResults.map((result) => {
              const isSelected = discogsSelectedId === result.id;
              return (
                <button
                  key={`${result.type}-${result.id}`}
                  type="button"
                  className={`discogs-result ${isSelected ? 'is-selected' : ''}`}
                  disabled={discogsLoading}
                  onClick={() => handleDiscogsSelect(result)}
                >
                  <div className="discogs-result-thumb">
                    {result.thumb_url ? (
                      <img src={result.thumb_url} alt={`${result.title} artwork`} />
                    ) : (
                      <span className="discogs-result-placeholder">?</span>
                    )}
                  </div>
                  <div className="discogs-result-content">
                    <div className="discogs-result-name">
                      {result.title}
                      <span className="discogs-result-tag">
                        {result.type === 'master' ? 'MASTER' : 'RELEASE'}
                      </span>
                    </div>
                    <div className="discogs-result-meta">
                      {[result.year, result.country, result.label, result.format].filter(Boolean).join(' · ')}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
          <div className="discogs-results-footer">
            <button type="button" className="discogs-results-cancel" onClick={resetDiscogsState}>
              Clear results
            </button>
          </div>
        </div>
      )}

      {!isEditMode && discogsSelectedId && discogsResults.find((item) => item.id === discogsSelectedId)?.type === 'master' && (
        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={importMasterReleases}
              onChange={(e) => setImportMasterReleases(e.target.checked)}
              style={{ marginRight: '0.5rem' }}
            />
            Create all pressings under this master (queued)
          </label>
          <small>Child releases will be created in the background.</small>
        </div>
      )}

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="format">
            Format <span className="required">*</span>
          </label>
          <select
            id="format"
            name="format"
            value={formData.format}
            onChange={handleChange}
            required
          >
            {VINYL_FORMAT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="disc_count">
            Disc Count <span className="required">*</span>
          </label>
          <input
            type="number"
            id="disc_count"
            name="disc_count"
            value={formData.disc_count}
            onChange={handleChange}
            required
            min="1"
            max="10"
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="speed_rpm">
            Speed <span className="required">*</span>
          </label>
          <select
            id="speed_rpm"
            name="speed_rpm"
            value={formData.speed_rpm}
            onChange={handleChange}
            required
          >
            {speedOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="size_inches">
            Size <span className="required">*</span>
          </label>
          <select
            id="size_inches"
            name="size_inches"
            value={formData.size_inches}
            onChange={handleChange}
            required
          >
            {sizeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="country">Country</label>
          <select
            id="country"
            name="country"
            value={formData.country}
            onChange={handleChange}
          >
            <option value="">Select country...</option>
            {countries.map((country) => (
              <option key={country.code} value={country.code}>
                {country.name} ({country.code})
              </option>
            ))}
          </select>
          <small>Pressing country (ISO code)</small>
        </div>

        <div className="form-group">
          <label htmlFor="release_year">Release Year</label>
          <input
            type="number"
            id="release_year"
            name="release_year"
            value={formData.release_year}
            onChange={handleChange}
            placeholder="1969"
            min="1900"
            max="2100"
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="pressing_plant">Pressing Plant</label>
          <input
            type="text"
            id="pressing_plant"
            name="pressing_plant"
            value={formData.pressing_plant}
            onChange={handleChange}
            placeholder="EMI Hayes"
            maxLength={200}
          />
        </div>

        <div className="form-group">
          <label htmlFor="mastering_engineer">Mastering Engineer</label>
          <input
            type="text"
            id="mastering_engineer"
            name="mastering_engineer"
            value={formData.mastering_engineer}
            onChange={handleChange}
            placeholder="Bob Ludwig"
            maxLength={200}
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="mastering_studio">Mastering Studio</label>
          <input
            type="text"
            id="mastering_studio"
            name="mastering_studio"
            value={formData.mastering_studio}
            onChange={handleChange}
            placeholder="Abbey Road Studios"
            maxLength={200}
          />
        </div>

        <div className="form-group">
          <label htmlFor="vinyl_color">Vinyl Color</label>
          <input
            type="text"
            id="vinyl_color"
            name="vinyl_color"
            value={formData.vinyl_color}
            onChange={handleChange}
            placeholder="Black"
            maxLength={100}
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="label_design">Label Design</label>
          <input
            type="text"
            id="label_design"
            name="label_design"
            value={formData.label_design}
            onChange={handleChange}
            placeholder="Apple label"
            maxLength={200}
          />
        </div>

        <div className="form-group">
          <label htmlFor="edition_type">Edition Type</label>
          <select
            id="edition_type"
            name="edition_type"
            value={formData.edition_type}
            onChange={handleChange}
          >
            <option value="">Select edition type...</option>
            {editionTypes.map((option) => (
              <option key={option.code} value={option.code}>
                {option.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="pressing_image_upload">Pressing Cover Image</label>
        <div className="image-upload">
          <div className="image-preview" aria-live="polite">
            {formData.image_url ? (
              <img src={formData.image_url} alt={`${albumTitle || 'Pressing'} preview`} />
            ) : (
              <span>No image selected</span>
            )}
          </div>
          <div className="image-actions">
            <input
              type="file"
              id="pressing_image_upload"
              name="pressing_image_upload"
              accept="image/*"
              onChange={handleImageChange}
            />
            {formData.image_url && (
              <button
                type="button"
                className="btn-secondary btn-image-remove"
                onClick={handleImageRemove}
                disabled={loading}
              >
                Remove Image
              </button>
            )}
          </div>
        </div>
        <small>PNG or JPG recommended. Smaller images load faster.</small>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="sleeve_type">Sleeve Type</label>
          <select
            id="sleeve_type"
            name="sleeve_type"
            value={formData.sleeve_type}
            onChange={handleChange}
          >
            <option value="">Select sleeve type...</option>
            {sleeveTypes.map((option) => (
              <option key={option.code} value={option.code}>
                {option.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="barcode">Barcode and Other Identifiers</label>
          <textarea
            id="barcode"
            name="barcode"
            value={formData.barcode}
            onChange={handleChange}
            placeholder={"Barcode: 5099969945526\nMatrix / Runout (A): YEX 749-1\nMatrix / Runout (B): YEX 750-1\nCatalog Number: PCS 7088"}
            maxLength={2000}
          />
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="notes">Notes</label>
        <textarea
          id="notes"
          name="notes"
          value={formData.notes}
          onChange={handleChange}
          placeholder="Original UK pressing with 'Her Majesty' runout"
        />
      </div>

      {/* Add to Collection section (only shown when showAddToCollection is true) */}
      {showAddToCollection && !isEditMode && (
        <>
          <div className="form-group" style={{ marginTop: '1.5rem', borderTop: '1px solid #444', paddingTop: '1.5rem' }}>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={addToCollection}
                onChange={(e) => setAddToCollection(e.target.checked)}
                style={{ marginRight: '0.5rem' }}
              />
              Add to my collection
            </label>
          </div>

          {/* Collection fields (shown when checkbox is checked) */}
          {addToCollection && (
            <>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="media_condition">
                    Media Condition <span className="required">*</span>
                  </label>
                  <select
                    id="media_condition"
                    name="media_condition"
                    value={formData.media_condition}
                    onChange={handleChange}
                    required={addToCollection}
                  >
                    {CONDITION_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="sleeve_condition">
                    Sleeve Condition <span className="required">*</span>
                  </label>
                  <select
                    id="sleeve_condition"
                    name="sleeve_condition"
                    value={formData.sleeve_condition}
                    onChange={handleChange}
                    required={addToCollection}
                  >
                    {CONDITION_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="purchase_price">Purchase Price</label>
                  <input
                    type="number"
                    id="purchase_price"
                    name="purchase_price"
                    value={formData.purchase_price}
                    onChange={handleChange}
                    placeholder="25.99"
                    min="0"
                    step="0.01"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="purchase_currency">Currency</label>
                  <input
                    type="text"
                    id="purchase_currency"
                    name="purchase_currency"
                    value={formData.purchase_currency}
                    placeholder="USD"
                    maxLength={3}
                    readOnly
                    aria-readonly="true"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="purchase_date">Purchase Date</label>
                  <input
                    type="date"
                    id="purchase_date"
                    name="purchase_date"
                    value={formData.purchase_date}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="location">Storage Location</label>
                <input
                  type="text"
                  id="location"
                  name="location"
                  value={formData.location}
                  onChange={handleChange}
                  placeholder="Shelf A3"
                  maxLength={200}
                />
              </div>
            </>
          )}
        </>
      )}

      <div className="form-actions">
        <button
          type="button"
          onClick={onCancel}
          className="btn-secondary"
          disabled={loading}
        >
          Cancel
        </button>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading
            ? (isEditMode ? 'Updating...' : 'Creating...')
            : (isEditMode ? 'Update Pressing' : (addToCollection && showAddToCollection ? 'Create Pressing & Add to Collection' : 'Create Pressing'))}
        </button>
      </div>
    </form>

    {/* Discogs Release Search Modal */}
    <DiscogsReleaseSearchModal
      albumId={formData.album_id}
      isOpen={showDiscogsModal}
      onClose={() => setShowDiscogsModal(false)}
      onSelectRelease={applyDiscogsRelease}
    />
    </>
  );
}
