-- Migration: Add indexes and trigger for market_data pricing
-- Date: 2025-12-27
-- Description: Add performance indexes and auto-update trigger for the existing market_data table

-- Add index for efficient lookups when joining collection items with market data
CREATE INDEX IF NOT EXISTS idx_market_data_pressing_id ON market_data(pressing_id);

-- Add index for worker queries to find stale pricing data
CREATE INDEX IF NOT EXISTS idx_market_data_updated_at ON market_data(updated_at);

-- Add trigger function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_market_data_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger that fires before any UPDATE on market_data
CREATE TRIGGER market_data_update_timestamp
    BEFORE UPDATE ON market_data
    FOR EACH ROW
    EXECUTE FUNCTION update_market_data_timestamp();

-- Add documentation comments to clarify table usage
COMMENT ON TABLE market_data IS 'Marketplace pricing data from Discogs for pressings. Updated periodically by pricing worker.';
COMMENT ON COLUMN market_data.median_value IS 'Median marketplace price - primary display value for estimated sales price';
COMMENT ON COLUMN market_data.updated_at IS 'Last time pricing data was fetched from Discogs API. Used to determine when pricing needs refresh (30 day threshold).';
COMMENT ON COLUMN market_data.pressing_id IS 'Foreign key to pressings table. Market data is pressing-level (shared across all users who own the same pressing).';
