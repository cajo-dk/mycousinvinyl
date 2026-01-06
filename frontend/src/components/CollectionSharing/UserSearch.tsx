/**
 * UserSearch component for searching and selecting users to follow.
 *
 * Features:
 * - Autocomplete search with debounced API calls (300ms)
 * - Dropdown showing user results with icon previews
 * - Filters out already-followed users
 * - Loading and error states
 */

import { useState, useEffect, useRef } from 'react';
import { Icon } from '@/components/UI';
import * as mdi from '@mdi/js';
import { collectionSharingApi } from '@/api/services';
import { UserOwnerInfo } from '@/types/api';
import './UserSearch.css';

interface UserSearchProps {
  onSelect: (user: UserOwnerInfo) => void;
  excludeUserIds: string[];
}

export function UserSearch({ onSelect, excludeUserIds }: UserSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<UserOwnerInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const searchRef = useRef<HTMLDivElement>(null);
  const debounceTimer = useRef<number | null>(null);

  /**
   * Close dropdown when clicking outside.
   */
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  /**
   * Debounced search with 300ms delay.
   */
  useEffect(() => {
    // Clear previous timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Don't search if query is too short
    if (query.trim().length < 2) {
      setResults([]);
      setIsOpen(false);
      setError(null);
      return;
    }

    // Set new timer
    debounceTimer.current = setTimeout(() => {
      performSearch(query.trim());
    }, 300);

    // Cleanup
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [query, excludeUserIds]);

  /**
   * Perform API search and filter results.
   */
  const performSearch = async (searchQuery: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await collectionSharingApi.searchUsers(searchQuery);

      // Filter out excluded users
      const filtered = response.users.filter(
        user => !excludeUserIds.includes(user.user_id)
      );

      setResults(filtered);
      setIsOpen(filtered.length > 0);
    } catch (err) {
      console.error('User search failed:', err);
      setError('Failed to search users. Please try again.');
      setResults([]);
      setIsOpen(false);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle user selection.
   */
  const handleSelect = (user: UserOwnerInfo) => {
    onSelect(user);
    setQuery('');
    setResults([]);
    setIsOpen(false);
    setError(null);
  };

  /**
   * Get MDI icon path from icon type name.
   */
  const getIconPath = (iconType: string): string => {
    return (mdi as any)[iconType] || mdi.mdiAccount;
  };

  return (
    <div className="user-search" ref={searchRef}>
      <div className="user-search-input-wrapper">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search users by name..."
          className="user-search-input"
          aria-label="Search users"
        />
        {isLoading && (
          <div className="user-search-spinner" aria-label="Loading">
            ⏳
          </div>
        )}
      </div>

      {error && (
        <div className="user-search-error" role="alert">
          {error}
        </div>
      )}

      {isOpen && results.length > 0 && (
        <div className="user-search-dropdown">
          {results.map((user) => (
            <button
              key={user.user_id}
              onClick={() => handleSelect(user)}
              className="user-search-result"
              type="button"
            >
              <div
                className="user-search-icon"
                style={{ backgroundColor: user.icon_bg_color }}
              >
                <Icon
                  path={getIconPath(user.icon_type)}
                  size={1}
                  color={user.icon_fg_color}
                />
              </div>
              <div className="user-search-info">
                <span className="user-search-name">{user.display_name}</span>
                <span className="user-search-first-name">@{user.first_name}</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {isOpen && results.length === 0 && !isLoading && query.trim().length >= 2 && (
        <div className="user-search-dropdown user-search-no-results">
          No users found matching "{query}"
        </div>
      )}
    </div>
  );
}
