-- ============================================================================
-- MyCousinVinyl Database Schema
-- PostgreSQL initialization script for vinyl collection management
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For trigram similarity search

-- ============================================================================
-- ENUM TYPES
-- ============================================================================

CREATE TYPE vinyl_format AS ENUM ('LP', 'EP', 'Single', 'Maxi', 'CD');

CREATE TYPE vinyl_speed AS ENUM ('33 1/3', '45', '78', 'N/A');

CREATE TYPE vinyl_size AS ENUM ('7"', '10"', '12"', 'CD');

CREATE TYPE condition_grade AS ENUM ('Mint', 'NM', 'VG+', 'VG', 'G', 'P');

CREATE TYPE media_type AS ENUM ('Image', 'Video');

CREATE TYPE external_source AS ENUM (
    'Discogs',
    'MusicBrainz',
    'Spotify',
    'Apple Music'
);

CREATE TYPE data_source AS ENUM ('User', 'Import', 'API');

CREATE TYPE verification_status AS ENUM (
    'Verified',
    'Community',
    'Unverified'
);

-- ============================================================================
-- LOOKUP TABLES
-- ============================================================================

-- Genres lookup table
CREATE TABLE genres (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_order INT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Styles lookup table (styles can belong to genres)
CREATE TABLE styles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    genre_id UUID REFERENCES genres(id) ON DELETE SET NULL,
    display_order INT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Countries lookup table (ISO 3166-1 alpha-2)
CREATE TABLE countries (
    code VARCHAR(2) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_order INT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Artist types lookup table
CREATE TABLE artist_types (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_order INT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Release types lookup table
CREATE TABLE release_types (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_order INT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Edition types lookup table
CREATE TABLE edition_types (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_order INT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Sleeve types lookup table
CREATE TABLE sleeve_types (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_order INT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CORE ENTITY TABLES
-- ============================================================================

-- Artists table
CREATE TABLE artists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    sort_name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'Person' REFERENCES artist_types(code) ON DELETE RESTRICT,
    country VARCHAR(2) REFERENCES countries(code) ON DELETE SET NULL,
    active_years VARCHAR(50),
    disambiguation VARCHAR(500),
    bio TEXT,
    aliases TEXT[],
    notes TEXT,
    image_url TEXT,
    discogs_id INT,

    -- System metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    data_source data_source DEFAULT 'User',
    verification_status verification_status DEFAULT 'Unverified'
);

-- Albums table
CREATE TABLE albums (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    primary_artist_id UUID NOT NULL REFERENCES artists(id) ON DELETE RESTRICT,
    release_type VARCHAR(50) NOT NULL DEFAULT 'Studio' REFERENCES release_types(code) ON DELETE RESTRICT,
    original_release_year INT,
    original_release_date DATE,
    country_of_origin VARCHAR(2) REFERENCES countries(code) ON DELETE SET NULL,
    label VARCHAR(255),
    catalog_number_base VARCHAR(100),
    description TEXT,
    image_url TEXT,
    original_release_id UUID REFERENCES albums(id) ON DELETE SET NULL,
    discogs_id INT,

    -- Full-text search
    search_vector tsvector,

    -- System metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    data_source data_source DEFAULT 'User',
    verification_status verification_status DEFAULT 'Unverified',

    -- Business rules
    CONSTRAINT no_self_reference CHECK (id != original_release_id)
);

-- Tracks table
CREATE TABLE tracks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    album_id UUID NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    side VARCHAR(10) NOT NULL,
    position VARCHAR(10) NOT NULL,
    title VARCHAR(500) NOT NULL,
    duration INT,  -- Duration in seconds
    songwriters TEXT[],
    notes TEXT,

    -- System metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Business rules
    UNIQUE (album_id, side, position)
);

-- Pressings table
CREATE TABLE pressings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    album_id UUID NOT NULL REFERENCES albums(id) ON DELETE RESTRICT,
    format vinyl_format NOT NULL,
    speed_rpm vinyl_speed NOT NULL,
    size_inches vinyl_size NOT NULL,
    disc_count INT NOT NULL DEFAULT 1 CHECK (disc_count >= 1),
    pressing_country VARCHAR(2) REFERENCES countries(code) ON DELETE SET NULL,
    pressing_year INT,
    pressing_plant VARCHAR(255),
    mastering_engineer VARCHAR(255),
    mastering_studio VARCHAR(255),
    vinyl_color VARCHAR(100),
    label_design VARCHAR(255),
    image_url TEXT,
    edition_type VARCHAR(50) DEFAULT 'Standard' REFERENCES edition_types(code) ON DELETE RESTRICT,
    barcode TEXT,
    notes TEXT,
    discogs_release_id INT,
    discogs_master_id INT,
    master_title VARCHAR(500),

    -- System metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    data_source data_source DEFAULT 'User',
    verification_status verification_status DEFAULT 'Unverified'
);

-- Matrices (runout codes) table
CREATE TABLE matrices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pressing_id UUID NOT NULL REFERENCES pressings(id) ON DELETE CASCADE,
    side VARCHAR(10) NOT NULL,
    matrix_code VARCHAR(255),
    etchings TEXT,
    stamper_info VARCHAR(255),

    -- System metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Business rules
    UNIQUE (pressing_id, side)
);

-- Packaging table (one-to-one with pressing)
CREATE TABLE packaging (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pressing_id UUID NOT NULL UNIQUE REFERENCES pressings(id) ON DELETE CASCADE,
    sleeve_type VARCHAR(50) NOT NULL REFERENCES sleeve_types(code) ON DELETE RESTRICT,
    cover_artist VARCHAR(255),
    includes_inner_sleeve BOOLEAN DEFAULT FALSE,
    includes_insert BOOLEAN DEFAULT FALSE,
    includes_poster BOOLEAN DEFAULT FALSE,
    includes_obi BOOLEAN DEFAULT FALSE,
    stickers TEXT,
    notes TEXT,

    -- System metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Collection items table
CREATE TABLE collection_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    pressing_id UUID NOT NULL REFERENCES pressings(id) ON DELETE RESTRICT,
    media_condition condition_grade NOT NULL,
    sleeve_condition condition_grade NOT NULL,
    play_tested BOOLEAN DEFAULT FALSE,
    defect_notes TEXT,
    purchase_price DECIMAL(10, 2) CHECK (purchase_price >= 0),
    purchase_currency VARCHAR(3),
    purchase_date DATE,
    seller VARCHAR(255),
    storage_location VARCHAR(255),
    play_count INT DEFAULT 0 CHECK (play_count >= 0),
    last_played_date DATE,
    user_rating INT CHECK (user_rating >= 0 AND user_rating <= 5),
    user_notes TEXT,
    tags TEXT[],
    date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- System metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Per-user album play counts (overall)
CREATE TABLE user_album_plays (
    user_id UUID NOT NULL,
    album_id UUID NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    play_count INT DEFAULT 0 CHECK (play_count >= 0),
    last_played_at TIMESTAMP,

    -- System metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, album_id)
);

-- Per-user album play counts by year
CREATE TABLE user_album_play_years (
    user_id UUID NOT NULL,
    album_id UUID NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    year INT NOT NULL,
    play_count INT DEFAULT 0 CHECK (play_count >= 0),

    -- System metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, album_id, year)
);

-- Collection import jobs table
CREATE TABLE collection_imports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    filename TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'queued',
    total_rows INT NOT NULL DEFAULT 0,
    processed_rows INT NOT NULL DEFAULT 0,
    success_count INT NOT NULL DEFAULT 0,
    error_count INT NOT NULL DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_summary TEXT,
    options JSONB DEFAULT '{}'::jsonb,

    -- System metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Collection import rows table
CREATE TABLE collection_import_rows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    import_id UUID NOT NULL REFERENCES collection_imports(id) ON DELETE CASCADE,
    row_number INT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    raw_data JSONB DEFAULT '{}'::jsonb,
    discogs_release_id INTEGER,
    artist_id UUID REFERENCES artists(id) ON DELETE SET NULL,
    album_id UUID REFERENCES albums(id) ON DELETE SET NULL,
    pressing_id UUID REFERENCES pressings(id) ON DELETE SET NULL,
    collection_item_id UUID REFERENCES collection_items(id) ON DELETE SET NULL,
    error_message TEXT,

    -- System metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (import_id, row_number)
);

