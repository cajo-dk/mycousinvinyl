/**
 * Artist filters panel content for the nav dropdown.
 */

import { useEffect, useState } from 'react';
import { lookupApi } from '@/api/services';
import { CountryResponse, ArtistTypeResponse } from '@/types/api';

export interface ArtistFilterValues {
  query?: string;
  artistType?: string;
  country?: string;
}

interface ArtistFiltersPanelProps {
  filters: ArtistFilterValues;
  onFilterChange: (filters: ArtistFilterValues) => void;
  onApply: () => void;
  onReset: () => void;
}

export function ArtistFiltersPanel({
  filters,
  onFilterChange,
  onApply,
  onReset,
}: ArtistFiltersPanelProps) {
  const [countries, setCountries] = useState<CountryResponse[]>([]);
  const [artistTypes, setArtistTypes] = useState<ArtistTypeResponse[]>([]);

  useEffect(() => {
    const loadFilters = async () => {
      try {
        const [countriesData, artistTypesData] = await Promise.all([
          lookupApi.getAllCountries(),
          lookupApi.getAllArtistTypes(),
        ]);
        setCountries(countriesData);
        setArtistTypes(artistTypesData);
      } catch (err) {
        console.error('Failed to load artist filters:', err);
      }
    };

    loadFilters();
  }, []);

  return (
    <>
      <div className="nav-filter-section">
        <label htmlFor="artist-type-filter">Artist Type</label>
        <select
          id="artist-type-filter"
          value={filters.artistType || ''}
          onChange={(e) => onFilterChange({ ...filters, artistType: e.target.value || undefined })}
        >
          <option value="">All Types</option>
          {artistTypes.map((type) => (
            <option key={type.code} value={type.code}>
              {type.name}
            </option>
          ))}
        </select>
      </div>

      <div className="nav-filter-section">
        <label htmlFor="artist-country-filter">Country</label>
        <select
          id="artist-country-filter"
          value={filters.country || ''}
          onChange={(e) => onFilterChange({ ...filters, country: e.target.value || undefined })}
        >
          <option value="">All Countries</option>
          {countries.map((country) => (
            <option key={country.code} value={country.code}>
              {country.name}
            </option>
          ))}
        </select>
      </div>

      <div className="nav-filter-actions">
        <button type="button" className="nav-filter-reset" onClick={onReset}>
          Reset
        </button>
        <button type="button" className="nav-filter-apply" onClick={onApply}>
          Apply
        </button>
      </div>
    </>
  );
}
