/**
 * Settings page for keyword lookups.
 */

import { useEffect, useState } from 'react';
import { lookupApi, preferencesApi, systemLogsApi } from '@/api/services';
import { Loading, ErrorAlert, Icon } from '@/components/UI';
import { mdiPencilOutline, mdiTrashCanOutline } from '@mdi/js';
import {
  GenreResponse,
  StyleResponse,
  ArtistTypeResponse,
  ReleaseTypeResponse,
  EditionTypeResponse,
  SleeveTypeResponse,
  SystemLogEntry,
} from '@/types/api';
import { useViewControls } from '@/components/Layout/ViewControlsContext';
import { useIsAdmin } from '@/auth/useAdmin';
import { formatDateTime } from '@/utils/format';
import './Settings.css';
import '../styles/Table.css';

type KeywordItem = {
  code: string;
  name: string;
  display_order?: number;
};

type NamedItem = {
  id: string;
  name: string;
  display_order?: number;
};

type KeywordSectionProps<T extends KeywordItem> = {
  title: string;
  description: string;
  items: T[];
  onCreate: (payload: { code: string; name: string; display_order?: number }) => Promise<unknown>;
  onUpdate: (code: string, payload: { name: string; display_order?: number }) => Promise<unknown>;
  onDelete: (code: string) => Promise<unknown>;
};

