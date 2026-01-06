/**
 * Profile page for user preferences.
 */

import { useEffect, useState } from 'react';
import { useMsal } from '@azure/msal-react';
import { preferencesApi, collectionSharingApi, collectionApi, discogsApi } from '@/api/services';
import { Loading, ErrorAlert } from '@/components/UI';
import { ItemsPerPageView, resolveItemsPerPage } from '@/utils/preferences';
import { useViewControls } from '@/components/Layout/ViewControlsContext';
import { IconSelector, ColorPicker, UserSearch } from '@/components/CollectionSharing';
import { apiRequest } from '@/auth/authConfig';
import { getEnv } from '@/config/runtimeEnv';
import {
  CollectionImportResponse,
  CollectionSharingSettings,
  UserOwnerInfo,
  DiscogsOAuthStatusResponse,
} from '@/types/api';
import { Icon } from '@/components/UI';
import * as mdi from '@mdi/js';
import './Settings.css';

const ITEMS_PER_PAGE_OPTIONS = [10, 25, 50, 100];
const ITEMS_PER_PAGE_LABELS: Record<ItemsPerPageView, string> = {
  collection: 'My Collection',
  artists: 'Artists',
  albums: 'Albums',
  pressings: 'Pressings',
};

export function Profile() {
  const { accounts, instance } = useMsal();
  const [currency, setCurrency] = useState('');
  const [currencySaving, setCurrencySaving] = useState(false);
  const [itemsPerPageByView, setItemsPerPageByView] = useState<Record<ItemsPerPageView, number>>({
    collection: 10,
    artists: 10,
    albums: 10,
    pressings: 10,
  });
  const [itemsPerPageSaving, setItemsPerPageSaving] = useState(false);
  const [displaySettings, setDisplaySettings] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { setControls } = useViewControls();

  // Collection Sharing state
  const [sharingSettings, setSharingSettings] = useState<CollectionSharingSettings>({
    enabled: false,
    icon_type: 'mdiAlphaACircle',
    icon_fg_color: '#FFFFFF',
    icon_bg_color: '#1976D2',
  });
  const [sharingSaving, setSharingSaving] = useState(false);
  const [follows, setFollows] = useState<UserOwnerInfo[]>([]);
  const [followsLoading, setFollowsLoading] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importStatus, setImportStatus] = useState<CollectionImportResponse | null>(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [discogsStatus, setDiscogsStatus] = useState<DiscogsOAuthStatusResponse | null>(null);
  const [discogsLoading, setDiscogsLoading] = useState(false);
  const [discogsSyncLoading, setDiscogsSyncLoading] = useState(false);
  const [discogsNotice, setDiscogsNotice] = useState<string | null>(null);
  const [discogsStreamLines, setDiscogsStreamLines] = useState<string[]>([]);
  const [discogsPatUsername, setDiscogsPatUsername] = useState('');
  const [discogsPatToken, setDiscogsPatToken] = useState('');
  const [discogsPatSaving, setDiscogsPatSaving] = useState(false);

  // Extract user first name from Azure AD token
  const userFirstName: string = (accounts[0]?.idTokenClaims?.given_name as string) || accounts[0]?.name?.split(' ')[0] || 'A';

  const loadPreferences = async () => {
    try {
      setLoading(true);
      setError(null);
      const preferencesResp = await preferencesApi.getPreferences();
      setCurrency(preferencesResp.currency || '');
      setDisplaySettings(preferencesResp.display_settings || {});
      setItemsPerPageByView({
        collection: resolveItemsPerPage(preferencesResp, 'collection'),
        artists: resolveItemsPerPage(preferencesResp, 'artists'),
        albums: resolveItemsPerPage(preferencesResp, 'albums'),
        pressings: resolveItemsPerPage(preferencesResp, 'pressings'),
      });

      // Load collection sharing settings
      if (preferencesResp.collection_sharing) {
        setSharingSettings(preferencesResp.collection_sharing);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load profile settings');
    } finally {
      setLoading(false);
    }
  };

  const loadFollows = async () => {
    try {
      setFollowsLoading(true);
      const followsResp = await collectionSharingApi.getFollows();
      setFollows(followsResp.follows);
    } catch (err: any) {
      console.error('Failed to load follows:', err);
      setError(err.response?.data?.detail || 'Failed to load follows');
    } finally {
      setFollowsLoading(false);
    }
  };

  const loadDiscogsStatus = async () => {
    try {
      setDiscogsLoading(true);
      const status = await discogsApi.getOAuthStatus();
      setDiscogsStatus(status);
      if (status.username) {
        setDiscogsPatUsername((prev) => prev || status.username || '');
      }
    } catch (err) {
      console.error('Failed to load Discogs status:', err);
    } finally {
      setDiscogsLoading(false);
    }
  };

  useEffect(() => {
    loadPreferences();
    loadFollows();
    loadDiscogsStatus();
  }, []);

  useEffect(() => {
    setControls(null);
  }, [setControls]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const discogsResult = params.get('discogs');
    if (!discogsResult) {
      return;
    }
    if (discogsResult === 'connected') {
      setDiscogsNotice('Discogs connected successfully.');
      loadDiscogsStatus();
    } else if (discogsResult === 'error') {
      setImportError(params.get('message') || 'Discogs connection failed');
    }
    params.delete('discogs');
    params.delete('message');
    const nextQuery = params.toString();
    const nextUrl = `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ''}`;
    window.history.replaceState({}, '', nextUrl);
  }, []);

  useEffect(() => {
    if (!importStatus || importStatus.status === 'completed' || importStatus.status === 'failed') {
      return;
    }

    const interval = window.setInterval(async () => {
      try {
        const updated = await collectionApi.getImportStatus(importStatus.id);
        setImportStatus(updated);
      } catch (err) {
        console.error('Failed to refresh import status', err);
      }
    }, 3000);

    return () => window.clearInterval(interval);
  }, [importStatus?.id, importStatus?.status]);

  const handleCurrencySave = async () => {
    const nextCurrency = currency.trim().toUpperCase();
    if (!nextCurrency || nextCurrency.length !== 3) {
      setError('Currency must be a 3-letter ISO code');
      return;
    }
    setCurrencySaving(true);
    try {
      setError(null);
      const updated = await preferencesApi.updateCurrency(nextCurrency);
      setCurrency(updated.currency);
      setDisplaySettings(updated.display_settings || {});
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update currency');
    } finally {
      setCurrencySaving(false);
    }
  };

  const handleItemsPerPageSave = async () => {
    setItemsPerPageSaving(true);
    try {
      setError(null);
      const nextDisplaySettings: Record<string, any> = {
        ...displaySettings,
        items_per_page_by_view: itemsPerPageByView,
      };
      delete nextDisplaySettings.items_per_page;
      const updated = await preferencesApi.updateDisplaySettings({
        ...nextDisplaySettings,
      });
      setDisplaySettings(updated.display_settings || {});
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update display settings');
    } finally {
      setItemsPerPageSaving(false);
    }
  };

  const handleSharingSave = async () => {
    setSharingSaving(true);
    try {
      setError(null);
      const updated = await collectionSharingApi.updateSettings(sharingSettings);
      setSharingSettings(updated);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update collection sharing settings');
    } finally {
      setSharingSaving(false);
    }
  };

  const handleFollowUser = async (user: UserOwnerInfo) => {
    if (follows.length >= 3) {
      setError('You can only follow up to 3 users');
      return;
    }

    try {
      setError(null);
      await collectionSharingApi.followUser(user.user_id);
      setFollows([...follows, user]);
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to follow ${user.display_name}`);
    }
  };

  const handleUnfollowUser = async (userId: string) => {
    try {
      setError(null);
      await collectionSharingApi.unfollowUser(userId);
      setFollows(follows.filter(f => f.user_id !== userId));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to unfollow user');
    }
  };

  const handleImport = async () => {
    if (!importFile) {
      setImportError('Select a CSV file to import');
      return;
    }
    if (!importFile.name.toLowerCase().endsWith('.csv')) {
      setImportError('Please upload a .csv file');
      return;
    }
    setImportLoading(true);
    setImportError(null);
    try {
      const job = await collectionApi.importDiscogs(importFile);
      setImportStatus(job);
    } catch (err: any) {
      setImportError(err.response?.data?.detail || 'Failed to import collection');
    } finally {
      setImportLoading(false);
    }
  };

  const handleDiscogsConnect = async () => {
    setDiscogsNotice(null);
    setImportError(null);
    try {
      const response = await discogsApi.startOAuth({
        redirect_uri: window.location.pathname,
      });
      window.location.assign(response.authorization_url);
    } catch (err: any) {
      setImportError(err.response?.data?.detail || 'Failed to start Discogs OAuth');
    }
  };

  const handleDiscogsDisconnect = async () => {
    setDiscogsNotice(null);
    setImportError(null);
    try {
      await discogsApi.disconnectOAuth();
      await loadDiscogsStatus();
      setDiscogsNotice('Discogs connection removed.');
    } catch (err: any) {
      setImportError(err.response?.data?.detail || 'Failed to disconnect Discogs');
    }
  };

  const handleDiscogsSync = async () => {
    setDiscogsNotice(null);
    setImportError(null);
    setDiscogsSyncLoading(true);
    setDiscogsStreamLines([]);
    try {
      const account = accounts[0];
      if (!account) {
        throw new Error('No active account');
      }

      const tokenResponse = await instance.acquireTokenSilent({
        ...apiRequest,
        account,
      });

      const baseUrl = (getEnv('VITE_API_URL') || '').replace(/\/+$/, '');
      const response = await fetch(
        `${baseUrl}/api/v1/collection/imports/discogs/sync/stream`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${tokenResponse.accessToken}`,
            Accept: 'text/event-stream',
          },
        }
      );

      if (!response.ok || !response.body) {
        throw new Error('Failed to start Discogs sync');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        let delimiterIndex = buffer.indexOf('\n\n');
        while (delimiterIndex !== -1) {
          const chunk = buffer.slice(0, delimiterIndex);
          buffer = buffer.slice(delimiterIndex + 2);
          delimiterIndex = buffer.indexOf('\n\n');

          const lines = chunk.split('\n');
          for (const line of lines) {
            if (!line.startsWith('data:')) {
              continue;
            }
            const payloadText = line.slice(5).trim();
            if (!payloadText) {
              continue;
            }
            const payload = JSON.parse(payloadText) as {
              type?: string;
              artist?: string | null;
              title?: string | null;
              result?: string;
              import_id?: string;
              message?: string;
            };

            if (payload.type === 'row') {
              const name = [payload.artist, payload.title].filter(Boolean).join(' - ') || 'Unknown';
              const result = payload.result || 'Failed';
              setDiscogsStreamLines((prev) => [...prev, `${name}: ${result}`]);
            } else if (payload.type === 'complete') {
              if (payload.import_id) {
                const job = await collectionApi.getImportStatus(payload.import_id);
                setImportStatus(job);
              }
              await loadDiscogsStatus();
              setDiscogsNotice('Discogs sync completed.');
            } else if (payload.type === 'error') {
              throw new Error(payload.message || 'Discogs sync failed');
            }
          }
        }
      }
    } catch (err: any) {
      setImportError(err.response?.data?.detail || err.message || 'Failed to sync Discogs collection');
    } finally {
      setDiscogsSyncLoading(false);
    }
  };

  const handleDiscogsPatSave = async () => {
    setDiscogsNotice(null);
    setImportError(null);
    const cleanedUsername = discogsPatUsername.trim();
    const cleanedToken = discogsPatToken.trim();
    if (!cleanedUsername) {
      setImportError('Discogs username is required');
      return;
    }
    if (!cleanedToken) {
      setImportError('Discogs personal access token is required');
      return;
    }
    setDiscogsPatSaving(true);
    try {
      await discogsApi.connectPat({ username: cleanedUsername, token: cleanedToken });
      await loadDiscogsStatus();
      setDiscogsNotice('Discogs token saved.');
      setDiscogsPatToken('');
    } catch (err: any) {
      setImportError(err.response?.data?.detail || 'Failed to save Discogs token');
    } finally {
      setDiscogsPatSaving(false);
    }
  };

  const getIconPath = (iconType: string): string => {
    return (mdi as any)[iconType] || mdi.mdiAccount;
  };

  const lastSyncedLabel = discogsStatus?.last_synced_at
    ? new Date(discogsStatus.last_synced_at).toLocaleString()
    : 'Never';

  if (loading) {
    return <Loading message="Loading profile..." />;
  }

  return (
    <div className="settings-page">
      <div className="page-header">
        <div>
          <h1>Profile</h1>
          <p>Manage your personal preferences.</p>
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={loadPreferences} />}

      <section className="settings-section">
        <div className="settings-section-header">
          <div>
            <h2>Preferences</h2>
            <p>Set your preferred currency for purchases.</p>
          </div>
        </div>
        <div className="settings-form-row settings-form-row--compact">
          <input
            type="text"
            placeholder="Currency (e.g., USD)"
            value={currency}
            onChange={(e) => setCurrency(e.target.value.toUpperCase())}
            maxLength={3}
          />
          <button
            className="btn-primary"
            type="button"
            onClick={handleCurrencySave}
            disabled={currencySaving}
          >
            {currencySaving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </section>

      <section className="settings-section">
        <div className="settings-section-header">
          <div>
            <h2>Display</h2>
            <p>Set the default number of items per page for each view.</p>
          </div>
        </div>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>View</th>
                <th>Items per page</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(ITEMS_PER_PAGE_LABELS).map(([viewKey, label]) => {
                const view = viewKey as ItemsPerPageView;
                return (
                  <tr key={view}>
                    <td>{label}</td>
                    <td>
                      <select
                        value={itemsPerPageByView[view]}
                        onChange={(e) => {
                          const value = Number(e.target.value);
                          setItemsPerPageByView((prev) => ({ ...prev, [view]: value }));
                        }}
                      >
                        {ITEMS_PER_PAGE_OPTIONS.map((count) => (
                          <option key={count} value={count}>
                            {count} per page
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="settings-form-row settings-form-row--compact">
          <div />
          <button
            className="btn-primary"
            type="button"
            onClick={handleItemsPerPageSave}
            disabled={itemsPerPageSaving}
          >
            {itemsPerPageSaving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </section>

      <section className="settings-section">
        <div className="settings-section-header">
          <div>
            <h2>Collection Sharing</h2>
            <p>Configure how your collection appears to other users</p>
          </div>
        </div>
        <div className="settings-form-row">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={sharingSettings.enabled}
              onChange={(e) => setSharingSettings({ ...sharingSettings, enabled: e.target.checked })}
            />
            <span>Share My Collection</span>
          </label>
        </div>

        <IconSelector
          firstName={userFirstName}
          selectedIcon={sharingSettings.icon_type}
          fgColor={sharingSettings.icon_fg_color}
          bgColor={sharingSettings.icon_bg_color}
          onChange={(iconType) => setSharingSettings({ ...sharingSettings, icon_type: iconType })}
        />

        <ColorPicker
          label="Icon Color"
          value={sharingSettings.icon_fg_color}
          onChange={(color) => setSharingSettings({ ...sharingSettings, icon_fg_color: color })}
        />

        <ColorPicker
          label="Background Color"
          value={sharingSettings.icon_bg_color}
          onChange={(color) => setSharingSettings({ ...sharingSettings, icon_bg_color: color })}
        />

        <div className="settings-form-row settings-form-row--compact">
          <div />
          <button
            className="btn-primary"
            type="button"
            onClick={handleSharingSave}
            disabled={sharingSaving}
          >
            {sharingSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </section>

      <section className="settings-section">
        <div className="settings-section-header">
          <div>
            <h2>Following ({follows.length}/3)</h2>
            <p>Follow up to 3 users to see their collection ownership</p>
          </div>
        </div>

        {follows.length < 3 && (
          <UserSearch
            onSelect={handleFollowUser}
            excludeUserIds={follows.map(f => f.user_id)}
          />
        )}

        {followsLoading ? (
          <div className="follows-status">Loading follows...</div>
        ) : follows.length > 0 ? (
          <div className="follows-list">
            {follows.map(user => (
              <div key={user.user_id} className="follow-item">
                <div
                  className="follow-item-icon"
                  style={{ backgroundColor: user.icon_bg_color }}
                >
                  <Icon
                    path={getIconPath(user.icon_type)}
                    size={1}
                    color={user.icon_fg_color}
                  />
                </div>
                <div className="follow-item-details">
                  <div className="follow-item-name">{user.display_name}</div>
                  <div className="follow-item-handle">@{user.first_name}</div>
                </div>
                <button
                  className="btn-secondary"
                  type="button"
                  onClick={() => handleUnfollowUser(user.user_id)}
                >
                  Unfollow
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="follows-status follows-status--empty">
            You are not following anyone yet. Use the search above to find users to follow.
          </div>
        )}
      </section>

      <section className="settings-section settings-section--import">
        <div className="settings-section-header">
          <div>
            <h2>Import Collection</h2>
            <p>Use a Discogs personal access token for API sync, or upload a CSV export as fallback.</p>
          </div>
        </div>

        <div className="import-connection">
          {discogsLoading ? (
            <div className="import-connection-status">Checking Discogs connection...</div>
          ) : discogsStatus?.connected ? (
            <div className="import-connection-status">
              Connected as {discogsStatus.username} - Last sync: {lastSyncedLabel}
            </div>
          ) : (
            <div className="import-connection-status">Discogs not connected.</div>
          )}

          <div className="import-pat-fields">
            <div className="import-field">
              <label htmlFor="discogs-username">User Name</label>
              <input
                id="discogs-username"
                type="text"
                value={discogsPatUsername}
                onChange={(event) => setDiscogsPatUsername(event.target.value)}
              />
            </div>
            <div className="import-field">
              <label htmlFor="discogs-pat">Personal Access Token</label>
              <input
                id="discogs-pat"
                type="password"
                value={discogsPatToken}
                onChange={(event) => setDiscogsPatToken(event.target.value)}
              />
            </div>
          </div>

          <div className="import-actions">
            <button
              className="btn-primary"
              type="button"
              onClick={handleDiscogsPatSave}
              disabled={discogsPatSaving}
            >
              {discogsPatSaving ? 'Saving...' : 'Save PAT'}
            </button>
            {discogsStatus?.connected ? (
              <>
                <button
                  className="btn-primary"
                  type="button"
                  onClick={handleDiscogsSync}
                  disabled={discogsSyncLoading}
                >
                  {discogsSyncLoading ? 'Syncing...' : 'Sync from Discogs'}
                </button>
                <button
                  className="btn-secondary"
                  type="button"
                  onClick={handleDiscogsDisconnect}
                >
                  Disconnect
                </button>
              </>
            ) : (
              <button
                className="btn-secondary"
                type="button"
                onClick={handleDiscogsConnect}
              >
                Connect via OAuth
              </button>
            )}
          </div>
        </div>

        <div className="import-divider">CSV fallback</div>

        <div className="import-csv-row">
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => {
              const file = event.target.files?.[0] || null;
              setImportFile(file);
            }}
          />
          <button
            className="btn-primary"
            type="button"
            onClick={handleImport}
            disabled={importLoading || !importFile}
          >
            {importLoading ? 'Importing...' : 'Import'}
          </button>
        </div>

        {discogsNotice && (
          <div className="import-status import-status--success">{discogsNotice}</div>
        )}

        {importError && (
          <div className="import-status import-status--error">{importError}</div>
        )}

        {discogsStreamLines.length > 0 && (
          <div className="import-status">
            <div className="import-status-rows">
              {discogsStreamLines.map((line, index) => (
                <div key={`${index}-${line}`} className="import-status-row">
                  <span>{line}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {importStatus && (
          <div className="import-status">
            <div>Status: {importStatus.status}</div>
            <div>
              Processed {importStatus.processed_rows}/{importStatus.total_rows}
            </div>
            <div>
              Success: {importStatus.success_count} | Errors: {importStatus.error_count}
            </div>
            {importStatus.rows && importStatus.rows.length > 0 && (
              <div className="import-status-rows">
                {importStatus.rows.map((row) => {
                  const rowLabel = [row.artist, row.title].filter(Boolean).join(' - ');
                  const metadata = rowLabel ? `: ${rowLabel}` : '';
                  return (
                    <div
                      key={row.row_number}
                      className={`import-status-row import-status-row--${row.result}`}
                    >
                      <span>
                        Row {row.row_number}{metadata}
                      </span>
                      <span>{row.message}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}



