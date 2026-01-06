-- Migration: Collection Imports
-- Date: 2025-12-29
-- Description: Adds tables for Discogs CSV collection imports

CREATE TABLE IF NOT EXISTS collection_imports (
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
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS collection_import_rows (
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
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (import_id, row_number)
);

CREATE INDEX IF NOT EXISTS idx_collection_imports_user ON collection_imports(user_id);
CREATE INDEX IF NOT EXISTS idx_collection_imports_status ON collection_imports(status);
CREATE INDEX IF NOT EXISTS idx_collection_import_rows_import ON collection_import_rows(import_id);
CREATE INDEX IF NOT EXISTS idx_collection_import_rows_status ON collection_import_rows(status);

CREATE TRIGGER update_collection_imports_updated_at
    BEFORE UPDATE ON collection_imports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collection_import_rows_updated_at
    BEFORE UPDATE ON collection_import_rows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE collection_imports IS 'Imports of external collection data (Discogs CSV)';
COMMENT ON TABLE collection_import_rows IS 'Row-level status for collection imports';
COMMENT ON COLUMN collection_imports.user_id IS 'User who initiated the import';
COMMENT ON COLUMN collection_import_rows.import_id IS 'Parent collection import job';
