/**
 * Settings page for keyword lookups.
 */

import { useEffect, useState } from 'react';
import { lookupApi, preferencesApi } from '@/api/services';
import { Loading, ErrorAlert, Icon } from '@/components/UI';
import { mdiPencilOutline, mdiTrashCanOutline } from '@mdi/js';
import {
  GenreResponse,
  StyleResponse,
  ArtistTypeResponse,
  ReleaseTypeResponse,
  EditionTypeResponse,
  SleeveTypeResponse,
} from '@/types/api';
import { useViewControls } from '@/components/Layout/ViewControlsContext';
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
  const [activeTab, setActiveTab] = useState('genres');
  const [currency, setCurrency] = useState('');
  const [currencySaving, setCurrencySaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { setControls } = useViewControls();

  const tabs = [
    { id: 'preferences', label: 'Preferences' },
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
      const [
        preferencesResp,
        genresResp,
        stylesResp,
        artistTypesResp,
        releaseTypesResp,
        editionTypesResp,
        sleeveTypesResp,
      ] = await Promise.all([
        preferencesApi.getPreferences(),
        lookupApi.getAllGenres(),
        lookupApi.getAllStyles(),
        lookupApi.getAllArtistTypes(),
        lookupApi.getAllReleaseTypes(),
        lookupApi.getAllEditionTypes(),
        lookupApi.getAllSleeveTypes(),
      ]);
      setCurrency(preferencesResp.currency || '');
      setGenres(genresResp);
      setStyles(stylesResp);
      setArtistTypes(artistTypesResp);
      setReleaseTypes(releaseTypesResp);
      setEditionTypes(editionTypesResp);
      setSleeveTypes(sleeveTypesResp);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load settings data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  useEffect(() => {
    setControls(null);
  }, [setControls]);

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

  if (loading) {
    return <Loading message="Loading settings..." />;
  }

  return (
    <div className="settings-page">
      <div className="page-header">
        <div>
          <h1>Settings</h1>
          <p>Manage keyword tables for the catalog.</p>
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
        </section>
      )}

      {activeTab === 'genres' && (
        <NamedSection
          title="Genres"
          description="Controls available music genres."
          items={genres}
          onCreate={(payload) => runAction(() => lookupApi.createGenre(payload))}
          onUpdate={(id, payload) => runAction(() => lookupApi.updateGenre(id, payload))}
          onDelete={(id) => runAction(() => lookupApi.deleteGenre(id))}
        />
      )}

      {activeTab === 'styles' && (
        <StyleSection
          title="Styles"
          description="Controls available music styles (optional genre association)."
          items={styles}
          genres={genres}
          onCreate={(payload) => runAction(() => lookupApi.createStyle(payload))}
          onUpdate={(id, payload) => runAction(() => lookupApi.updateStyle(id, payload))}
          onDelete={(id) => runAction(() => lookupApi.deleteStyle(id))}
        />
      )}

      {activeTab === 'artist-types' && (
        <KeywordSection
          title="Artist Types"
          description="Controls available artist types in the catalog."
          items={artistTypes}
          onCreate={(payload) => runAction(() => lookupApi.createArtistType(payload))}
          onUpdate={(code, payload) => runAction(() => lookupApi.updateArtistType(code, payload))}
          onDelete={(code) => runAction(() => lookupApi.deleteArtistType(code))}
        />
      )}

      {activeTab === 'release-types' && (
        <KeywordSection
          title="Release Types"
          description="Controls available album release types."
          items={releaseTypes}
          onCreate={(payload) => runAction(() => lookupApi.createReleaseType(payload))}
          onUpdate={(code, payload) => runAction(() => lookupApi.updateReleaseType(code, payload))}
          onDelete={(code) => runAction(() => lookupApi.deleteReleaseType(code))}
        />
      )}

      {activeTab === 'edition-types' && (
        <KeywordSection
          title="Edition Types"
          description="Controls available pressing edition types."
          items={editionTypes}
          onCreate={(payload) => runAction(() => lookupApi.createEditionType(payload))}
          onUpdate={(code, payload) => runAction(() => lookupApi.updateEditionType(code, payload))}
          onDelete={(code) => runAction(() => lookupApi.deleteEditionType(code))}
        />
      )}

      {activeTab === 'sleeve-types' && (
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
  );
}
