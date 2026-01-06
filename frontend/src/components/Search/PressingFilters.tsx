/**
 * Advanced filters for pressing search.
 */

import { useState, useEffect } from 'react';
import { lookupApi } from '@/api/services';
import { CountryResponse, VinylFormat, VinylSpeed, VinylSize } from '@/types/api';
import './AlbumFilters.css';

export interface PressingFilterValues {
  format?: string;
  speed?: string;
  size?: string;
  country?: string;
  yearMin?: number;
  yearMax?: number;
}

interface PressingFiltersProps {
  filters: PressingFilterValues;
  onFilterChange: (filters: PressingFilterValues) => void;
  onSearch: () => void;
}

const FORMATS = [
  { value: '', label: 'All Formats' },
  { value: VinylFormat.LP, label: 'LP' },
  { value: VinylFormat.EP, label: 'EP' },
  { value: VinylFormat.SINGLE, label: 'Single' },
  { value: VinylFormat.MAXI, label: 'Maxi Single' },
];

const SPEEDS = [
  { value: '', label: 'All Speeds' },
  { value: VinylSpeed.RPM_33, label: '33 1/3 RPM' },
  { value: VinylSpeed.RPM_45, label: '45 RPM' },
  { value: VinylSpeed.RPM_78, label: '78 RPM' },
];

const SIZES = [
  { value: '', label: 'All Sizes' },
  { value: VinylSize.SIZE_7, label: '7"' },
  { value: VinylSize.SIZE_10, label: '10"' },
  { value: VinylSize.SIZE_12, label: '12"' },
];

export function PressingFilters({ filters, onFilterChange, onSearch }: PressingFiltersProps) {
  const [countries, setCountries] = useState<CountryResponse[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    loadCountries();
  }, []);

  const loadCountries = async () => {
    try {
      const data = await lookupApi.getAllCountries();
      setCountries(data);
    } catch (err) {
      console.error('Failed to load countries:', err);
    }
  };

  const handleReset = () => {
    onFilterChange({});
    onSearch();
  };

  return (
    <div className="album-filters">
      <div className="search-bar">
        <button onClick={onSearch} className="search-button">
          Refresh
        </button>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="toggle-filters-button"
        >
          {showAdvanced ? 'Hide' : 'Show'} Filters
        </button>
      </div>

      {showAdvanced && (
        <div className="advanced-filters">
          <div className="filter-section">
            <label>Format</label>
            <select
              value={filters.format || ''}
              onChange={(e) => onFilterChange({ ...filters, format: e.target.value || undefined })}
            >
              {FORMATS.map(format => (
                <option key={format.value} value={format.value}>
                  {format.label}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-section">
            <label>Speed</label>
            <select
              value={filters.speed || ''}
              onChange={(e) => onFilterChange({ ...filters, speed: e.target.value || undefined })}
            >
              {SPEEDS.map(speed => (
                <option key={speed.value} value={speed.value}>
                  {speed.label}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-section">
            <label>Size</label>
            <select
              value={filters.size || ''}
              onChange={(e) => onFilterChange({ ...filters, size: e.target.value || undefined })}
            >
              {SIZES.map(size => (
                <option key={size.value} value={size.value}>
                  {size.label}
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

          <div className="filter-section">
            <label>Year Range</label>
            <div className="year-range">
              <input
                type="number"
                placeholder="From"
                value={filters.yearMin || ''}
                onChange={(e) => onFilterChange({ ...filters, yearMin: e.target.value ? parseInt(e.target.value) : undefined })}
                min="1900"
                max="2100"
              />
              <span>to</span>
              <input
                type="number"
                placeholder="To"
                value={filters.yearMax || ''}
                onChange={(e) => onFilterChange({ ...filters, yearMax: e.target.value ? parseInt(e.target.value) : undefined })}
                min="1900"
                max="2100"
              />
            </div>
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
