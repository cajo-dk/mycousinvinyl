/**
 * Artist creation/edit form
 */

import { useState, useEffect, FormEvent } from 'react';
import { artistsApi, lookupApi, discogsApi } from '@/api/services';
import { CountryResponse, ArtistTypeResponse, DiscogsArtistSearchResult } from '@/types/api';
import { Icon } from '@/components/UI';
import { mdiMagnify } from '@mdi/js';
import './Form.css';

interface ArtistFormProps {
  artistId?: string;
  onSuccess: () => void;
  onCancel: () => void;
}

export function ArtistForm({ artistId, onSuccess, onCancel }: ArtistFormProps) {
  const [formData, setFormData] = useState({
    name: '',
    sort_name: '',
    artist_type: 'Person',
    country: '',
    disambiguation: '',
    bio: '',
    image_url: '',
    begin_date: '',
    end_date: '',
    discogs_id: null as number | null,
  });
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(!!artistId);
  const [error, setError] = useState<string | null>(null);
  const [countries, setCountries] = useState<CountryResponse[]>([]);
  const [artistTypes, setArtistTypes] = useState<ArtistTypeResponse[]>([]);
  const isEditMode = !!artistId;
  const [imageTouched, setImageTouched] = useState(false);
  const [beginDateTouched, setBeginDateTouched] = useState(false);
  const [endDateTouched, setEndDateTouched] = useState(false);
  const [discogsResults, setDiscogsResults] = useState<DiscogsArtistSearchResult[]>([]);
  const [discogsLoading, setDiscogsLoading] = useState(false);
  const [discogsError, setDiscogsError] = useState<string | null>(null);
  const [discogsSelectedId, setDiscogsSelectedId] = useState<number | null>(null);

  // Load countries and artist data on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load countries and artist types
        const [countriesResp, artistTypesResp] = await Promise.all([
          lookupApi.getAllCountries(),
          lookupApi.getAllArtistTypes(),
        ]);
        setCountries(countriesResp);
        setArtistTypes(artistTypesResp);

        // Load existing artist if in edit mode
        if (artistId) {
          const artist = await artistsApi.getById(artistId);
          setFormData({
            name: artist.name || '',
            sort_name: artist.sort_name || '',
            artist_type: artist.artist_type || artist.type || 'Person',
            country: artist.country || '',
            disambiguation: artist.disambiguation || '',
            bio: artist.bio || '',
            image_url: artist.image_url || '',
            begin_date: artist.begin_date || '',
            end_date: artist.end_date || '',
            discogs_id: artist.discogs_id ?? null,
          });
          setImageTouched(false);
          setBeginDateTouched(false);
          setEndDateTouched(false);
        }
        if (!artistId && artistTypesResp.length > 0) {
          setFormData((prev) => ({
            ...prev,
            artist_type: prev.artist_type || artistTypesResp[0].code,
          }));
        }
      } catch (err: any) {
        console.error('Failed to load data:', err);
        setError(err.response?.data?.detail || 'Failed to load artist data');
      } finally {
        setInitialLoading(false);
      }
    };
    loadData();
  }, [artistId]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Only send fields that have values
      const payload: any = {
        name: formData.name,
        artist_type: formData.artist_type,
      };

      if (formData.sort_name) payload.sort_name = formData.sort_name;
      if (formData.country) payload.country = formData.country;
      if (formData.disambiguation) payload.disambiguation = formData.disambiguation;
      if (formData.bio) payload.bio = formData.bio;
      if (imageTouched) {
        payload.image_url = formData.image_url ? formData.image_url : null;
      }
      if (formData.begin_date || beginDateTouched) {
        payload.begin_date = formData.begin_date ? formData.begin_date : null;
      }
      if (formData.end_date || endDateTouched) {
        payload.end_date = formData.end_date ? formData.end_date : null;
      }
      if (formData.discogs_id) payload.discogs_id = formData.discogs_id;

      if (isEditMode && artistId) {
        await artistsApi.update(artistId, payload);
      } else {
        await artistsApi.create(payload);
      }
      onSuccess();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((e: any) => e.msg).join(', '));
      } else {
        setError(detail || err.message || `Failed to ${isEditMode ? 'update' : 'create'} artist`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    if (e.target.name === 'name') {
      setDiscogsResults([]);
      setDiscogsError(null);
      setDiscogsSelectedId(null);
    }
    if (e.target.name === 'begin_date') {
      setBeginDateTouched(true);
    }
    if (e.target.name === 'end_date') {
      setEndDateTouched(true);
    }
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
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

  const handleDiscogsSearch = async () => {
    const query = formData.name.trim();
    if (query.length < 3) return;
    setDiscogsLoading(true);
    setDiscogsError(null);
    try {
      const response = await discogsApi.searchArtists(query, 3);
      setDiscogsResults(response.items);
    } catch (err: any) {
      setDiscogsError(err.response?.data?.detail || 'Failed to search Discogs');
    } finally {
      setDiscogsLoading(false);
    }
  };

  const handleDiscogsSelect = async (artistId: number) => {
    setDiscogsSelectedId(artistId);
    setDiscogsLoading(true);
    setDiscogsError(null);
    try {
      const details = await discogsApi.getArtist(artistId);
      const countryCode = resolveCountryCode(details.country);
      let resolvedType: string | null = null;
      if (details.artist_type) {
        const normalizedType = details.artist_type.trim();
        const existing = artistTypes.find(
          (type) =>
            type.code === normalizedType ||
            type.name.toLowerCase() === normalizedType.toLowerCase()
        );
        if (existing) {
          resolvedType = existing.code;
        } else {
          try {
            const created = await lookupApi.createArtistType({
              code: normalizedType,
              name: normalizedType,
            });
            setArtistTypes((prev) => [...prev, created]);
            resolvedType = created.code;
          } catch (typeError) {
            console.warn('Failed to create artist type from Discogs:', typeError);
          }
        }
      }
      setFormData((prev) => ({
        ...prev,
        name: details.name || prev.name,
        country: countryCode || prev.country,
        bio: details.bio || prev.bio,
        begin_date: details.begin_date || prev.begin_date,
        end_date: details.end_date || prev.end_date,
        sort_name: details.sort_name || prev.sort_name,
        image_url: details.image_url || prev.image_url,
        discogs_id: details.id || prev.discogs_id,
        artist_type: resolvedType || prev.artist_type,
      }));
      if (details.image_url) {
        setImageTouched(true);
      }
      setDiscogsResults([]);
    } catch (err: any) {
      setDiscogsError(err.response?.data?.detail || 'Failed to load Discogs artist');
    } finally {
      setDiscogsLoading(false);
    }
  };

  if (initialLoading) {
    return <div className="form-loading">Loading artist data...</div>;
  }

  return (
    <form onSubmit={handleSubmit} className="form">
      {error && (
        <div className="form-error">
          {error}
        </div>
      )}

      <div className="form-grid-2col">
        {/* Line 1, Column 1: Name + Discogs Search Button */}
        <div className="form-group">
          <label htmlFor="name">
            Name <span className="required">*</span>
          </label>
          <div className="form-field-with-action">
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              maxLength={500}
              placeholder="e.g., The Beatles"
            />
            <button
              type="button"
              className="btn-icon-blue"
              onClick={handleDiscogsSearch}
              disabled={formData.name.trim().length < 3 || discogsLoading}
              title={discogsLoading ? 'Searching...' : 'Search Discogs'}
              style={{
                minWidth: '40px',
                height: '40px',
                padding: '8px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: formData.name.trim().length < 3 || discogsLoading ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                opacity: formData.name.trim().length < 3 || discogsLoading ? 0.5 : 1,
              }}
            >
              <Icon path={mdiMagnify} size={24} />
            </button>
          </div>
          <small>Type at least 3 characters to enable Discogs search.</small>
          {discogsError && <div className="form-hint-error">{discogsError}</div>}
          {discogsResults.length > 0 && (
            <div className="discogs-results">
              <div className="discogs-results-header">Select</div>
              <div className="discogs-results-list">
                {discogsResults.map((result) => (
                  <button
                    key={result.id}
                    type="button"
                    className={`discogs-result ${discogsSelectedId === result.id ? 'is-selected' : ''}`}
                    onClick={() => handleDiscogsSelect(result.id)}
                    disabled={discogsLoading}
                  >
                    <div className="discogs-result-thumb">
                      {result.thumb_url ? (
                        <img src={result.thumb_url} alt={result.name} />
                      ) : (
                        <span className="discogs-result-placeholder">?</span>
                      )}
                    </div>
                    <div className="discogs-result-content">
                      <div className="discogs-result-name">{result.name}</div>
                      {result.uri && <div className="discogs-result-meta">{result.uri}</div>}
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

        {/* Line 1, Column 2: Sort Name */}
        <div className="form-group">
          <label htmlFor="sort_name">Sort Name</label>
          <input
            type="text"
            id="sort_name"
            name="sort_name"
            value={formData.sort_name}
            onChange={handleChange}
            maxLength={500}
            placeholder="e.g., Beatles, The"
          />
          <small>Used for alphabetical sorting</small>
        </div>

        {/* Line 2, Column 1: Type */}
        <div className="form-group">
          <label htmlFor="artist_type">
            Type <span className="required">*</span>
          </label>
          <select
            id="artist_type"
            name="artist_type"
            value={formData.artist_type}
            onChange={handleChange}
            required
          >
            <option value="">Select type...</option>
            {artistTypes.map((type) => (
              <option key={type.code} value={type.code}>
                {type.name}
              </option>
            ))}
          </select>
        </div>

        {/* Line 2, Column 2: Country */}
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
          <small>Country of origin</small>
        </div>

        {/* Line 3, Column 1: Begin Date */}
        <div className="form-group">
          <label htmlFor="begin_date">Begin Date</label>
          <input
            type="text"
            id="begin_date"
            name="begin_date"
            value={formData.begin_date}
            onChange={handleChange}
            placeholder="e.g., 1960 or 1960-08-12"
          />
          <small>Year or YYYY-MM-DD</small>
        </div>

        {/* Line 3, Column 2: End Date */}
        <div className="form-group">
          <label htmlFor="end_date">End Date</label>
          <input
            type="text"
            id="end_date"
            name="end_date"
            value={formData.end_date}
            onChange={handleChange}
            placeholder="e.g., 1970 or 1970-04-10"
          />
          <small>Year or YYYY-MM-DD</small>
        </div>

        {/* Line 4, Column 1: Disambiguation */}
        <div className="form-group">
          <label htmlFor="disambiguation">Disambiguation</label>
          <input
            type="text"
            id="disambiguation"
            name="disambiguation"
            value={formData.disambiguation}
            onChange={handleChange}
            maxLength={500}
            placeholder="e.g., British rock band"
          />
          <small>Helps distinguish between artists with the same name</small>
        </div>

        {/* Line 4, Column 2: Discogs Artist ID */}
        <div className="form-group">
          <label htmlFor="discogs_id">Discogs Artist ID</label>
          <input
            type="text"
            id="discogs_id"
            name="discogs_id"
            value={formData.discogs_id ?? ''}
            disabled
            placeholder="Select a Discogs artist"
          />
        </div>

        {/* Line 5: Biography (span both columns) */}
        <div className="form-group form-group-full">
          <label htmlFor="bio">Biography</label>
          <textarea
            id="bio"
            name="bio"
            value={formData.bio}
            onChange={handleChange}
            rows={4}
            placeholder="Brief biography or description"
          />
        </div>

        {/* Line 6: Artist Image (span both columns) */}
        <div className="form-group form-group-full">
          <label htmlFor="image_upload">Artist Image</label>
          <div className="image-upload">
            <div className="image-preview" aria-live="polite">
              {formData.image_url ? (
                <img src={formData.image_url} alt={`${formData.name || 'Artist'} preview`} />
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
        <button
          type="submit"
          className="btn-primary"
          disabled={loading}
        >
          {loading
            ? (isEditMode ? 'Updating...' : 'Creating...')
            : (isEditMode ? 'Update Artist' : 'Create Artist')}
        </button>
      </div>
    </form>
  );
}
