/**
 * Advanced filters for album search.
 */

import { useState, useEffect } from 'react';
import { lookupApi } from '@/api/services';
import { GenreResponse, StyleResponse } from '@/types/api';
import './AlbumFilters.css';

export interface AlbumFilterValues {
  query?: string;
  artistId?: string;
  genreIds?: string[];
  styleIds?: string[];
  releaseType?: string;
  yearMin?: number;
  yearMax?: number;
  sortBy?: string;
}

interface AlbumFiltersProps {
  filters: AlbumFilterValues;
  onFilterChange: (filters: AlbumFilterValues) => void;
  onSearch: () => void;
}

const RELEASE_TYPES = [
  { value: '', label: 'All Types' },
  { value: 'STUDIO', label: 'Studio Album' },
  { value: 'LIVE', label: 'Live Album' },
  { value: 'COMPILATION', label: 'Compilation' },
  { value: 'EP', label: 'EP' },
  { value: 'SINGLE', label: 'Single' },
  { value: 'SOUNDTRACK', label: 'Soundtrack' },
  { value: 'REMIX', label: 'Remix' },
  { value: 'BOOTLEG', label: 'Bootleg' },
];

const SORT_OPTIONS = [
  { value: 'relevance', label: 'Relevance' },
  { value: 'title', label: 'Title (A-Z)' },
  { value: 'year_desc', label: 'Year (Newest)' },
  { value: 'year_asc', label: 'Year (Oldest)' },
];

export function AlbumFilters({ filters, onFilterChange, onSearch }: AlbumFiltersProps) {
  const [genres, setGenres] = useState<GenreResponse[]>([]);
  const [styles, setStyles] = useState<StyleResponse[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    loadGenres();
    loadStyles();
  }, []);

  const loadGenres = async () => {
    try {
      const data = await lookupApi.getAllGenres();
      setGenres(data);
    } catch (err) {
      console.error('Failed to load genres:', err);
    }
  };

  const loadStyles = async () => {
    try {
      const data = await lookupApi.getAllStyles();
      setStyles(data);
    } catch (err) {
      console.error('Failed to load styles:', err);
    }
  };

  const handleQueryChange = (query: string) => {
    onFilterChange({ ...filters, query });
  };

  const handleGenreToggle = (genreId: string) => {
    const currentGenres = filters.genreIds || [];
    const newGenres = currentGenres.includes(genreId)
      ? currentGenres.filter(id => id !== genreId)
      : [...currentGenres, genreId];
    onFilterChange({ ...filters, genreIds: newGenres.length > 0 ? newGenres : undefined });
  };

  const handleStyleToggle = (styleId: string) => {
    const currentStyles = filters.styleIds || [];
    const newStyles = currentStyles.includes(styleId)
      ? currentStyles.filter(id => id !== styleId)
      : [...currentStyles, styleId];
    onFilterChange({ ...filters, styleIds: newStyles.length > 0 ? newStyles : undefined });
  };

  const handleReset = () => {
    onFilterChange({ sortBy: 'relevance' });
    onSearch();
  };

  return (
    <div className="album-filters">
      <div className="search-bar">
        <input
          type="text"
          placeholder="Search albums by title..."
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

      {showAdvanced && (
        <div className="advanced-filters">
          <div className="filter-section">
            <label>Release Type</label>
            <select
              value={filters.releaseType || ''}
              onChange={(e) => onFilterChange({ ...filters, releaseType: e.target.value || undefined })}
            >
              {RELEASE_TYPES.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
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

          <div className="filter-section">
            <label>Sort By</label>
            <select
              value={filters.sortBy || 'relevance'}
              onChange={(e) => onFilterChange({ ...filters, sortBy: e.target.value })}
            >
              {SORT_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {genres.length > 0 && (
            <div className="filter-section">
              <label>Genres</label>
              <div className="filter-tags">
                {genres.map(genre => (
                  <button
                    key={genre.id}
                    onClick={() => handleGenreToggle(genre.id)}
                    className={`filter-tag ${(filters.genreIds || []).includes(genre.id) ? 'active' : ''}`}
                  >
                    {genre.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {styles.length > 0 && (
            <div className="filter-section">
              <label>Styles</label>
              <div className="filter-tags">
                {styles.slice(0, 20).map(style => (
                  <button
                    key={style.id}
                    onClick={() => handleStyleToggle(style.id)}
                    className={`filter-tag ${(filters.styleIds || []).includes(style.id) ? 'active' : ''}`}
                  >
                    {style.name}
                  </button>
                ))}
              </div>
            </div>
          )}

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
