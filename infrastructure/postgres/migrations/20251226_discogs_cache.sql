-- Migration: Add Discogs cache tables
-- Created: 2025-12-26
-- Purpose: Implement API-level caching for Discogs master releases to avoid rate limits

-- Table: discogs_cache_pages
-- Stores paginated master release lists with 24-hour TTL
CREATE TABLE IF NOT EXISTS discogs_cache_pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,  -- Format: 'master_releases:{master_id}:page:{page}:per_page:{per_page}'
    master_id INTEGER NOT NULL,
    page INTEGER NOT NULL,
    per_page INTEGER NOT NULL,
    response_data JSONB NOT NULL,  -- Stores: { items: [...], pagination: {...} }
    cached_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours'),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient cache lookups and cleanup
CREATE INDEX IF NOT EXISTS idx_discogs_cache_pages_key ON discogs_cache_pages(cache_key);
CREATE INDEX IF NOT EXISTS idx_discogs_cache_pages_master ON discogs_cache_pages(master_id);
CREATE INDEX IF NOT EXISTS idx_discogs_cache_pages_expires ON discogs_cache_pages(expires_at);

-- Table: discogs_cache_releases
-- Stores individual release details with 7-day TTL
CREATE TABLE IF NOT EXISTS discogs_cache_releases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    release_id INTEGER UNIQUE NOT NULL,
    release_data JSONB NOT NULL,  -- Full DiscogsReleaseDetails
    cached_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days'),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient cache lookups and cleanup
CREATE INDEX IF NOT EXISTS idx_discogs_cache_releases_id ON discogs_cache_releases(release_id);
CREATE INDEX IF NOT EXISTS idx_discogs_cache_releases_expires ON discogs_cache_releases(expires_at);

-- Comments for documentation
COMMENT ON TABLE discogs_cache_pages IS 'Caches paginated Discogs master release lists to avoid API rate limits';
COMMENT ON TABLE discogs_cache_releases IS 'Caches individual Discogs release details to avoid API rate limits';
COMMENT ON COLUMN discogs_cache_pages.cache_key IS 'Unique key format: master_releases:{master_id}:page:{page}:per_page:{per_page}';
COMMENT ON COLUMN discogs_cache_pages.expires_at IS 'Automatic expiration after 24 hours for page cache';
COMMENT ON COLUMN discogs_cache_releases.expires_at IS 'Automatic expiration after 7 days for release cache';
