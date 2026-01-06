/**
 * Album filters panel content for the nav dropdown.
 */

import { useEffect, useState } from 'react';
import { lookupApi } from '@/api/services';
import { GenreResponse, StyleResponse, ReleaseTypeResponse } from '@/types/api';

export interface AlbumFilterValues {
  releaseType?: string;
  yearMin?: number;
  yearMax?: number;
  genreIds?: string[];
  styleIds?: string[];
}

interface AlbumFiltersPanelProps {
  filters: AlbumFilterValues;
  onFilterChange: (filters: AlbumFilterValues) => void;
  onApply: () => void;
  onReset: () => void;
}

export function AlbumFiltersPanel({
  filters,
  onFilterChange,
  onApply,
  onReset,
}: AlbumFiltersPanelProps) {
  const [genres, setGenres] = useState<GenreResponse[]>([]);
  const [styles, setStyles] = useState<StyleResponse[]>([]);
  const [releaseTypes, setReleaseTypes] = useState<ReleaseTypeResponse[]>([]);

  useEffect(() => {
    const loadFilters = async () => {
      try {
        const [genresData, stylesData, releaseTypesData] = await Promise.all([
          lookupApi.getAllGenres(),
          lookupApi.getAllStyles(),
          lookupApi.getAllReleaseTypes(),
        ]);
        setGenres(genresData);
        setStyles(stylesData);
        setReleaseTypes(releaseTypesData);
      } catch (err) {
        console.error('Failed to load album filters:', err);
      }
    };

    loadFilters();
  }, []);

  const handleYearChange = (value: string, key: 'yearMin' | 'yearMax') => {
    const parsed = Number(value);
    const nextValue = Number.isFinite(parsed) ? parsed : undefined;
    onFilterChange({ ...filters, [key]: value === '' ? undefined : nextValue });
  };

  const toggleSelection = (value: string, key: 'genreIds' | 'styleIds') => {
    const current = filters[key] || [];
    const next = current.includes(value)
      ? current.filter((id) => id !== value)
      : [...current, value];
    onFilterChange({ ...filters, [key]: next.length ? next : undefined });
  };

  return (
    <>
      <div className="nav-filter-section">
        <label htmlFor="album-year-min">Year</label>
        <input
          id="album-year-min"
          type="number"
          placeholder="From"
          aria-label="Year from"
          value={filters.yearMin ?? ''}
          min={1900}
          max={2100}
          onChange={(e) => handleYearChange(e.target.value, 'yearMin')}
        />
        <input
          id="album-year-max"
          type="number"
          placeholder="To"
          aria-label="Year to"
          value={filters.yearMax ?? ''}
          min={1900}
          max={2100}
          onChange={(e) => handleYearChange(e.target.value, 'yearMax')}
        />
      </div>

      <div className="nav-filter-section">
        <label htmlFor="album-release-type">Type</label>
        <select
          id="album-release-type"
          value={filters.releaseType || ''}
          onChange={(e) => onFilterChange({ ...filters, releaseType: e.target.value || undefined })}
        >
          <option value="">All Types</option>
          {releaseTypes.map((type) => (
            <option key={type.code} value={type.code}>
              {type.name}
            </option>
          ))}
        </select>
      </div>

      <div className="nav-filter-section">
        <label>Genre</label>
        <div className="nav-filter-tags">
          {genres.map((genre) => {
            const active = (filters.genreIds || []).includes(genre.id);
            return (
              <button
                key={genre.id}
                type="button"
                className={`nav-filter-tag ${active ? 'active' : ''}`}
                onClick={() => toggleSelection(genre.id, 'genreIds')}
              >
                {genre.name}
              </button>
            );
          })}
        </div>
      </div>

      <div className="nav-filter-section">
        <label>Styles</label>
        <div className="nav-filter-tags">
          {styles.map((style) => {
            const active = (filters.styleIds || []).includes(style.id);
            return (
              <button
                key={style.id}
                type="button"
                className={`nav-filter-tag ${active ? 'active' : ''}`}
                onClick={() => toggleSelection(style.id, 'styleIds')}
              >
                {style.name}
              </button>
            );
          })}
        </div>
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
