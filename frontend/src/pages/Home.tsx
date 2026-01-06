/**
 * Home page with collection statistics.
 */

import { useState, useEffect } from 'react';
import { collectionApi } from '@/api/services';
import { CollectionItemDetailResponse, CollectionStatistics } from '@/types/api';
import { Card, Loading, ErrorAlert } from '@/components/UI';
import { formatDecimal, parseLocaleNumber } from '@/utils/format';
import { useViewControls } from '@/components/Layout/ViewControlsContext';
import './Home.css';

export function Home() {
  const [stats, setStats] = useState<CollectionStatistics | null>(null);
  const [latestAdditions, setLatestAdditions] = useState<CollectionItemDetailResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { setControls } = useViewControls();

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await collectionApi.getStatistics();
      setStats(data);
      try {
        const latest = await collectionApi.getCollectionWithDetails({
          sort_by: 'date_added_desc',
          limit: 2,
          offset: 0,
        });
        setLatestAdditions(latest.items || []);
      } catch (latestErr) {
        console.error('Failed to load latest addition:', latestErr);
        setLatestAdditions([]);
      }
    } catch (err: any) {
      // Handle validation errors (422) which have detail as an array
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((e: any) => e.msg).join(', ') || 'Validation error');
      } else if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Failed to load statistics');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    setControls(null);
  }, [setControls]);

  if (loading) {
    return <Loading message="Loading your collection statistics..." />;
  }

  if (error) {
    return <ErrorAlert message={error} onRetry={fetchStats} />;
  }

  const formatPrice = (price: number | undefined, currency: string | undefined) => {
    if (price === null || price === undefined) return '-';
    const numPrice = typeof price === 'string' ? parseLocaleNumber(price) : price;
    if (numPrice === null) return '-';
    if (Number.isNaN(numPrice)) return '-';
    return `${currency || stats?.currency || 'USD'} ${formatDecimal(numPrice)}`;
  };

  const formatEstimatedPriceStack = (item: CollectionItemDetailResponse) => {
    const marketData = item.market_data;

    if (!marketData || marketData.median_value === null) {
      return <span className="latest-addition-value">-</span>;
    }

    const currency = marketData.currency || 'USD';
    const minPrice = marketData.min_value !== null ? formatDecimal(marketData.min_value) : '-';
    const medianPrice = marketData.median_value !== null ? formatDecimal(marketData.median_value) : '-';
    const maxPrice = marketData.max_value !== null ? formatDecimal(marketData.max_value) : '-';

    return (
      <div className="latest-addition-price-row">
        <span className="latest-addition-price-line">Min: {currency} {minPrice}</span>
        <span className="latest-addition-price-line latest-addition-price-median">Avg: {currency} {medianPrice}</span>
        <span className="latest-addition-price-line">Max: {currency} {maxPrice}</span>
      </div>
    );
  };

  return (
    <div className="home">
      <div className="home-header">
        <h1>Welcome to MyCousinVinyl</h1>
        <p>Your personal vinyl collection manager</p>
      </div>

      {stats && (
        <div className="stats-grid">
          <Card className="stat-card-tall stat-card-albums">
            <div className="stat-card">
              <div className="stat-value">{stats.total_albums}</div>
              <div className="stat-label">Albums in Collection</div>
            </div>
          </Card>

          <Card className="stat-summary-card stat-card-portrait stat-card-purchase-summary">
            <div className="stat-summary">
              <div className="stat-summary-title">Purchase Summary</div>
              <div className="stat-summary-grid stat-summary-grid-split">
                <div className="stat-summary-column">
                  <div className="stat-summary-item">
                    <div className="stat-summary-label">Average Purchase</div>
                    <div className="stat-summary-value">
                      {stats.currency} {formatDecimal(stats.avg_value)}
                    </div>
                  </div>
                  <div className="stat-summary-item">
                    <div className="stat-summary-label">Most Expensive Purchase</div>
                    <div className="stat-summary-value">
                      {stats.currency} {formatDecimal(stats.max_value)}
                    </div>
                  </div>
                </div>
                <div className="stat-summary-item stat-summary-total">
                  <div className="stat-summary-label">Total Purchase Value</div>
                  <div className="stat-summary-value stat-value">
                    {stats.currency} {formatDecimal(stats.total_purchase_price)}
                  </div>
                </div>
              </div>
            </div>
          </Card>

          <Card className="stat-summary-card stat-card-portrait stat-card-collection-summary">
            <div className="stat-summary">
              <div className="stat-summary-title">Collection Value</div>
              <div className="stat-summary-grid stat-summary-grid-split">
                <div className="stat-summary-column">
                  <div className="stat-summary-item">
                    <div className="stat-summary-label">Low Est. Sales Price</div>
                    <div className="stat-summary-value">
                      {stats.currency} {formatDecimal(stats.low_est_sales_price)}
                    </div>
                  </div>
                  <div className="stat-summary-item">
                    <div className="stat-summary-label">High Est. Sales Price</div>
                    <div className="stat-summary-value">
                      {stats.currency} {formatDecimal(stats.high_est_sales_price)}
                    </div>
                  </div>
                </div>
                <div className="stat-summary-item stat-summary-total">
                  <div className="stat-summary-label">Avg. Est. Sales Price</div>
                  <div className="stat-summary-value stat-value">
                    {stats.currency} {formatDecimal(stats.avg_est_sales_price)}
                  </div>
                </div>
              </div>
            </div>
          </Card>

          <Card className="stat-card-desktop">
            <div className="stat-card">
              <div className="stat-value">
                {stats.currency} {formatDecimal(stats.total_purchase_price)}
              </div>
              <div className="stat-label">Total Purchase Value</div>
            </div>
          </Card>

          <Card className="stat-card-desktop">
            <div className="stat-card">
              <div className="stat-value">
                {stats.currency} {formatDecimal(stats.avg_value)}
              </div>
              <div className="stat-label">Average Purchase</div>
            </div>
          </Card>

          <Card className="stat-card-desktop">
            <div className="stat-card">
              <div className="stat-value">
                {stats.currency} {formatDecimal(stats.max_value)}
              </div>
              <div className="stat-label">Most Expensive Purchase</div>
            </div>
          </Card>

          <Card className="stat-card-desktop">
            <div className="stat-card">
              <div className="stat-value">
                {stats.currency} {formatDecimal(stats.low_est_sales_price)}
              </div>
              <div className="stat-label">Low Est. Sales Price</div>
            </div>
          </Card>

          <Card className="stat-card-desktop">
            <div className="stat-card">
              <div className="stat-value">
                {stats.currency} {formatDecimal(stats.avg_est_sales_price)}
              </div>
              <div className="stat-label">Avg. Est. Sales Price</div>
            </div>
          </Card>

          <Card className="stat-card-desktop">
            <div className="stat-card">
              <div className="stat-value">
                {stats.currency} {formatDecimal(stats.high_est_sales_price)}
              </div>
              <div className="stat-label">High Est. Sales Price</div>
            </div>
          </Card>

          {[
            { label: 'Latest Addition', item: latestAdditions[0], className: 'latest-addition-primary' },
            { label: 'The One Before', item: latestAdditions[1], className: 'latest-addition-secondary' },
          ].map(({ label, item, className }) => (
            <Card key={label} className={`latest-addition-card ${className}`}>
              <div className="latest-addition">
                <div className="latest-addition-header">{label}</div>
                {item ? (
                  <div className="latest-addition-body">
                    <div className="latest-addition-image">
                      {item.pressing_image_url || item.album.image_url ? (
                        <img
                          src={item.pressing_image_url || item.album.image_url}
                          alt={`${item.album.title} cover`}
                        />
                      ) : (
                        <div className="latest-addition-placeholder">No cover</div>
                      )}
                    </div>
                    <div className="latest-addition-details">
                      <div className="latest-addition-field">
                        <div className="latest-addition-label">Artist</div>
                        <div className="latest-addition-value">{item.artist.name}</div>
                      </div>
                      <div className="latest-addition-field">
                        <div className="latest-addition-label">Album</div>
                        <div className="latest-addition-value">{item.album.title}</div>
                      </div>
                      <div className="latest-addition-field">
                        <div className="latest-addition-label">Purchase Price</div>
                        <div className="latest-addition-value">
                          {formatPrice(item.purchase_price, item.purchase_currency)}
                        </div>
                      </div>
                    </div>
                    <div className="latest-addition-estimates">
                      <div className="latest-addition-label">Est. Sales Price</div>
                      {formatEstimatedPriceStack(item)}
                    </div>
                  </div>
                ) : (
                  <div className="latest-addition-empty">No additions yet.</div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

    </div>
  );
}
