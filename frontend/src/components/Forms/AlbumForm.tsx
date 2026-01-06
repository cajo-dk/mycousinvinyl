/**
 * Album creation form.
 */

import { useState, useEffect, FormEvent } from 'react';
import { albumsApi, artistsApi, lookupApi, discogsApi } from '@/api/services';
import {
  ArtistResponse,
  DiscogsAlbumSearchResult,
  GenreResponse,
  StyleResponse,
  CountryResponse,
  DataSource,
  ReleaseTypeResponse,
} from '@/types/api';
import './Form.css';

interface AlbumFormProps {
  albumId?: string;
  initialArtistId?: string;
  onSuccess: () => void;
  onCancel: () => void;
}

export function AlbumForm({ albumId, initialArtistId, onSuccess, onCancel }: AlbumFormProps) {
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(!!albumId);
  const [error, setError] = useState<string | null>(null);
  const [artists, setArtists] = useState<ArtistResponse[]>([]);
  const [genres, setGenres] = useState<GenreResponse[]>([]);
  const [styles, setStyles] = useState<StyleResponse[]>([]);
  const [countries, setCountries] = useState<CountryResponse[]>([]);
  const [releaseTypes, setReleaseTypes] = useState<ReleaseTypeResponse[]>([]);
  const isEditMode = !!albumId;
  const [imageTouched, setImageTouched] = useState(false);
  const formatApiError = (err: any, fallback: string) => {
    const detail = err?.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      const messages = detail
        .map((item) => (typeof item?.msg === 'string' ? item.msg : null))
        .filter(Boolean);
      if (messages.length > 0) {
        return messages.join('; ');
      }
    }
    if (typeof err?.message === 'string' && err.message.trim()) {
      return err.message;
    }
    return fallback;
  };

  const [formData, setFormData] = useState({
    title: '',
    artist_id: initialArtistId || '',
    release_type: '',
    release_year: '',
    country_of_origin: '',
    genre_ids: [] as string[],
    style_ids: [] as string[],
    label: '',
    catalog_number: '',
    notes: '',
    image_url: '',
    discogs_id: null as number | null,
  });
  const [discogsResults, setDiscogsResults] = useState<DiscogsAlbumSearchResult[]>([]);
  const [discogsLoading, setDiscogsLoading] = useState(false);
  const [discogsError, setDiscogsError] = useState<string | null>(null);
  const [discogsSelectedId, setDiscogsSelectedId] = useState<number | null>(null);

  // Load lookup data and album data on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        const [artistsResp, genresResp, stylesResp, countriesResp, releaseTypesResp] = await Promise.all([
          artistsApi.search({ limit: 1000 }),
          lookupApi.getAllGenres(),
          lookupApi.getAllStyles(),
          lookupApi.getAllCountries(),
          lookupApi.getAllReleaseTypes(),
        ]);
        setArtists(artistsResp.items);
        setGenres(genresResp);
        setStyles(stylesResp);
        setCountries(countriesResp);
        setReleaseTypes(releaseTypesResp);

        // Load existing album if in edit mode
        if (albumId) {
          const album = await albumsApi.getById(albumId);
          const genreIdsFromNested = Array.isArray(album.genres)
            ? album.genres
              .map((genre: any) => (typeof genre === 'string' ? null : genre?.id))
              .filter(Boolean)
            : [];
          const styleIdsFromNested = Array.isArray(album.styles)
            ? album.styles
              .map((style: any) => (typeof style === 'string' ? null : style?.id))
              .filter(Boolean)
            : [];
          const genreIds = genreIdsFromNested.length > 0 ? genreIdsFromNested : album.genre_ids ?? [];
          const styleIds = styleIdsFromNested.length > 0 ? styleIdsFromNested : album.style_ids ?? [];
          const releaseYear = album.release_year ?? album.original_release_year;
          setFormData({
            title: album.title || '',
            artist_id: album.artist_id || album.primary_artist_id || '',
            release_type: album.release_type || releaseTypesResp[0]?.code || '',
            release_year: releaseYear ? releaseYear.toString() : '',
            country_of_origin: album.country_of_origin || '',
            genre_ids: genreIds,
            style_ids: styleIds,
            label: album.label || '',
            catalog_number: album.catalog_number || album.catalog_number_base || '',
            notes: album.notes || album.description || '',
            image_url: album.image_url || '',
            discogs_id: album.discogs_id ?? null,
          });
          setImageTouched(false);
        }
        if (!albumId && releaseTypesResp.length > 0) {
          setFormData((prev) => ({
            ...prev,
            release_type: prev.release_type || releaseTypesResp[0].code,
          }));
        }
      } catch (err: any) {
        console.error('Failed to load data:', err);
        setError(formatApiError(err, 'Failed to load form data. Please try again.'));
      } finally {
        setInitialLoading(false);
      }
    };
    loadData();
  }, [albumId, initialArtistId]);

  useEffect(() => {
    if (!albumId && initialArtistId) {
      setFormData((prev) => ({
        ...prev,
        artist_id: initialArtistId,
      }));
    }
  }, [albumId, initialArtistId]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    if (name === 'title' || name === 'artist_id') {
      setDiscogsResults([]);
      setDiscogsError(null);
      setDiscogsSelectedId(null);
    }
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleMultiSelect = (e: React.ChangeEvent<HTMLSelectElement>, field: 'genre_ids' | 'style_ids') => {
    const options = e.target.selectedOptions;
    const values = Array.from(options).map(option => option.value);
    setFormData((prev) => ({ ...prev, [field]: values }));
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

  const resolveGenreIds = async (names: string[] | undefined) => {
    const result: string[] = [];
    for (const name of names ?? []) {
      const trimmed = name.trim();
      if (!trimmed) continue;
      const existing = genres.find((genre) => genre.name.toLowerCase() === trimmed.toLowerCase());
      if (existing) {
        result.push(existing.id);
        continue;
      }
      try {
        const created = await lookupApi.createGenre({ name: trimmed });
        setGenres((prev) => [...prev, created]);
        result.push(created.id);
      } catch (err) {
        console.warn('Failed to create genre from Discogs:', err);
      }
    }
    return result;
  };

  const resolveStyleIds = async (names: string[] | undefined) => {
    const result: string[] = [];
    for (const name of names ?? []) {
      const trimmed = name.trim();
      if (!trimmed) continue;
      const existing = styles.find((style) => style.name.toLowerCase() === trimmed.toLowerCase());
      if (existing) {
        result.push(existing.id);
        continue;
      }
      try {
        const created = await lookupApi.createStyle({ name: trimmed });
        setStyles((prev) => [...prev, created]);
        result.push(created.id);
      } catch (err) {
        console.warn('Failed to create style from Discogs:', err);
      }
    }
    return result;
  };

  const resolveReleaseType = async (value: string | undefined | null) => {
    if (!value) return null;
    const trimmed = value.trim();
    if (!trimmed) return null;
    const existing = releaseTypes.find(
      (type) =>
        type.code.toLowerCase() === trimmed.toLowerCase() ||
        type.name.toLowerCase() === trimmed.toLowerCase()
    );
    if (existing) {
      return existing.code;
    }
    try {
      const created = await lookupApi.createReleaseType({ code: trimmed, name: trimmed });
      setReleaseTypes((prev) => [...prev, created]);
      return created.code;
    } catch (err) {
      console.warn('Failed to create release type from Discogs:', err);
      return null;
    }
  };

  const getSelectedArtistDiscogsId = () => {
    const selected = artists.find((artist) => artist.id === formData.artist_id);
    return selected?.discogs_id ?? null;
  };

  const handleDiscogsSearch = async () => {
    const query = formData.title.trim();
    const artistDiscogsId = getSelectedArtistDiscogsId();
    if (!artistDiscogsId || query.length < 3) return;
    setDiscogsLoading(true);
    setDiscogsError(null);
    try {
      const response = await discogsApi.searchAlbums(artistDiscogsId, query, 3);
      setDiscogsResults(response.items);
    } catch (err: any) {
      setDiscogsError(err.response?.data?.detail || 'Failed to search Discogs');
    } finally {
      setDiscogsLoading(false);
    }
  };

  const handleDiscogsSelect = async (albumId: number, albumType?: string) => {
    setDiscogsSelectedId(albumId);
    setDiscogsLoading(true);
    setDiscogsError(null);
    try {
      const details = await discogsApi.getAlbum(albumId, albumType);
      const countryCode = resolveCountryCode(details.country);
      const genreIds = await resolveGenreIds(details.genres);
      const styleIds = await resolveStyleIds(details.styles);
      const resolvedReleaseType = await resolveReleaseType(details.type);
      setFormData((prev) => ({
        ...prev,
        title: details.title || prev.title,
        release_year: details.year ? String(details.year) : prev.release_year,
        country_of_origin: countryCode || prev.country_of_origin,
        label: details.label || prev.label,
        catalog_number: details.catalog_number || prev.catalog_number,
        image_url: details.image_url || prev.image_url,
        discogs_id: details.id || prev.discogs_id,
        genre_ids: genreIds.length ? genreIds : prev.genre_ids,
        style_ids: styleIds.length ? styleIds : prev.style_ids,
        release_type: resolvedReleaseType || prev.release_type,
      }));
      if (details.image_url) {
        setImageTouched(true);
      }
      setDiscogsResults([]);
    } catch (err: any) {
      setDiscogsError(err.response?.data?.detail || 'Failed to load Discogs album');
    } finally {
      setDiscogsLoading(false);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.title.trim()) {
      setError('Title is required');
      return;
    }
    if (!formData.artist_id) {
      setError('Artist is required');
      return;
    }

    setLoading(true);

    try {
      const payload: any = {
        title: formData.title,
        artist_id: formData.artist_id,
        release_type: formData.release_type,
        genre_ids: formData.genre_ids,
        style_ids: formData.style_ids,
        data_source: DataSource.USER,
      };

      // Add optional fields if provided
      if (formData.release_year) {
        const year = parseInt(formData.release_year);
        if (!isNaN(year)) {
          payload.release_year = year;
        }
      }
      if (formData.country_of_origin) payload.country_of_origin = formData.country_of_origin;
      if (formData.label) payload.label = formData.label;
      if (formData.catalog_number) payload.catalog_number = formData.catalog_number;
      if (formData.notes) payload.notes = formData.notes;
      if (formData.discogs_id) payload.discogs_id = formData.discogs_id;
      if (formData.image_url && (!isEditMode || imageTouched)) {
        payload.image_url = formData.image_url;
      } else if (isEditMode && imageTouched && !formData.image_url) {
        payload.image_url = null;
      }

      if (isEditMode && albumId) {
        await albumsApi.update(albumId, payload);
      } else {
        await albumsApi.create(payload);
      }
      onSuccess();
    } catch (err: any) {
      console.error(`Failed to ${isEditMode ? 'update' : 'create'} album:`, err);
      setError(
        formatApiError(
          err,
          `Failed to ${isEditMode ? 'update' : 'create'} album`
        )
      );
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) {
    return <div className="form-loading">Loading album data...</div>;
  }

  const artistDiscogsId = getSelectedArtistDiscogsId();

  return (
    <form className="form" onSubmit={handleSubmit}>
      {error && <div className="form-error">{error}</div>}

      <div className="form-group">
        <label htmlFor="title">
          Title <span className="required">*</span>
        </label>
        <div className="form-field-with-action">
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="Abbey Road"
            required
            maxLength={500}
          />
          <button
            type="button"
            className="btn-secondary discogs-button"
            onClick={handleDiscogsSearch}
            disabled={!artistDiscogsId || formData.title.trim().length < 3 || discogsLoading}
          >
            {discogsLoading ? 'Searching...' : 'Discogs'}
          </button>
        </div>
        <small>
          Select an artist with a Discogs ID and type at least 3 characters to enable Discogs search.
        </small>
        {discogsError && <div className="form-hint-error">{discogsError}</div>}
        {discogsResults.length > 0 && (
          <div className="discogs-results">
            <div className="discogs-results-header">Select</div>
            <div className="discogs-results-list">
              {discogsResults.map((result) => (
                <button
                  key={`${result.id}-${result.type ?? 'master'}`}
                  type="button"
                  className={`discogs-result ${discogsSelectedId === result.id ? 'is-selected' : ''}`}
                  onClick={() => handleDiscogsSelect(result.id, result.type)}
                  disabled={discogsLoading}
                >
                  <div className="discogs-result-thumb">
                    {result.thumb_url ? (
                      <img src={result.thumb_url} alt={result.title} />
                    ) : (
                      <span className="discogs-result-placeholder">?</span>
                    )}
                  </div>
                  <div className="discogs-result-content">
                    <div className="discogs-result-name">{result.title}</div>
                    <div className="discogs-result-meta">
                      {result.year ? result.year : 'Unknown year'}
                    </div>
                  </div>
                </button>
              ))}
            </div>
            <div className="discogs-results-footer">
              <button
                type="button"
                className="discogs-results-cancel"
                onClick={() => {
                  setDiscogsResults([]);
                  setDiscogsSelectedId(null);
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="artist_id">
          Artist <span className="required">*</span>
        </label>
        <select
          id="artist_id"
          name="artist_id"
          value={formData.artist_id}
          onChange={handleChange}
          required
        >
          <option value="">Select an artist...</option>
          {artists.map((artist) => (
            <option key={artist.id} value={artist.id}>
              {artist.name}
            </option>
          ))}
        </select>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="release_type">
            Release Type <span className="required">*</span>
          </label>
          <select
            id="release_type"
            name="release_type"
            value={formData.release_type}
            onChange={handleChange}
            required
          >
            <option value="">Select release type...</option>
            {releaseTypes.map((option) => (
              <option key={option.code} value={option.code}>
                {option.name}
              </option>
            ))}
          </select>
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

      <div className="form-group">
        <label htmlFor="country_of_origin">Country of Origin</label>
        <select
          id="country_of_origin"
          name="country_of_origin"
          value={formData.country_of_origin}
          onChange={handleChange}
        >
          <option value="">Select country...</option>
          {countries.map((country) => (
            <option key={country.code} value={country.code}>
              {country.name} ({country.code})
            </option>
          ))}
        </select>
        <small>Country where the album was originally released</small>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="genre_ids">Genres</label>
          <select
            id="genre_ids"
            name="genre_ids"
            multiple
            size={5}
            value={formData.genre_ids}
            onChange={(e) => handleMultiSelect(e, 'genre_ids')}
          >
            {genres.map((genre) => (
              <option key={genre.id} value={genre.id}>
                {genre.name}
              </option>
            ))}
          </select>
          <small>Hold Ctrl/Cmd to select multiple</small>
        </div>

        <div className="form-group">
          <label htmlFor="style_ids">Styles</label>
          <select
            id="style_ids"
            name="style_ids"
            multiple
            size={5}
            value={formData.style_ids}
            onChange={(e) => handleMultiSelect(e, 'style_ids')}
          >
            {styles.map((style) => (
              <option key={style.id} value={style.id}>
                {style.name}
              </option>
            ))}
          </select>
          <small>Hold Ctrl/Cmd to select multiple</small>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="label">Label</label>
          <input
            type="text"
            id="label"
            name="label"
            value={formData.label}
            onChange={handleChange}
            placeholder="Apple Records"
            maxLength={200}
          />
        </div>

        <div className="form-group">
          <label htmlFor="catalog_number">Catalog Number</label>
          <input
            type="text"
            id="catalog_number"
            name="catalog_number"
            value={formData.catalog_number}
            onChange={handleChange}
            placeholder="PCS 7088"
            maxLength={100}
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
          placeholder="Original UK pressing"
        />
      </div>

      <div className="form-group">
        <label htmlFor="image_upload">Album Image</label>
        <div className="image-upload">
          <div className="image-preview" aria-live="polite">
            {formData.image_url ? (
              <img src={formData.image_url} alt={`${formData.title || 'Album'} preview`} />
            ) : (
              <span>No image selected</span>
            )}
          </div>
          <div className="image-actions">
            <input
              type="file"
              id="image_upload"
              name="image_upload"
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

      <div className="form-group">
        <label htmlFor="discogs_id">Discogs Album ID</label>
        <input
          type="text"
          id="discogs_id"
          name="discogs_id"
          value={formData.discogs_id ?? ''}
          disabled
          placeholder="Select a Discogs album"
        />
      </div>

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
            : (isEditMode ? 'Update Album' : 'Create Album')}
        </button>
      </div>
    </form>
  );
}
