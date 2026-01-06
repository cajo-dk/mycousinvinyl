/**
 * Advanced filters for artist search.
 */

import { useState, useEffect, type ReactNode } from 'react';
import { lookupApi } from '@/api/services';
import { CountryResponse, ArtistTypeResponse } from '@/types/api';
import './AlbumFilters.css';

export interface ArtistFilterValues {
  query?: string;
  artistType?: string;
  country?: string;
}

interface ArtistFiltersProps {
  filters: ArtistFilterValues;
  onFilterChange: (filters: ArtistFilterValues) => void;
  onSearch: () => void;
  afterSearch?: ReactNode;
}

export function ArtistFilters({ filters, onFilterChange, onSearch, afterSearch }: ArtistFiltersProps) {
  const [countries, setCountries] = useState<CountryResponse[]>([]);
  const [artistTypes, setArtistTypes] = useState<ArtistTypeResponse[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    loadFilters();
  }, []);

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

  const handleQueryChange = (query: string) => {
    onFilterChange({ ...filters, query });
  };

  const handleReset = () => {
    onFilterChange({});
    onSearch();
  };

  return (
    <div className="album-filters">
      <div className="search-bar">
        <input
          type="text"
          placeholder="Search artists by name..."
          value={filters.query || ''}
          onChange={(e) => handleQueryChange(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && onSearch()}
          className="search-input"
        />
        <button onClick={onSearch} className="search-button">
          Search
        </button>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="toggle-filters-button"
        >
          {showAdvanced ? 'Hide' : 'Show'} Filters
        </button>
      </div>
      {afterSearch}

      {showAdvanced && (
        <div className="advanced-filters">
          <div className="filter-section">
            <label>Artist Type</label>
            <select
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

          <div className="filter-section">
            <label>Country</label>
            <select
              value={filters.country || ''}
              onChange={(e) => onFilterChange({ ...filters, country: e.target.value || undefined })}
            >
              <option value="">All Countries</option>
              {countries.map(country => (
                <option key={country.code} value={country.code}>
                  {country.name}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-actions">
            <button onClick={onSearch} className="apply-filters-button">
              Apply Filters
            </button>
            <button onClick={handleReset} className="reset-filters-button">
              Reset All
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
