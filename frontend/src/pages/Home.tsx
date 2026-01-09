/**
 * Home page with collection statistics.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { collectionApi } from '@/api/services';
import { CollectionItemDetailResponse, CollectionStatistics, PlayedAlbumEntry } from '@/types/api';
import { Card, Loading, ErrorAlert, Icon } from '@/components/UI';
import { mdiEyeOutline } from '@mdi/js';
import { formatDecimal, parseLocaleNumber, formatDateTime } from '@/utils/format';
import { useViewControls } from '@/components/Layout/ViewControlsContext';
import './Home.css';

export function Home() {
  const [stats, setStats] = useState<CollectionStatistics | null>(null);
  const [latestAdditions, setLatestAdditions] = useState<CollectionItemDetailResponse[]>([]);
  const [playedYearItems, setPlayedYearItems] = useState<PlayedAlbumEntry[]>([]);
  const [playedYearTotal, setPlayedYearTotal] = useState(0);
  const [playedYearLoading, setPlayedYearLoading] = useState(false);
  const [playedYearError, setPlayedYearError] = useState<string | null>(null);
  const [playedYearPage, setPlayedYearPage] = useState(1);
  const [playedYearPageSize, setPlayedYearPageSize] = useState(50);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { setControls } = useViewControls();
  const navigate = useNavigate();
  const currentYear = new Date().getFullYear();
  const playedYearTotalPages = Math.max(1, Math.ceil(playedYearTotal / playedYearPageSize));

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
    const fetchPlayedYear = async () => {
      try {
        setPlayedYearLoading(true);
        setPlayedYearError(null);
        const response = await collectionApi.getPlayedAlbumsYtd({
          year: currentYear,
          limit: playedYearPageSize,
          offset: (playedYearPage - 1) * playedYearPageSize,
        });
        setPlayedYearItems(response.items || []);
        setPlayedYearTotal(response.total || 0);
      } catch (err: any) {
        setPlayedYearError(err.response?.data?.detail || 'Failed to load played albums');
      } finally {
        setPlayedYearLoading(false);
      }
    };

    fetchPlayedYear();
  }, [currentYear, playedYearPage, playedYearPageSize]);

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

  const isExcludedArtist = (name: string) => name.trim().toLowerCase() === 'various';
  const topArtists = (stats?.top_artists || [])
    .filter((entry) => entry.collected_count > 1)
    .filter((entry) => !isExcludedArtist(entry.artist_name));
  const topAlbums = (stats?.top_albums || [])
    .filter((entry) => entry.collected_count > 1)
    .filter((entry) => !isExcludedArtist(entry.artist_name));

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

          <Card className="latest-addition-card top-ten-card">
            <div className="top-ten">
              <div className="top-ten-header">TOP 10 ARTISTS (ALL USERS)</div>
              {topArtists.length > 0 ? (
                <div className="top-ten-table">
                  <div className="top-ten-row top-ten-row-header">
                    <span>#</span>
                    <span>Artist</span>
                    <span>Collected</span>
                    <span />
                  </div>
                  {topArtists.map((entry, index) => (
                    <div key={entry.artist_id} className="top-ten-row">
                      <span>{index + 1}</span>
                      <span className="top-ten-name">{entry.artist_name}</span>
                      <span>{entry.collected_count}</span>
                      <button
                        type="button"
                        className="top-ten-view"
                        onClick={() => navigate('/artists', { state: { selectedArtistId: entry.artist_id } })}
                        aria-label={`View ${entry.artist_name}`}
                        title="View artist"
                      >
                        <Icon path={mdiEyeOutline} size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="top-ten-empty">Not enough shared collection data yet.</div>
              )}
            </div>
          </Card>

          <Card className="latest-addition-card top-ten-card">
            <div className="top-ten">
              <div className="top-ten-header">TOP 10 ALBUMS (ALL USERS)</div>
              {topAlbums.length > 0 ? (
                <div className="top-ten-table">
                  <div className="top-ten-row top-ten-row-header top-ten-row-album">
                    <span>#</span>
                    <span>Album</span>
                    <span>Artist</span>
                    <span>Collected</span>
                    <span />
                  </div>
                  {topAlbums.map((entry, index) => (
                    <div key={entry.album_id} className="top-ten-row top-ten-row-album">
                      <span>{index + 1}</span>
                      <span className="top-ten-name">{entry.album_title}</span>
                      <span className="top-ten-name">{entry.artist_name}</span>
                      <span>{entry.collected_count}</span>
                      <button
                        type="button"
                        className="top-ten-view"
                        onClick={() => navigate('/albums', { state: { selectedAlbumId: entry.album_id } })}
                        aria-label={`View ${entry.album_title}`}
                        title="View album"
                      >
                        <Icon path={mdiEyeOutline} size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="top-ten-empty">Not enough shared collection data yet.</div>
              )}
            </div>
          </Card>
        </div>
      )}

      <div className="played-year-section">
        <Card className="played-year-card">
          <div className="played-year-header">
            <h2>PLAYED THIS YEAR</h2>
            <span>{playedYearTotal} albums</span>
          </div>
          {playedYearLoading && (
            <div className="played-year-status">Loading plays...</div>
          )}
          {playedYearError && !playedYearLoading && (
            <div className="played-year-status played-year-error">{playedYearError}</div>
          )}
          {!playedYearLoading && !playedYearError && playedYearItems.length === 0 && (
            <div className="played-year-status">No plays logged yet this year.</div>
          )}
          {!playedYearLoading && !playedYearError && playedYearItems.length > 0 && (
            <div className="played-year-table">
              <div className="played-year-row played-year-header-row">
                <span>#</span>
                <span>Plays YTD</span>
                <span>Artist</span>
                <span>Album</span>
                <span>Last Played</span>
              </div>
              {playedYearItems.map((entry, index) => (
                <div key={`${entry.album_id}-${index}`} className="played-year-row">
                  <span>{(playedYearPage - 1) * playedYearPageSize + index + 1}</span>
                  <span>{entry.play_count_ytd}</span>
                  <span className="played-year-name">{entry.artist_name}</span>
                  <span className="played-year-name">{entry.album_title}</span>
                  <span>{formatDateTime(entry.last_played_at || undefined)}</span>
                </div>
              ))}
            </div>
          )}
          {playedYearTotalPages > 1 && (
            <div className="played-year-pagination">
              <div className="pagination-controls">
                <button
                  onClick={() => setPlayedYearPage((prev) => Math.max(1, prev - 1))}
                  disabled={playedYearPage === 1}
                  className="pagination-button"
                >
                  Previous
                </button>
                <div className="pagination-info">
                  Page {playedYearPage} of {playedYearTotalPages}
                </div>
                <button
                  onClick={() => setPlayedYearPage((prev) => Math.min(playedYearTotalPages, prev + 1))}
                  disabled={playedYearPage === playedYearTotalPages}
                  className="pagination-button"
                >
                  Next
                </button>
              </div>
              <div className="items-per-page">
                <span>Per page</span>
                <select
                  value={playedYearPageSize}
                  onChange={(e) => {
                    setPlayedYearPageSize(Number(e.target.value));
                    setPlayedYearPage(1);
                  }}
                >
                  {[25, 50, 100, 200].map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