-- Media assets table
CREATE TABLE media_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    media_type media_type NOT NULL,
    url VARCHAR(1000) NOT NULL,
    description TEXT,
    uploaded_by_user BOOLEAN DEFAULT TRUE,

    -- System metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- External references table
CREATE TABLE external_references (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    source external_source NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    url VARCHAR(1000),

    -- System metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Business rules
    UNIQUE (entity_type, entity_id, source)
);

-- User preferences table
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY,
    currency VARCHAR(3) NOT NULL DEFAULT 'DKK',
    display_settings JSONB DEFAULT '{}'::jsonb,

    -- System metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- System settings table (global configuration)
CREATE TABLE system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- System logs table (admin-visible audit log)
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    user_name VARCHAR(255) NOT NULL,
    severity VARCHAR(10) NOT NULL,
    component VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT system_logs_severity_check CHECK (severity IN ('INFO', 'WARN', 'ERROR'))
);

-- Discogs OAuth request tokens (short-lived)
CREATE TABLE discogs_oauth_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    request_token TEXT NOT NULL UNIQUE,
    request_secret TEXT NOT NULL,
    state TEXT NOT NULL,
    redirect_uri TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- Discogs OAuth access tokens (per user)
CREATE TABLE discogs_user_tokens (
    user_id UUID PRIMARY KEY,
    access_token TEXT NOT NULL,
    access_secret TEXT,
    discogs_username TEXT NOT NULL,
    last_synced_at TIMESTAMP,

    -- System metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Discogs cache tables
CREATE TABLE discogs_cache_pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    master_id INTEGER NOT NULL,
    page INTEGER NOT NULL,
    per_page INTEGER NOT NULL,
    response_data JSONB NOT NULL,
    cached_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours'),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE discogs_cache_releases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    release_id INTEGER UNIQUE NOT NULL,
    release_data JSONB NOT NULL,
    cached_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days'),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- User follows table (collection sharing)
CREATE TABLE user_follows (
    follower_user_id UUID NOT NULL,
    followed_user_id UUID NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (follower_user_id, followed_user_id),
    CONSTRAINT no_self_follow CHECK (follower_user_id != followed_user_id)
);

-- Market data table (optional, Phase 10+)
CREATE TABLE market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pressing_id UUID NOT NULL UNIQUE REFERENCES pressings(id) ON DELETE CASCADE,
    min_value DECIMAL(10, 2),
    median_value DECIMAL(10, 2),
    max_value DECIMAL(10, 2),
    last_sold_price DECIMAL(10, 2),
    currency VARCHAR(3),
    availability_status VARCHAR(50),

    -- System metadata
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- JUNCTION TABLES (Many-to-Many Relationships)
-- ============================================================================

-- Album-Genre many-to-many
CREATE TABLE album_genres (
    album_id UUID NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    genre_id UUID NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY (album_id, genre_id)
);

-- Album-Style many-to-many
CREATE TABLE album_styles (
    album_id UUID NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    style_id UUID NOT NULL REFERENCES styles(id) ON DELETE CASCADE,
    PRIMARY KEY (album_id, style_id)
);

-- ============================================================================
-- OUTBOX TABLE (Transactional Outbox Pattern)
-- ============================================================================

-- Outbox events for reliable message publishing
CREATE TABLE outbox_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    event_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    aggregate_id UUID NOT NULL,
    aggregate_type VARCHAR(50) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    headers JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Full-text search indexes
CREATE INDEX idx_albums_search ON albums USING gin(search_vector);
CREATE INDEX idx_artists_name_trgm ON artists USING gin(name gin_trgm_ops);
CREATE INDEX idx_albums_title_trgm ON albums USING gin(title gin_trgm_ops);

-- Foreign key indexes (critical for joins)
CREATE INDEX idx_albums_primary_artist ON albums(primary_artist_id);
CREATE INDEX idx_albums_original_release ON albums(original_release_id);
CREATE INDEX idx_tracks_album ON tracks(album_id);
CREATE INDEX idx_pressings_album ON pressings(album_id);
CREATE INDEX idx_matrices_pressing ON matrices(pressing_id);
CREATE INDEX idx_packaging_pressing ON packaging(pressing_id);
CREATE INDEX idx_collection_items_user ON collection_items(user_id);
CREATE INDEX idx_collection_items_pressing ON collection_items(pressing_id);
CREATE INDEX idx_user_album_plays_user ON user_album_plays(user_id);
CREATE INDEX idx_user_album_plays_last_played ON user_album_plays(user_id, last_played_at DESC);
CREATE INDEX idx_user_album_play_years_user_year ON user_album_play_years(user_id, year);
CREATE INDEX idx_user_album_play_years_user_year_count ON user_album_play_years(user_id, year, play_count DESC, album_id);
CREATE INDEX idx_media_assets_entity ON media_assets(entity_type, entity_id);
CREATE INDEX idx_external_refs_entity ON external_references(entity_type, entity_id);
CREATE INDEX idx_discogs_cache_pages_key ON discogs_cache_pages(cache_key);
CREATE INDEX idx_discogs_cache_pages_master ON discogs_cache_pages(master_id);
CREATE INDEX idx_discogs_cache_pages_expires ON discogs_cache_pages(expires_at);
CREATE INDEX idx_discogs_cache_releases_id ON discogs_cache_releases(release_id);
CREATE INDEX idx_discogs_cache_releases_expires ON discogs_cache_releases(expires_at);
CREATE INDEX idx_user_follows_follower ON user_follows(follower_user_id);
CREATE INDEX idx_user_follows_followed ON user_follows(followed_user_id);
CREATE INDEX idx_system_logs_created_at ON system_logs(created_at DESC);
CREATE INDEX idx_system_logs_severity ON system_logs(severity);
CREATE INDEX idx_market_data_pressing_id ON market_data(pressing_id);
CREATE INDEX idx_market_data_updated_at ON market_data(updated_at);

-- Filtering and sorting indexes
CREATE INDEX idx_albums_year ON albums(original_release_year);
CREATE INDEX idx_albums_title ON albums(title);
CREATE INDEX idx_albums_release_type ON albums(release_type);
CREATE INDEX idx_artists_name ON artists(name);
CREATE INDEX idx_artists_sort_name ON artists(sort_name);
CREATE INDEX idx_pressings_country ON pressings(pressing_country);
CREATE INDEX idx_pressings_format ON pressings(format);
CREATE INDEX idx_pressings_year ON pressings(pressing_year);
CREATE INDEX idx_pressings_master_title ON pressings(master_title);
CREATE INDEX idx_pressings_discogs_release ON pressings(discogs_release_id);
CREATE INDEX idx_pressings_discogs_master ON pressings(discogs_master_id);
CREATE INDEX idx_collection_items_date_added ON collection_items(user_id, date_added DESC);
CREATE INDEX idx_collection_items_rating ON collection_items(user_id, user_rating DESC);
CREATE INDEX idx_collection_items_condition ON collection_items(user_id, media_condition);
CREATE INDEX idx_collection_imports_user ON collection_imports(user_id);
CREATE INDEX idx_collection_imports_status ON collection_imports(status);
CREATE INDEX idx_collection_import_rows_import ON collection_import_rows(import_id);
CREATE INDEX idx_collection_import_rows_status ON collection_import_rows(status);
CREATE INDEX idx_discogs_oauth_requests_user ON discogs_oauth_requests(user_id);
CREATE INDEX idx_discogs_oauth_requests_expires ON discogs_oauth_requests(expires_at);
CREATE INDEX idx_discogs_user_tokens_username ON discogs_user_tokens(discogs_username);

-- Outbox processing index
CREATE INDEX idx_outbox_unprocessed ON outbox_events(processed, created_at) WHERE NOT processed;
CREATE INDEX idx_outbox_aggregate ON outbox_events(aggregate_type, aggregate_id);

-- Lookup optimization
CREATE INDEX idx_genres_name ON genres(name);
CREATE INDEX idx_styles_name ON styles(name);
CREATE INDEX idx_styles_genre ON styles(genre_id);
CREATE INDEX idx_album_genres_album ON album_genres(album_id);
CREATE INDEX idx_album_genres_genre ON album_genres(genre_id);
CREATE INDEX idx_album_styles_album ON album_styles(album_id);
CREATE INDEX idx_album_styles_style ON album_styles(style_id);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to all tables with updated_at column
CREATE TRIGGER update_artists_updated_at
    BEFORE UPDATE ON artists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_albums_updated_at
    BEFORE UPDATE ON albums
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tracks_updated_at
    BEFORE UPDATE ON tracks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pressings_updated_at
    BEFORE UPDATE ON pressings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_matrices_updated_at
    BEFORE UPDATE ON matrices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_packaging_updated_at
    BEFORE UPDATE ON packaging
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collection_items_updated_at
    BEFORE UPDATE ON collection_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_album_plays_updated_at
    BEFORE UPDATE ON user_album_plays
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_album_play_years_updated_at
    BEFORE UPDATE ON user_album_play_years
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_media_assets_updated_at
    BEFORE UPDATE ON media_assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_external_references_updated_at
    BEFORE UPDATE ON external_references
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_settings_updated_at
    BEFORE UPDATE ON system_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_discogs_user_tokens_updated_at
    BEFORE UPDATE ON discogs_user_tokens
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_market_data_updated_at
    BEFORE UPDATE ON market_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collection_imports_updated_at
    BEFORE UPDATE ON collection_imports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collection_import_rows_updated_at
    BEFORE UPDATE ON collection_import_rows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to auto-update album search vector
CREATE OR REPLACE FUNCTION albums_search_vector_update()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(NEW.label, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER albums_search_vector_update
    BEFORE INSERT OR UPDATE ON albums
    FOR EACH ROW EXECUTE FUNCTION albums_search_vector_update();

-- ============================================================================
-- SEED DATA
-- ============================================================================

-- Insert common countries (ISO 3166-1 alpha-3)
-- ISO 3166-1 alpha-2 country codes (2-letter standard)
INSERT INTO countries (code, name, display_order) VALUES
    ('US', 'United States', 1),
    ('GB', 'United Kingdom', 2),
    ('DE', 'Germany', 3),
    ('FR', 'France', 4),
    ('JP', 'Japan', 5),
    ('CA', 'Canada', 6),
    ('AU', 'Australia', 7),
    ('NL', 'Netherlands', 8),
    ('SE', 'Sweden', 9),
    ('IT', 'Italy', 10),
    ('ES', 'Spain', 11),
    ('NO', 'Norway', 12),
    ('DK', 'Denmark', 13),
    ('BE', 'Belgium', 14),
    ('AT', 'Austria', 15),
    ('CH', 'Switzerland', 16),
    ('IE', 'Ireland', 17),
    ('PL', 'Poland', 18),
    ('BR', 'Brazil', 19),
    ('MX', 'Mexico', 20),
    ('AR', 'Argentina', 21),
    ('CL', 'Chile', 22),
    ('NZ', 'New Zealand', 23),
    ('ZA', 'South Africa', 24),
    ('KR', 'South Korea', 25),
    ('CN', 'China', 26),
    ('IN', 'India', 27),
    ('RU', 'Russia', 28),
    ('CZ', 'Czech Republic', 29),
    ('HU', 'Hungary', 30)
ON CONFLICT (code) DO NOTHING;

-- Insert artist types
INSERT INTO artist_types (code, name, display_order) VALUES
    ('Person', 'Person', 1),
    ('Group', 'Group', 2)
ON CONFLICT (code) DO NOTHING;

-- Insert release types
INSERT INTO release_types (code, name, display_order) VALUES
    ('Studio', 'Studio', 1),
    ('Live', 'Live', 2),
    ('Compilation', 'Compilation', 3),
    ('EP', 'EP', 4),
    ('Single', 'Single', 5),
    ('Box Set', 'Box Set', 6)
ON CONFLICT (code) DO NOTHING;

-- Insert edition types
INSERT INTO edition_types (code, name, display_order) VALUES
    ('Standard', 'Standard', 1),
    ('Limited', 'Limited', 2),
    ('Numbered', 'Numbered', 3),
    ('Reissue', 'Reissue', 4),
    ('Remaster', 'Remaster', 5)
ON CONFLICT (code) DO NOTHING;

-- Insert sleeve types
INSERT INTO sleeve_types (code, name, display_order) VALUES
    ('Single', 'Single', 1),
    ('Gatefold', 'Gatefold', 2),
    ('Box', 'Box', 3)
ON CONFLICT (code) DO NOTHING;

-- Insert default system settings
INSERT INTO system_settings (key, value) VALUES
    ('log_retention_days', '60')
ON CONFLICT (key) DO NOTHING;

-- Insert common music genres
INSERT INTO genres (name, display_order) VALUES
    ('Rock', 1),
    ('Pop', 2),
    ('Jazz', 3),
    ('Classical', 4),
    ('Electronic', 5),
    ('Hip Hop', 6),
    ('R&B', 7),
    ('Country', 8),
    ('Blues', 9),
    ('Folk', 10),
    ('Metal', 11),
    ('Punk', 12),
    ('Reggae', 13),
    ('Soul', 14),
    ('Funk', 15),
    ('Disco', 16),
    ('House', 17),
    ('Techno', 18),
    ('Ambient', 19),
    ('Experimental', 20)
ON CONFLICT (name) DO NOTHING;

-- Insert common music styles (can be expanded)
INSERT INTO styles (name, genre_id, display_order)
SELECT 'Progressive Rock', g.id, 1 FROM genres g WHERE g.name = 'Rock'
UNION ALL
SELECT 'Hard Rock', g.id, 2 FROM genres g WHERE g.name = 'Rock'
UNION ALL
SELECT 'Alternative Rock', g.id, 3 FROM genres g WHERE g.name = 'Rock'
UNION ALL
SELECT 'Indie Rock', g.id, 4 FROM genres g WHERE g.name = 'Rock'
UNION ALL
SELECT 'Psychedelic Rock', g.id, 5 FROM genres g WHERE g.name = 'Rock'
UNION ALL
SELECT 'Bebop', g.id, 1 FROM genres g WHERE g.name = 'Jazz'
UNION ALL
SELECT 'Free Jazz', g.id, 2 FROM genres g WHERE g.name = 'Jazz'
UNION ALL
SELECT 'Fusion', g.id, 3 FROM genres g WHERE g.name = 'Jazz'
UNION ALL
SELECT 'Synth-pop', g.id, 1 FROM genres g WHERE g.name = 'Pop'
UNION ALL
SELECT 'Dance-pop', g.id, 2 FROM genres g WHERE g.name = 'Pop'
UNION ALL
SELECT 'Thrash Metal', g.id, 1 FROM genres g WHERE g.name = 'Metal'
UNION ALL
SELECT 'Death Metal', g.id, 2 FROM genres g WHERE g.name = 'Metal'
UNION ALL
SELECT 'Black Metal', g.id, 3 FROM genres g WHERE g.name = 'Metal'
UNION ALL
SELECT 'Deep House', g.id, 1 FROM genres g WHERE g.name = 'House'
UNION ALL
SELECT 'Tech House', g.id, 2 FROM genres g WHERE g.name = 'House'
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- GRANTS (if needed for specific users)
-- ============================================================================

-- Uncomment and modify if you need specific user permissions
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mycousinvinyl_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mycousinvinyl_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO mycousinvinyl_app;

-- ============================================================================
-- COMMENTS (Database Documentation)
-- ============================================================================

COMMENT ON TABLE artists IS 'Musical artists and groups';
COMMENT ON TABLE albums IS 'Musical releases (independent of physical pressings)';
COMMENT ON TABLE tracks IS 'Individual tracks on albums';
COMMENT ON TABLE pressings IS 'Physical vinyl pressings of albums';
COMMENT ON TABLE matrices IS 'Matrix/runout codes etched on vinyl records';
COMMENT ON TABLE packaging IS 'Packaging details for pressings';
COMMENT ON TABLE collection_items IS 'User-owned vinyl records';
COMMENT ON TABLE user_album_plays IS 'Per-user album play counts and last played timestamp';
COMMENT ON TABLE user_album_play_years IS 'Per-user album play counts by year';
COMMENT ON TABLE collection_imports IS 'Imports of external collection data (Discogs CSV)';
COMMENT ON TABLE collection_import_rows IS 'Row-level status for collection imports';
COMMENT ON TABLE media_assets IS 'Images and videos associated with entities';
COMMENT ON TABLE external_references IS 'Links to external databases (Discogs, MusicBrainz, etc.)';
COMMENT ON TABLE user_preferences IS 'User settings and preferences';
COMMENT ON TABLE system_settings IS 'Global application settings';
COMMENT ON TABLE system_logs IS 'System audit log entries';
COMMENT ON TABLE discogs_oauth_requests IS 'Short-lived OAuth request tokens for Discogs user auth';
COMMENT ON TABLE discogs_user_tokens IS 'Discogs OAuth or PAT tokens per user';
COMMENT ON TABLE market_data IS 'Market pricing data for pressings';
COMMENT ON TABLE discogs_cache_pages IS 'Caches paginated Discogs master release lists to avoid API rate limits';
COMMENT ON TABLE discogs_cache_releases IS 'Caches individual Discogs release details to avoid API rate limits';
COMMENT ON TABLE genres IS 'Musical genre classifications';
COMMENT ON TABLE styles IS 'Musical style classifications (sub-genres)';
COMMENT ON TABLE countries IS 'ISO 3166-1 alpha-3 country codes';
COMMENT ON TABLE artist_types IS 'Lookup values for artist types';
COMMENT ON TABLE release_types IS 'Lookup values for album release types';
COMMENT ON TABLE edition_types IS 'Lookup values for pressing edition types';
COMMENT ON TABLE sleeve_types IS 'Lookup values for sleeve/jacket types';
COMMENT ON TABLE outbox_events IS 'Transactional outbox for reliable event publishing';

COMMENT ON COLUMN collection_items.user_id IS 'User who owns this item (references Azure AD user ID)';
COMMENT ON COLUMN collection_items.media_condition IS 'Condition of the vinyl disc (Goldmine grading)';
COMMENT ON COLUMN collection_items.sleeve_condition IS 'Condition of the album sleeve/jacket';
COMMENT ON COLUMN collection_imports.user_id IS 'User who initiated the import';
COMMENT ON COLUMN discogs_user_tokens.last_synced_at IS 'Last successful Discogs collection sync timestamp';
COMMENT ON COLUMN collection_import_rows.import_id IS 'Parent collection import job';
COMMENT ON COLUMN albums.search_vector IS 'Full-text search vector (auto-updated by trigger)';
COMMENT ON COLUMN outbox_events.processed IS 'Whether this event has been published to message queue';
COMMENT ON COLUMN discogs_cache_pages.cache_key IS 'Unique key format: master_releases:{master_id}:page:{page}:per_page:{per_page}';
COMMENT ON COLUMN discogs_cache_pages.expires_at IS 'Automatic expiration after 24 hours for page cache';
COMMENT ON COLUMN discogs_cache_releases.expires_at IS 'Automatic expiration after 7 days for release cache';
