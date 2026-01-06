/**
 * Collection item form - add/edit pressing in collection.
 */

import { useState, useEffect, FormEvent } from 'react';
import { collectionApi } from '@/api/services';
import { usePreferences } from '@/hooks/usePreferences';
import { parseLocaleNumber } from '@/utils/format';
import './Form.css';

interface CollectionItemFormProps {
  collectionItemId?: string;
  pressingId?: string;
  onSuccess: () => void;
  onCancel: () => void;
}

const CONDITIONS = [
  { value: 'Mint', label: 'Mint (M)' },
  { value: 'NM', label: 'Near Mint (NM)' },
  { value: 'VG+', label: 'Very Good Plus (VG+)' },
  { value: 'VG', label: 'Very Good (VG)' },
  { value: 'G', label: 'Good (G)' },
  { value: 'P', label: 'Poor (P)' },
] as const;

export function CollectionItemForm({ collectionItemId, pressingId, onSuccess, onCancel }: CollectionItemFormProps) {
  const [formData, setFormData] = useState({
    media_condition: 'NM',
    sleeve_condition: 'NM',
    purchase_price: '',
    purchase_currency: 'USD',
    purchase_date: '',
    seller: '',
    location: '',
    defect_notes: '',
    notes: '',
  });
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(!!collectionItemId);
  const [error, setError] = useState<string | null>(null);
  const isEditMode = !!collectionItemId;
  const { preferences } = usePreferences();

  // Load existing collection item if in edit mode
  useEffect(() => {
    const loadData = async () => {
      if (collectionItemId) {
        try {
          const item = await collectionApi.getById(collectionItemId);
          setFormData({
            media_condition: item.media_condition || 'NM',
            sleeve_condition: item.sleeve_condition || 'NM',
            purchase_price: item.purchase_price?.toString() || '',
            purchase_currency: item.purchase_currency || 'USD',
            purchase_date: item.purchase_date || '',
            seller: item.seller || '',
            location: item.location || '',
            defect_notes: item.defect_notes || '',
            notes: item.notes || '',
          });
        } catch (err: any) {
          console.error('Failed to load collection item:', err);
          setError(err.response?.data?.detail || 'Failed to load collection item data');
        } finally {
          setInitialLoading(false);
        }
      }
    };
    loadData();
  }, [collectionItemId]);

  useEffect(() => {
    if (preferences?.currency) {
      setFormData((prev) => ({ ...prev, purchase_currency: preferences.currency }));
    }
  }, [preferences?.currency]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload: any = {
        media_condition: formData.media_condition,
        sleeve_condition: formData.sleeve_condition,
      };

      // Only add pressing_id for new items
      if (!isEditMode && pressingId) {
        payload.pressing_id = pressingId;
      }

      // Add optional fields if provided
      if (formData.purchase_price) {
        const price = parseLocaleNumber(formData.purchase_price);
        if (price !== null) {
          payload.purchase_price = price;
        }
      }
      if (formData.purchase_currency) payload.purchase_currency = formData.purchase_currency;
      if (formData.purchase_date) payload.purchase_date = formData.purchase_date;
      if (formData.seller) payload.seller = formData.seller;
      if (formData.location) payload.location = formData.location;
      if (formData.defect_notes) payload.defect_notes = formData.defect_notes;
      if (formData.notes) payload.notes = formData.notes;

      if (isEditMode && collectionItemId) {
        await collectionApi.update(collectionItemId, payload);
      } else {
        await collectionApi.addItem(payload);
      }
      onSuccess();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((e: any) => e.msg).join(', '));
      } else {
        setError(detail || err.message || `Failed to ${isEditMode ? 'update' : 'add'} collection item`);
      }
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) {
    return <div className="form-loading">Loading collection item data...</div>;
  }

  return (
    <form onSubmit={handleSubmit} className="form">
      {error && (
        <div className="form-error">
          {error}
        </div>
      )}

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="media_condition">
            Vinyl Condition <span className="required">*</span>
          </label>
          <select
            id="media_condition"
            name="media_condition"
            value={formData.media_condition}
            onChange={handleChange}
            required
          >
            {CONDITIONS.map((cond) => (
              <option key={cond.value} value={cond.value}>
                {cond.label}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="sleeve_condition">
            Sleeve Condition <span className="required">*</span>
          </label>
          <select
            id="sleeve_condition"
            name="sleeve_condition"
            value={formData.sleeve_condition}
            onChange={handleChange}
            required
          >
            {CONDITIONS.map((cond) => (
              <option key={cond.value} value={cond.value}>
                {cond.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="purchase_price">Purchase Price</label>
          <input
            type="number"
            id="purchase_price"
            name="purchase_price"
            value={formData.purchase_price}
            onChange={handleChange}
            placeholder="25.99"
            step="0.01"
            min="0"
          />
        </div>

        <div className="form-group">
          <label htmlFor="purchase_currency">Currency</label>
          <input
            type="text"
            id="purchase_currency"
            name="purchase_currency"
            value={formData.purchase_currency}
            placeholder="USD"
            maxLength={3}
            minLength={3}
            readOnly
            aria-readonly="true"
          />
          <small>Managed in Settings</small>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="purchase_date">Purchase Date</label>
          <input
            type="date"
            id="purchase_date"
            name="purchase_date"
            value={formData.purchase_date}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="seller">Seller</label>
          <input
            type="text"
            id="seller"
            name="seller"
            value={formData.seller}
            onChange={handleChange}
            placeholder="Discogs seller"
            maxLength={200}
          />
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="location">Storage Location</label>
        <input
          type="text"
          id="location"
          name="location"
          value={formData.location}
          onChange={handleChange}
          placeholder="Shelf A3"
          maxLength={200}
        />
      </div>

      <div className="form-group">
        <label htmlFor="defect_notes">Defect Notes</label>
        <textarea
          id="defect_notes"
          name="defect_notes"
          value={formData.defect_notes}
          onChange={handleChange}
          rows={2}
          placeholder="Minor scuff on side B"
        />
      </div>

      <div className="form-group">
        <label htmlFor="notes">Notes</label>
        <textarea
          id="notes"
          name="notes"
          value={formData.notes}
          onChange={handleChange}
          rows={3}
          placeholder="First pressing with poster"
        />
      </div>

      <div className="form-actions">
        <button
          type="button"
          onClick={onCancel}
          className="btn-secondary"
          disabled={loading}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="btn-primary"
          disabled={loading}
        >
          {loading
            ? (isEditMode ? 'Updating...' : 'Adding...')
            : (isEditMode ? 'Update Item' : 'Add to Collection')}
        </button>
      </div>
    </form>
  );
}
