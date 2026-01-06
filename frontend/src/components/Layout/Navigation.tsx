/**
 * Main navigation component.
 */

import { Link, NavLink, useLocation } from 'react-router-dom';
import { useEffect, useRef, useState } from 'react';
import { useMsal } from '@azure/msal-react';
import { useIsAdmin } from '@/auth/useAdmin';
import { Icon } from '@/components/UI';
import { getEnv } from '@/config/runtimeEnv';
import {
  mdiAccountOutline,
  mdiCog,
  mdiMagnify,
  mdiFilterVariant,
  mdiMenu,
  mdiRecordCircleOutline,
  mdiAccountMusicOutline,
  mdiAlbum,
  mdiRecordPlayer,
  mdiLogout,
  mdiMagicStaff,
  mdiClose,
} from '@mdi/js';
import { useViewControls } from './ViewControlsContext';
import './Navigation.css';

export function Navigation() {
  const { instance, accounts } = useMsal();
  const location = useLocation();
  const { isAdmin, isLoading } = useIsAdmin();
  const { controls, showFilters, setShowFilters } = useViewControls();
  const searchRef = useRef<HTMLDivElement>(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isOtherOpen, setIsOtherOpen] = useState(false);
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
  const debugNav = getEnv('VITE_DEBUG_NAV') === 'true';
  const claimGroups = (accounts[0]?.idTokenClaims as { groups?: string[] } | undefined)?.groups;

  const handleLogout = () => {
    instance.logoutPopup();
  };

  const isActive = (path: string) => location.pathname === path;

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowFilters(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [setShowFilters]);

  useEffect(() => {
    setIsMenuOpen(false);
    setIsOtherOpen(false);
    setIsSearchModalOpen(false);
    setShowFilters(false);
  }, [location.pathname]);

  const handleSearchSubmit = () => {
    if (!controls) return;
    controls.onSearchSubmit();
  };

  const primaryNavItems = [
    { to: '/collection', label: 'My Collection', icon: mdiRecordCircleOutline },
    { to: '/artists', label: 'Artists', icon: mdiAccountMusicOutline },
    { to: '/albums', label: 'Albums', icon: mdiAlbum },
    { to: '/pressings', label: 'Pressings', icon: mdiRecordPlayer },
    { to: '/album-wizard', label: 'Album Wizard', icon: mdiMagicStaff },
  ];
  const navTitles = new Map<string, string>([
    ['/', 'Home'],
    ['/collection', 'Collection'],
    ['/artists', 'Artists'],
    ['/albums', 'Albums'],
    ['/pressings', 'Pressings'],
    ['/album-wizard', 'Album Wizard'],
    ['/profile', 'Profile'],
    ['/settings', 'Settings'],
  ]);
  const currentTitle = navTitles.get(location.pathname) ?? 'MyCousinVinyl';

  const closeSearchModal = () => {
    setIsSearchModalOpen(false);
    setShowFilters(false);
  };

  return (
    <nav className="navigation">
      <div className="nav-container">
        <div className="nav-left">
          <div className="nav-brand">
            <Link to="/">
              <h1>
                <span className="nav-brand-full">MyCousinVinyl</span>
                <span className="nav-brand-short">MyCousinVinyl</span>
              </h1>
            </Link>
            <div className="nav-page-title">{currentTitle}</div>
          </div>
          <div className="nav-primary" aria-label="Primary">
            {primaryNavItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `nav-primary-link ${isActive ? 'active' : ''}`}
              >
                <Icon path={item.icon} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        </div>

        {controls && (
          <div className="nav-center">
            <div className="nav-search" ref={searchRef}>
              <input
                type="text"
                className="nav-search-input"
                placeholder={controls.searchPlaceholder}
                value={controls.searchValue}
                onChange={(e) => controls.onSearchChange(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleSearchSubmit();
                  }
                }}
              />
              <div className="nav-search-actions">
                <button
                  type="button"
                  className="nav-search-button"
                  onClick={handleSearchSubmit}
                  aria-label="Search"
                >
                  <Icon path={mdiMagnify} />
                </button>
                <button
                  type="button"
                  className="nav-filter-button"
                  onClick={() => setShowFilters(!showFilters)}
                  aria-label="Filters"
                  aria-pressed={showFilters}
                  disabled={!controls.filtersContent}
                >
                  <Icon path={mdiFilterVariant} />
                </button>
              </div>
              {showFilters && controls.filtersContent && (
                <div className="nav-filter-panel">
                  <div className="nav-filter-panel-header">Filters</div>
                  <div className="nav-filter-panel-body">
                    {controls.filtersContent}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="nav-right">
          <button
            type="button"
            className="nav-search-trigger"
            onClick={() => setIsSearchModalOpen(true)}
            aria-label="Search and filters"
          >
            <Icon path={mdiMagnify} />
          </button>
          <button
            type="button"
            className="nav-hamburger"
            onClick={() => setIsMenuOpen((prev) => !prev)}
            aria-label="Toggle menu"
            aria-expanded={isMenuOpen}
          >
            <Icon path={mdiMenu} />
          </button>

          <div className="nav-user">
            {debugNav && (
              <span className="nav-debug">
                admin={String(isAdmin)} loading={String(isLoading)} account={String(!!accounts[0])}
                groups={claimGroups?.length ?? 0}
              </span>
            )}
            {accounts[0] && (
              <>
                <Link to="/profile" className="nav-icon-button" title="Profile" aria-label="Profile">
                  <Icon path={mdiAccountOutline} />
                </Link>
                {isAdmin && (
                  <Link
                    to="/settings"
                    className="nav-icon-button"
                    title="System Settings"
                    aria-label="System Settings"
                  >
                    <Icon path={mdiCog} />
                  </Link>
                )}
                <button
                  onClick={handleLogout}
                  className="nav-icon-button"
                  title="Sign Out"
                  aria-label="Sign Out"
                  type="button"
                >
                  <Icon path={mdiLogout} />
                </button>
              </>
            )}
          </div>
        </div>
      </div>

        <div className={`nav-links ${isMenuOpen ? 'open' : ''}`}>
          {primaryNavItems.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={isActive(item.to) ? 'active' : ''}
              onClick={() => setIsMenuOpen(false)}
            >
              <Icon path={item.icon} />
              <span>{item.label}</span>
            </Link>
          ))}
          {accounts[0] && (
            <div className="nav-other">
              <button
                type="button"
                className="nav-other-toggle"
                onClick={() => setIsOtherOpen((prev) => !prev)}
                aria-expanded={isOtherOpen}
              >
                Other <span aria-hidden="true">&gt;</span>
              </button>
              <div className={`nav-other-menu ${isOtherOpen ? 'open' : ''}`}>
                <Link to="/profile" onClick={() => setIsMenuOpen(false)}>
                  <Icon path={mdiAccountOutline} />
                  Profile
                </Link>
                {isAdmin && (
                  <Link to="/settings" onClick={() => setIsMenuOpen(false)}>
                    <Icon path={mdiCog} />
                    Settings
                  </Link>
                )}
                <button type="button" onClick={handleLogout}>
                  <Icon path={mdiLogout} />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>

      {controls && (
        <div className={`nav-search-modal ${isSearchModalOpen ? 'open' : ''}`} role="dialog">
          <div className="nav-search-modal-backdrop" onClick={closeSearchModal} />
          <div className="nav-search-modal-content">
            <div className="nav-search-modal-header">
              <div className="nav-search-modal-title">Search &amp; Filters</div>
              <button type="button" className="nav-search-modal-close" onClick={closeSearchModal}>
                <Icon path={mdiClose} />
              </button>
            </div>
              <div className="nav-search-modal-body">
                <div className="nav-search-modal-input">
                  <input
                    type="text"
                    className="nav-search-input"
                    placeholder={controls.searchPlaceholder}
                    value={controls.searchValue}
                  onChange={(e) => controls.onSearchChange(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleSearchSubmit();
                    }
                  }}
                />
                  <div className="nav-search-actions">
                    <button
                      type="button"
                      className="nav-search-button"
                      onClick={handleSearchSubmit}
                      aria-label="Search"
                    >
                      <Icon path={mdiMagnify} />
                    </button>
                  </div>
                </div>
                {controls.filtersContent && (
                  <div className="nav-search-modal-filters">
                    <div className="nav-filter-panel-header">Filters</div>
                    <div className="nav-filter-panel-body">
                      {controls.filtersContent}
                    </div>
                  </div>
                )}
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
