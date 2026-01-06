/**
 * Modal for adding an existing pressing to the user's collection.
 */

import { useState, useEffect, FormEvent } from 'react';
import { Modal } from '../UI/Modal';
import { collectionApi } from '@/api/services';
import { Condition, CollectionItemCreate } from '@/types/api';
import { usePreferences } from '@/hooks/usePreferences';
import { parseLocaleNumber } from '@/utils/format';
import '../Forms/Form.css';

interface AddToCollectionModalProps {
  pressingId: string;
  pressingDescription: string; // For display (e.g., "1969 UK LP")
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

// Condition options
const CONDITION_OPTIONS = [
  { value: Condition.MINT, label: 'Mint (M)' },
  { value: Condition.NEAR_MINT, label: 'Near Mint (NM)' },
  { value: Condition.VG_PLUS, label: 'Very Good Plus (VG+)' },
  { value: Condition.VG, label: 'Very Good (VG)' },
  { value: Condition.GOOD, label: 'Good (G)' },
  { value: Condition.POOR, label: 'Poor (P)' },
];

export function AddToCollectionModal({
  pressingId,
  pressingDescription,
  isOpen,
  onClose,
  onSuccess,
}: AddToCollectionModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { preferences } = usePreferences();

  const [formData, setFormData] = useState({
    media_condition: Condition.NEAR_MINT,
    sleeve_condition: Condition.NEAR_MINT,
    purchase_price: '',
    purchase_currency: 'USD',
    purchase_date: '',
    location: '',
  });

  useEffect(() => {
    if (preferences?.currency) {
      setFormData((prev) => ({ ...prev, purchase_currency: preferences.currency }));
    }
  }, [preferences?.currency]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.media_condition || !formData.sleeve_condition) {
      setError('Media and sleeve conditions are required');
      return;
    }

    setLoading(true);

    try {
      const payload: CollectionItemCreate = {
        pressing_id: pressingId,
        media_condition: formData.media_condition,
        sleeve_condition: formData.sleeve_condition,
      };

      // Add optional fields if provided
      if (formData.purchase_price) {
        const price = parseLocaleNumber(formData.purchase_price);
        if (price !== null && price >= 0) {
          payload.purchase_price = price;
        }
      }
      if (formData.purchase_currency) payload.purchase_currency = formData.purchase_currency;
      if (formData.purchase_date) payload.purchase_date = formData.purchase_date;
      if (formData.location) payload.location = formData.location;

      await collectionApi.addItem(payload);

      onSuccess();
      onClose();

      // Reset form
      setFormData({
        media_condition: Condition.NEAR_MINT,
        sleeve_condition: Condition.NEAR_MINT,
        purchase_price: '',
        purchase_currency: preferences?.currency || 'USD',
        purchase_date: '',
        location: '',
      });
    } catch (err: any) {
      console.error('Failed to add to collection:', err);

      // Handle validation errors (422) which return detail as an array
      let errorMessage = 'Failed to add to collection';
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          // Pydantic validation error format
          errorMessage = detail.map((e: any) => {
            const field = e.loc ? e.loc.join('.') : 'unknown';
            return `${field}: ${e.msg}`;
          }).join(', ');
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Add to Collection"
      size="medium"
      contentClassName="add-to-collection-modal"
    >
      <form className="form" onSubmit={handleSubmit}>
        {error && <div className="form-error">{error}</div>}

        <div className="form-info" style={{ marginBottom: '1rem', padding: '0.75rem', background: '#2a2a2a', borderRadius: '4px' }}>
          <strong>Pressing:</strong> {pressingDescription}
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="media_condition">
              Media Condition <span className="required">*</span>
            </label>
            <select
              id="media_condition"
              name="media_condition"
              value={formData.media_condition}
              onChange={handleChange}
              required
            >
              {CONDITION_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
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
              {CONDITION_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
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
              min="0"
              step="0.01"
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
              readOnly
              aria-readonly="true"
            />
          </div>

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

        <div className="form-actions">
          <button type="button" onClick={onClose} className="btn-secondary" disabled={loading}>
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Adding...' : 'Add to Collection'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