function KeywordSection<T extends KeywordItem>({
  title,
  description,
  items,
  onCreate,
  onUpdate,
  onDelete,
}: KeywordSectionProps<T>) {
  const [newCode, setNewCode] = useState('');
  const [newName, setNewName] = useState('');
  const [newOrder, setNewOrder] = useState('');
  const [editingCode, setEditingCode] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [editOrder, setEditOrder] = useState('');
  const [saving, setSaving] = useState(false);

  const startEdit = (item: KeywordItem) => {
    setEditingCode(item.code);
    setEditName(item.name);
    setEditOrder(item.display_order?.toString() || '');
  };

  const cancelEdit = () => {
    setEditingCode(null);
    setEditName('');
    setEditOrder('');
  };

  const handleCreate = async () => {
    if (!newCode.trim() || !newName.trim()) {
      return;
    }
    const display_order = newOrder.trim() ? Number(newOrder) : undefined;
    setSaving(true);
    try {
      await onCreate({
        code: newCode.trim(),
        name: newName.trim(),
        display_order,
      });
      setNewCode('');
      setNewName('');
      setNewOrder('');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async () => {
    if (!editingCode || !editName.trim()) {
      return;
    }
    const display_order = editOrder.trim() ? Number(editOrder) : undefined;
    setSaving(true);
    try {
      await onUpdate(editingCode, {
        name: editName.trim(),
        display_order,
      });
      cancelEdit();
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (code: string, name: string) => {
    if (!confirm(`Delete "${name}"? This may affect existing records.`)) {
      return;
    }
    setSaving(true);
    try {
      await onDelete(code);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="settings-section">
      <div className="settings-section-header">
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
      </div>

      <div className="settings-form-row">
        <input
          type="text"
          placeholder="Code"
          value={newCode}
          onChange={(e) => setNewCode(e.target.value)}
          maxLength={50}
        />
        <input
          type="text"
          placeholder="Name"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          maxLength={100}
        />
        <input
          type="number"
          placeholder="Order"
          value={newOrder}
          onChange={(e) => setNewOrder(e.target.value)}
          min="0"
        />
        <button className="btn-primary" onClick={handleCreate} disabled={saving}>
          Add
        </button>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Name</th>
              <th>Order</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td colSpan={4} className="empty-cell">No entries</td>
              </tr>
            )}
            {items.map((item) => (
              <tr key={item.code}>
                <td className="name-cell">{item.code}</td>
                <td>
                  {editingCode === item.code ? (
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      maxLength={100}
                    />
                  ) : (
                    item.name
                  )}
                </td>
                <td>
                  {editingCode === item.code ? (
                    <input
                      type="number"
                      value={editOrder}
                      onChange={(e) => setEditOrder(e.target.value)}
                      min="0"
                    />
                  ) : (
                    item.display_order ?? '-'
                  )}
                </td>
                <td className="actions-cell">
                  {editingCode === item.code ? (
                    <>
                      <button className="btn-action" onClick={handleUpdate} disabled={saving}>
                        ✓
                      </button>
                      <button className="btn-action" onClick={cancelEdit} disabled={saving}>
                        ✕
                      </button>
                    </>
                  ) : (
                    <>
                      <button className="btn-action" onClick={() => startEdit(item)} disabled={saving}>
                        <Icon path={mdiPencilOutline} />
                      </button>
                      <button
                        className="btn-action btn-danger"
                        onClick={() => handleDelete(item.code, item.name)}
                        disabled={saving}
                      >
                        <Icon path={mdiTrashCanOutline} />
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

type NamedSectionProps<T extends NamedItem> = {
  title: string;
  description: string;
  items: T[];
  onCreate: (payload: { name: string; display_order?: number }) => Promise<unknown>;
  onUpdate: (id: string, payload: { name: string; display_order?: number }) => Promise<unknown>;
  onDelete: (id: string) => Promise<unknown>;
};

function NamedSection<T extends NamedItem>({
  title,
  description,
  items,
  onCreate,
  onUpdate,
  onDelete,
}: NamedSectionProps<T>) {
  const [newName, setNewName] = useState('');
  const [newOrder, setNewOrder] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [editOrder, setEditOrder] = useState('');
  const [saving, setSaving] = useState(false);

  const startEdit = (item: NamedItem) => {
    setEditingId(item.id);
    setEditName(item.name);
    setEditOrder(item.display_order?.toString() || '');
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditName('');
    setEditOrder('');
  };

  const handleCreate = async () => {
    if (!newName.trim()) {
      return;
    }
    const display_order = newOrder.trim() ? Number(newOrder) : undefined;
    setSaving(true);
    try {
      await onCreate({
        name: newName.trim(),
        display_order,
      });
      setNewName('');
      setNewOrder('');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async () => {
    if (!editingId || !editName.trim()) {
      return;
    }
    const display_order = editOrder.trim() ? Number(editOrder) : undefined;
    setSaving(true);
    try {
      await onUpdate(editingId, {
        name: editName.trim(),
        display_order,
      });
      cancelEdit();
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"? This may affect existing records.`)) {
      return;
    }
    setSaving(true);
    try {
      await onDelete(id);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="settings-section">
      <div className="settings-section-header">
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
      </div>

      <div className="settings-form-row">
        <input
          type="text"
          placeholder="Name"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          maxLength={100}
        />
        <input
          type="number"
          placeholder="Order"
          value={newOrder}
          onChange={(e) => setNewOrder(e.target.value)}
          min="0"
        />
        <button className="btn-primary" onClick={handleCreate} disabled={saving}>
          Add
        </button>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Order</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td colSpan={3} className="empty-cell">No entries</td>
              </tr>
            )}
            {items.map((item) => (
              <tr key={item.id}>
                <td>
                  {editingId === item.id ? (
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      maxLength={100}
                    />
                  ) : (
                    item.name
                  )}
                </td>
                <td>
                  {editingId === item.id ? (
                    <input
                      type="number"
                      value={editOrder}
                      onChange={(e) => setEditOrder(e.target.value)}
                      min="0"
                    />
                  ) : (
                    item.display_order ?? '-'
                  )}
                </td>
                <td className="actions-cell">
                  {editingId === item.id ? (
                    <>
                      <button className="btn-action" onClick={handleUpdate} disabled={saving}>
                        ✓
                      </button>
                      <button className="btn-action" onClick={cancelEdit} disabled={saving}>
                        ✕
                      </button>
                    </>
                  ) : (
                    <>
                      <button className="btn-action" onClick={() => startEdit(item)} disabled={saving}>
                        <Icon path={mdiPencilOutline} />
                      </button>
                      <button
                        className="btn-action btn-danger"
                        onClick={() => handleDelete(item.id, item.name)}
                        disabled={saving}
                      >
                        <Icon path={mdiTrashCanOutline} />
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

type StyleSectionProps = {
  title: string;
  description: string;
  items: StyleResponse[];
  genres: GenreResponse[];
  onCreate: (payload: { name: string; display_order?: number; genre_id?: string }) => Promise<unknown>;
  onUpdate: (id: string, payload: { name: string; display_order?: number; genre_id?: string }) => Promise<unknown>;
  onDelete: (id: string) => Promise<unknown>;
};

function StyleSection({
  title,
  description,
  items,
  genres,
  onCreate,
  onUpdate,
  onDelete,
}: StyleSectionProps) {
  const [newName, setNewName] = useState('');
  const [newOrder, setNewOrder] = useState('');
  const [newGenreId, setNewGenreId] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [editOrder, setEditOrder] = useState('');
  const [editGenreId, setEditGenreId] = useState('');
  const [saving, setSaving] = useState(false);

  const genreNameById = new Map(genres.map((genre) => [genre.id, genre.name]));

  const startEdit = (item: StyleResponse) => {
    setEditingId(item.id);
    setEditName(item.name);
    setEditOrder(item.display_order?.toString() || '');
    setEditGenreId(item.genre_id || '');
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditName('');
    setEditOrder('');
    setEditGenreId('');
  };

  const handleCreate = async () => {
    if (!newName.trim()) {
      return;
    }
    const display_order = newOrder.trim() ? Number(newOrder) : undefined;
    const genre_id = newGenreId ? newGenreId : undefined;
    setSaving(true);
    try {
      await onCreate({
        name: newName.trim(),
        display_order,
        genre_id,
      });
      setNewName('');
      setNewOrder('');
      setNewGenreId('');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async () => {
    if (!editingId || !editName.trim()) {
      return;
    }
    const display_order = editOrder.trim() ? Number(editOrder) : undefined;
    const genre_id = editGenreId ? editGenreId : undefined;
    setSaving(true);
    try {
      await onUpdate(editingId, {
        name: editName.trim(),
        display_order,
        genre_id,
      });
      cancelEdit();
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"? This may affect existing records.`)) {
      return;
    }
    setSaving(true);
    try {
      await onDelete(id);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="settings-section">
      <div className="settings-section-header">
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
      </div>

      <div className="settings-form-row">
        <input
          type="text"
          placeholder="Name"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          maxLength={100}
        />
        <select value={newGenreId} onChange={(e) => setNewGenreId(e.target.value)}>
          <option value="">No genre</option>
          {genres.map((genre) => (
            <option key={genre.id} value={genre.id}>
              {genre.name}
            </option>
          ))}
        </select>
        <input
          type="number"
          placeholder="Order"
          value={newOrder}
          onChange={(e) => setNewOrder(e.target.value)}
          min="0"
        />
        <button className="btn-primary" onClick={handleCreate} disabled={saving}>
          Add
        </button>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Genre</th>
              <th>Order</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td colSpan={4} className="empty-cell">No entries</td>
              </tr>
            )}
            {items.map((item) => (
              <tr key={item.id}>
                <td>
                  {editingId === item.id ? (
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      maxLength={100}
                    />
                  ) : (
                    item.name
                  )}
                </td>
                <td>
                  {editingId === item.id ? (
                    <select value={editGenreId} onChange={(e) => setEditGenreId(e.target.value)}>
                      <option value="">No genre</option>
                      {genres.map((genre) => (
                        <option key={genre.id} value={genre.id}>
                          {genre.name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    genreNameById.get(item.genre_id || '') || '-'
                  )}
                </td>
                <td>
                  {editingId === item.id ? (
                    <input
                      type="number"
                      value={editOrder}
                      onChange={(e) => setEditOrder(e.target.value)}
                      min="0"
                    />
                  ) : (
                    item.display_order ?? '-'
                  )}
                </td>
                <td className="actions-cell">
                  {editingId === item.id ? (
                    <>
                      <button className="btn-action" onClick={handleUpdate} disabled={saving}>
                        ✓
                      </button>
                      <button className="btn-action" onClick={cancelEdit} disabled={saving}>
                        ✕
                      </button>
                    </>
                  ) : (
                    <>
                      <button className="btn-action" onClick={() => startEdit(item)} disabled={saving}>
                        <Icon path={mdiPencilOutline} />
                      </button>
                      <button
                        className="btn-action btn-danger"
                        onClick={() => handleDelete(item.id, item.name)}
                        disabled={saving}
                      >
                        <Icon path={mdiTrashCanOutline} />
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function Settings() {
  const [genres, setGenres] = useState<GenreResponse[]>([]);
  const [styles, setStyles] = useState<StyleResponse[]>([]);
  const [artistTypes, setArtistTypes] = useState<ArtistTypeResponse[]>([]);
  const [releaseTypes, setReleaseTypes] = useState<ReleaseTypeResponse[]>([]);
  const [editionTypes, setEditionTypes] = useState<EditionTypeResponse[]>([]);
  const [sleeveTypes, setSleeveTypes] = useState<SleeveTypeResponse[]>([]);
  const [activeTab, setActiveTab] = useState('preferences');
  const [activeKeywordTab, setActiveKeywordTab] = useState('genres');
  const [genrePage, setGenrePage] = useState(1);
  const [stylePage, setStylePage] = useState(1);
  const [logRetentionDays, setLogRetentionDays] = useState(60);
  const [logRetentionSaving, setLogRetentionSaving] = useState(false);
  const [logEntries, setLogEntries] = useState<SystemLogEntry[]>([]);
  const [logTotal, setLogTotal] = useState(0);
  const [logPage, setLogPage] = useState(1);
  const [logPageSize, setLogPageSize] = useState(50);
  const [logSeverityFilter, setLogSeverityFilter] = useState<'all' | 'INFO' | 'WARN' | 'ERROR'>('all');
  const [logLoading, setLogLoading] = useState(false);
  const [logError, setLogError] = useState<string | null>(null);
  const pageSize = 10;
  const [currency, setCurrency] = useState('');
  const [currencySaving, setCurrencySaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { setControls } = useViewControls();
  const { isAdmin, isLoading: isAdminLoading } = useIsAdmin();

  const tabs = [
    { id: 'preferences', label: 'Preferences' },
    { id: 'keywords', label: 'Keywords' },
    { id: 'logs', label: 'Logs' },
  ];

  const keywordTabs = [
    { id: 'genres', label: 'Genres' },
    { id: 'styles', label: 'Styles' },
    { id: 'artist-types', label: 'Artist Types' },
    { id: 'release-types', label: 'Release Types' },
    { id: 'edition-types', label: 'Edition Types' },
    { id: 'sleeve-types', label: 'Sleeve Types' },
  ];

  const loadAll = async () => {
    try {
      setLoading(true);
      setError(null);
      const retentionPromise = isAdmin
        ? systemLogsApi.getLogRetention()
        : Promise.resolve(null);
      const [
        preferencesResp,
        genresResp,
        stylesResp,
        artistTypesResp,
        releaseTypesResp,
        editionTypesResp,
        sleeveTypesResp,
        retentionResp,
      ] = await Promise.all([
        preferencesApi.getPreferences(),
        lookupApi.getAllGenres(),
        lookupApi.getAllStyles(),
        lookupApi.getAllArtistTypes(),
        lookupApi.getAllReleaseTypes(),
        lookupApi.getAllEditionTypes(),
        lookupApi.getAllSleeveTypes(),
        retentionPromise,
      ]);
      setCurrency(preferencesResp.currency || '');
      setGenres(genresResp);
      setStyles(stylesResp);
      setArtistTypes(artistTypesResp);
      setReleaseTypes(releaseTypesResp);
      setEditionTypes(editionTypesResp);
      setSleeveTypes(sleeveTypesResp);
      if (retentionResp?.retention_days) {
        setLogRetentionDays(retentionResp.retention_days);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load settings data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdminLoading) {
      return;
    }
    loadAll();
  }, [isAdminLoading, isAdmin]);

  useEffect(() => {
    setControls(null);
  }, [setControls]);

  const genreTotalPages = Math.max(1, Math.ceil(genres.length / pageSize));
  const styleTotalPages = Math.max(1, Math.ceil(styles.length / pageSize));
  const pagedGenres = genres.slice((genrePage - 1) * pageSize, genrePage * pageSize);
  const pagedStyles = styles.slice((stylePage - 1) * pageSize, stylePage * pageSize);

  useEffect(() => {
    if (genrePage > genreTotalPages) {
      setGenrePage(genreTotalPages);
    }
  }, [genrePage, genreTotalPages]);

  useEffect(() => {
    if (stylePage > styleTotalPages) {
      setStylePage(styleTotalPages);
    }
  }, [stylePage, styleTotalPages]);

  const runAction = async (action: () => Promise<unknown>) => {
    try {
      setError(null);
      await action();
      await loadAll();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update settings');
    }
  };

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
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update currency');
    } finally {
      setCurrencySaving(false);
    }
  };

  const handleRetentionSave = async () => {
    setLogRetentionSaving(true);
    try {
      setError(null);
      const updated = await systemLogsApi.updateLogRetention(logRetentionDays);
      setLogRetentionDays(updated.retention_days);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update log retention');
    } finally {
      setLogRetentionSaving(false);
    }
  };

  const loadLogs = async () => {
    try {
      setLogLoading(true);
      setLogError(null);
      const response = await systemLogsApi.getLogs({
        limit: logPageSize,
        offset: (logPage - 1) * logPageSize,
      });
      setLogEntries(response.items || []);
      setLogTotal(response.total || 0);
    } catch (err: any) {
      setLogError(err.response?.data?.detail || 'Failed to load logs');
    } finally {
      setLogLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab !== 'logs' || !isAdmin) {
      return;
    }
    loadLogs();
  }, [activeTab, isAdmin, logPage, logPageSize]);

  useEffect(() => {
    if (activeTab === 'logs') {
      setLogPage(1);
    }
  }, [activeTab]);

  const logTotalPages = Math.max(1, Math.ceil(logTotal / logPageSize));
  const filteredLogEntries = logSeverityFilter === 'all'
    ? logEntries
    : logEntries.filter((entry) => entry.severity === logSeverityFilter);

  if (loading) {
    return <Loading message="Loading settings..." />;
  }

  return (
    <div className="settings-page">
      <div className="page-header">
        <div>
          <h1>Settings</h1>
          <p>Manage system-wide settings</p>
        </div>
      </div>

      {error && <ErrorAlert message={error} onRetry={loadAll} />}

      <div className="settings-tabs" role="tablist" aria-label="Settings sections">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`settings-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'preferences' && (
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
          {isAdmin && (
            <div className="settings-form-row settings-form-row--compact">
              <select
                value={logRetentionDays}
                onChange={(e) => setLogRetentionDays(Number(e.target.value))}
              >
                {[30, 60, 90].map((value) => (
                  <option key={value} value={value}>
                    Log retention: {value} days
                  </option>
                ))}
              </select>
              <button
                className="btn-primary"
                type="button"
                onClick={handleRetentionSave}
                disabled={logRetentionSaving}
              >
                {logRetentionSaving ? 'Saving...' : 'Save'}
              </button>
            </div>
          )}
        </section>
      )}

      {activeTab === 'keywords' && (
        <div className="settings-keywords">
          <div className="settings-subtabs" role="tablist" aria-label="Keyword sections">
            {keywordTabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={activeKeywordTab === tab.id}
                className={`settings-subtab ${activeKeywordTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveKeywordTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {activeKeywordTab === 'genres' && (
            <>
              <NamedSection
                title="Genres"
                description="Controls available music genres."
                items={pagedGenres}
                onCreate={(payload) => runAction(() => lookupApi.createGenre(payload))}
                onUpdate={(id, payload) => runAction(() => lookupApi.updateGenre(id, payload))}
                onDelete={(id) => runAction(() => lookupApi.deleteGenre(id))}
              />
              {genreTotalPages > 1 && (
                <div className="pagination settings-pagination">
                  <div className="pagination-controls">
                    <button
                      onClick={() => setGenrePage((prev) => Math.max(1, prev - 1))}
                      disabled={genrePage === 1}
                      className="pagination-button"
                    >
                      Previous
                    </button>
                    <div className="pagination-info">
                      Page {genrePage} of {genreTotalPages}
                    </div>
                    <button
                      onClick={() => setGenrePage((prev) => Math.min(genreTotalPages, prev + 1))}
                      disabled={genrePage === genreTotalPages}
                      className="pagination-button"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          {activeKeywordTab === 'styles' && (
            <>
              <StyleSection
                title="Styles"
                description="Controls available music styles (optional genre association)."
                items={pagedStyles}
                genres={genres}
                onCreate={(payload) => runAction(() => lookupApi.createStyle(payload))}
                onUpdate={(id, payload) => runAction(() => lookupApi.updateStyle(id, payload))}
                onDelete={(id) => runAction(() => lookupApi.deleteStyle(id))}
              />
              {styleTotalPages > 1 && (
                <div className="pagination settings-pagination">
                  <div className="pagination-controls">
                    <button
                      onClick={() => setStylePage((prev) => Math.max(1, prev - 1))}
                      disabled={stylePage === 1}
                      className="pagination-button"
                    >
                      Previous
                    </button>
                    <div className="pagination-info">
                      Page {stylePage} of {styleTotalPages}
                    </div>
                    <button
                      onClick={() => setStylePage((prev) => Math.min(styleTotalPages, prev + 1))}
                      disabled={stylePage === styleTotalPages}
                      className="pagination-button"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          {activeKeywordTab === 'artist-types' && (
            <KeywordSection
              title="Artist Types"
              description="Controls available artist types in the catalog."
              items={artistTypes}
              onCreate={(payload) => runAction(() => lookupApi.createArtistType(payload))}
              onUpdate={(code, payload) => runAction(() => lookupApi.updateArtistType(code, payload))}
              onDelete={(code) => runAction(() => lookupApi.deleteArtistType(code))}
            />
          )}

          {activeKeywordTab === 'release-types' && (
            <KeywordSection
              title="Release Types"
              description="Controls available album release types."
              items={releaseTypes}
              onCreate={(payload) => runAction(() => lookupApi.createReleaseType(payload))}
              onUpdate={(code, payload) => runAction(() => lookupApi.updateReleaseType(code, payload))}
              onDelete={(code) => runAction(() => lookupApi.deleteReleaseType(code))}
            />
          )}

          {activeKeywordTab === 'edition-types' && (
            <KeywordSection
              title="Edition Types"
              description="Controls available pressing edition types."
              items={editionTypes}
              onCreate={(payload) => runAction(() => lookupApi.createEditionType(payload))}
              onUpdate={(code, payload) => runAction(() => lookupApi.updateEditionType(code, payload))}
              onDelete={(code) => runAction(() => lookupApi.deleteEditionType(code))}
            />
          )}

          {activeKeywordTab === 'sleeve-types' && (
            <KeywordSection
              title="Sleeve Types"
              description="Controls available sleeve/jacket types."
              items={sleeveTypes}
              onCreate={(payload) => runAction(() => lookupApi.createSleeveType(payload))}
              onUpdate={(code, payload) => runAction(() => lookupApi.updateSleeveType(code, payload))}
              onDelete={(code) => runAction(() => lookupApi.deleteSleeveType(code))}
            />
          )}
        </div>
      )}

      {activeTab === 'logs' && (
        <section className="settings-section">
          <div className="settings-section-header">
            <div>
              <h2>System Logs</h2>
              <p>Audit trail of system activity and Settings changes.</p>
            </div>
          </div>

          <div className="pagination settings-pagination settings-log-controls">
            <div className="pagination-controls">
              <button
                onClick={() => setLogPage((prev) => Math.max(1, prev - 1))}
                disabled={logPage === 1}
                className="pagination-button"
              >
                Previous
              </button>
              <div className="pagination-info">
                <label htmlFor="log-page-select">Page</label>
                <select
                  id="log-page-select"
                  value={logPage}
                  onChange={(e) => setLogPage(Number(e.target.value))}
                >
                  {Array.from({ length: logTotalPages }, (_, index) => index + 1).map((page) => (
                    <option key={page} value={page}>
                      {page}
                    </option>
                  ))}
                </select>
                <span>of {logTotalPages}</span>
              </div>
              <button
                onClick={() => setLogPage((prev) => Math.min(logTotalPages, prev + 1))}
                disabled={logPage === logTotalPages}
                className="pagination-button"
              >
                Next
              </button>
            </div>
            <div className="items-per-page">
              <label htmlFor="log-severity-filter">Severity</label>
              <select
                id="log-severity-filter"
                value={logSeverityFilter}
                onChange={(e) => setLogSeverityFilter(e.target.value as 'all' | 'INFO' | 'WARN' | 'ERROR')}
              >
                <option value="all">All</option>
                <option value="INFO">INFO</option>
                <option value="WARN">WARN</option>
                <option value="ERROR">ERROR</option>
              </select>
              <button
                type="button"
                className="btn-primary"
                onClick={loadLogs}
                disabled={logLoading}
              >
                Refresh
              </button>
            </div>
          </div>

          {logLoading && (
            <div className="settings-status">Loading logs...</div>
          )}
          {logError && !logLoading && (
            <div className="settings-status settings-status--error">{logError}</div>
          )}
          {!logLoading && !logError && filteredLogEntries.length === 0 && (
            <div className="settings-status">No log entries found.</div>
          )}
          {!logLoading && !logError && filteredLogEntries.length > 0 && (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date/Time</th>
                    <th>User</th>
                    <th>Severity</th>
                    <th>Component</th>
                    <th>Log</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLogEntries.map((entry) => (
                    <tr key={entry.id}>
                      <td>{formatDateTime(entry.created_at)}</td>
                      <td>{entry.user_name}</td>
                      <td className={`log-severity log-severity--${entry.severity.toLowerCase()}`}>
                        {entry.severity}
                      </td>
                      <td>{entry.component}</td>
                      <td>{entry.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {logTotalPages > 1 && (
            <div className="pagination settings-pagination">
              <div className="pagination-controls">
                <button
                  onClick={() => setLogPage((prev) => Math.max(1, prev - 1))}
                  disabled={logPage === 1}
                  className="pagination-button"
                >
                  Previous
                </button>
                <div className="pagination-info">
                  Page {logPage} of {logTotalPages}
                </div>
                <button
                  onClick={() => setLogPage((prev) => Math.min(logTotalPages, prev + 1))}
                  disabled={logPage === logTotalPages}
                  className="pagination-button"
                >
                  Next
                </button>
              </div>
              <div className="items-per-page">
                <span>Per page</span>
                <select
                  value={logPageSize}
                  onChange={(e) => {
                    setLogPageSize(Number(e.target.value));
                    setLogPage(1);
                  }}
                >
                  {[50, 100, 200].map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
