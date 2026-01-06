/**
 * Global search component - search across artists, albums, and pressings.
 */

import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { artistsApi, albumsApi, pressingsApi } from '@/api/services';
import { ArtistResponse, AlbumResponse, PressingResponse } from '@/types/api';
import './GlobalSearch.css';

interface SearchResults {
  artists: ArtistResponse[];
  albums: AlbumResponse[];
  pressings: PressingResponse[];
}

export function GlobalSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResults>({
    artists: [],
    albums: [],
    pressings: [],
  });
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (query.length < 2) {
      setResults({ artists: [], albums: [], pressings: [] });
      setShowResults(false);
      return;
    }

    const searchTimeout = setTimeout(async () => {
      setLoading(true);
      try {
        const [artistsRes, albumsRes, pressingsRes] = await Promise.all([
          artistsApi.search({ query, limit: 5 }),
          albumsApi.search({ query, limit: 5 }),
          pressingsApi.search({ limit: 5 }),
        ]);

        setResults({
          artists: artistsRes.items,
          albums: albumsRes.items,
          pressings: pressingsRes.items,
        });
        setShowResults(true);
      } catch (err) {
        console.error('Search failed:', err);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(searchTimeout);
  }, [query]);

  const handleViewAll = (type: 'artists' | 'albums' | 'pressings') => {
    navigate(`/${type}`, { state: { searchQuery: query } });
    setShowResults(false);
    setQuery('');
  };

  const totalResults = results.artists.length + results.albums.length + results.pressings.length;

  return (
    <div className="global-search" ref={searchRef}>
      <input
        type="text"
        placeholder="Search artists, albums, pressings..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => query.length >= 2 && setShowResults(true)}
        className="global-search-input"
      />

      {showResults && (
        <div className="global-search-results">
          {loading && (
            <div className="search-loading">Searching...</div>
          )}

          {!loading && totalResults === 0 && (
            <div className="no-search-results">
              No results found for "{query}"
            </div>
          )}

          {!loading && results.artists.length > 0 && (
            <div className="search-section">
              <div className="search-section-header">
                <h4>Artists</h4>
                <button onClick={() => handleViewAll('artists')} className="view-all-link">
                  View all
                </button>
              </div>
              <div className="search-items">
                {results.artists.map((artist) => (
                  <div
                    key={artist.id}
                    className="search-item"
                    onClick={() => {
                      navigate(`/artists/${artist.id}`);
                      setShowResults(false);
                      setQuery('');
                    }}
                  >
                    <div className="search-item-title">{artist.name}</div>
                    <div className="search-item-meta">{artist.artist_type}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!loading && results.albums.length > 0 && (
            <div className="search-section">
              <div className="search-section-header">
                <h4>Albums</h4>
                <button onClick={() => handleViewAll('albums')} className="view-all-link">
                  View all
                </button>
              </div>
              <div className="search-items">
                {results.albums.map((album) => (
                  <div
                    key={album.id}
                    className="search-item"
                    onClick={() => {
                      navigate(`/albums/${album.id}`);
                      setShowResults(false);
                      setQuery('');
                    }}
                  >
                    <div className="search-item-title">{album.title}</div>
                    <div className="search-item-meta">
                      {album.release_type} {album.release_year && `• ${album.release_year}`}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!loading && results.pressings.length > 0 && (
            <div className="search-section">
              <div className="search-section-header">
                <h4>Pressings</h4>
                <button onClick={() => handleViewAll('pressings')} className="view-all-link">
                  View all
                </button>
              </div>
              <div className="search-items">
                {results.pressings.map((pressing) => (
                  <div
                    key={pressing.id}
                    className="search-item"
                    onClick={() => {
                      navigate(`/pressings/${pressing.id}`);
                      setShowResults(false);
                      setQuery('');
                    }}
                  >
                    <div className="search-item-title">
                      {pressing.format} - {pressing.size_inches} / {pressing.speed_rpm} RPM
                    </div>
                    <div className="search-item-meta">
                      {pressing.country} {pressing.release_year && `• ${pressing.release_year}`}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
