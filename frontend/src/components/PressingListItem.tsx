/**
 * Pressing list item component for displaying pressing details with actions.
 */

import { PressingResponse, UserOwnerInfo } from '@/types/api';
import { Icon } from '@/components/UI';
import { OwnersGrid } from '@/components/CollectionSharing';
import { mdiPlus } from '@mdi/js';
import './UI/Card.css';
import '../styles/Table.css';

interface PressingListItemProps {
  pressing: PressingResponse;
  onAddToCollection: (pressingId: string) => void;
  fallbackImageUrl?: string;
  owners?: UserOwnerInfo[];
  currentUserId?: string;
}

export function PressingListItem({
  pressing,
  onAddToCollection,
  fallbackImageUrl,
  owners,
  currentUserId,
}: PressingListItemProps) {
  const getCountryName = (code: string | undefined): string => {
    if (!code) return '-';
    const countries: Record<string, string> = {
      'US': 'United States',
      'GB': 'United Kingdom',
      'CA': 'Canada',
      'AU': 'Australia',
      'DE': 'Germany',
      'FR': 'France',
      'IT': 'Italy',
      'ES': 'Spain',
      'JP': 'Japan',
      'KR': 'South Korea',
      'CN': 'China',
      'BR': 'Brazil',
      'MX': 'Mexico',
      'AR': 'Argentina',
      'SE': 'Sweden',
      'NO': 'Norway',
      'DK': 'Denmark',
      'FI': 'Finland',
      'NL': 'Netherlands',
      'BE': 'Belgium',
      'AT': 'Austria',
      'CH': 'Switzerland',
      'IE': 'Ireland',
      'NZ': 'New Zealand',
      'ZA': 'South Africa',
      'IN': 'India',
      'RU': 'Russia',
      'PL': 'Poland',
      'CZ': 'Czech Republic',
      'GR': 'Greece',
      'PT': 'Portugal',
      'IS': 'Iceland',
    };
    return countries[code] || code;
  };

  const country = getCountryName(pressing.country ?? pressing.pressing_country);
  const releaseYear = pressing.release_year ?? pressing.pressing_year ?? '-';
  const vinylColor = pressing.vinyl_color ?? '-';
  const editionType = pressing.edition_type ?? '-';
  const notes = pressing.notes || '-';
  const formatDetails = `${pressing.size_inches} ${pressing.format} at ${pressing.speed_rpm} RPM`;
  const coverUrl = pressing.image_url || fallbackImageUrl;
  const discCount = pressing.disc_count ?? '-';
  const pressingPlant = pressing.pressing_plant || '-';
  const masteringEngineer = pressing.mastering_engineer || '-';
  const masteringStudio = pressing.mastering_studio || '-';
  const labelDesign = pressing.label_design || '-';
  const barcode = pressing.barcode || '-';
  const discogsReleaseId = pressing.discogs_release_id || '-';
  const discogsMasterId = pressing.discogs_master_id || '-';

  return (
    <div className="pressing-list-item" style={{
      padding: '1rem',
      marginBottom: '0.5rem',
      background: '#2a2a2a',
      borderRadius: '4px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      border: '1px solid var(--color-border-strong)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 1, minWidth: 0 }}>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '0.5rem',
          flexShrink: 0
        }}>
          <div style={{
            position: 'relative',
            width: '56px',
            height: '56px'
          }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '6px',
              border: '1px solid var(--color-border-strong)',
              background: 'var(--color-background-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              overflow: 'hidden',
              color: '#666',
              fontSize: '0.75rem'
            }}>
              {coverUrl ? (
                <img src={coverUrl} alt="Pressing cover" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              ) : (
                <span>No cover</span>
              )}
            </div>
          </div>
          {owners && currentUserId && (
            <OwnersGrid
              owners={owners}
              currentUserId={currentUserId}
              showEmpty
              className="owners-grid-large"
            />
          )}
        </div>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
          gap: '0.5rem',
          fontSize: '0.875rem',
          color: '#ccc',
          flex: 1
        }}>
          <div><strong>Format:</strong> {formatDetails}</div>
          <div><strong>Disc Count:</strong> {discCount}</div>
          <div><strong>Release Year:</strong> {releaseYear}</div>
          <div><strong>Country:</strong> {country}</div>
          <div><strong>Pressing Plant:</strong> {pressingPlant}</div>
          <div><strong>Mastering Engineer:</strong> {masteringEngineer}</div>
          <div><strong>Mastering Studio:</strong> {masteringStudio}</div>
          <div><strong>Vinyl Color:</strong> {vinylColor}</div>
          <div><strong>Label Design:</strong> {labelDesign}</div>
          <div><strong>Edition Type:</strong> {editionType}</div>
          <div><strong>Discogs Release ID:</strong> {discogsReleaseId}</div>
          <div><strong>Discogs Master ID:</strong> {discogsMasterId}</div>
          <div style={{ gridColumn: '1 / span 3', minWidth: 0 }}>
            <strong>Barcode / Identifiers:</strong>{' '}
            <span style={{
              display: 'inline-block',
              maxWidth: '100%',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              verticalAlign: 'bottom'
            }}>
              {barcode}
            </span>
          </div>
          <div style={{ gridColumn: '1 / span 3', minWidth: 0 }}>
            <strong>Notes:</strong>{' '}
            <span style={{
              display: 'inline-block',
              maxWidth: '100%',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              verticalAlign: 'bottom'
            }}>
              {notes}
            </span>
          </div>
        </div>
      </div>
      <div style={{
        marginLeft: '1rem',
        display: 'flex',
        alignItems: 'center',
        height: '100%'
      }}>
        <button
          className="btn-action btn-success"
          onClick={() => onAddToCollection(pressing.id)}
          title="Add to Collection"
          aria-label="Add to Collection"
        >
          <Icon path={mdiPlus} />
        </button>
      </div>
    </div>
  );
}
