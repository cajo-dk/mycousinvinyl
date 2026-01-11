-- Migration: Add indexes and updated_at trigger for market_data pricing
-- Date: 2025-12-27
-- Description: Add performance indexes and ensure updated_at auto-update trigger exists

-- Add index for efficient lookups when joining collection items with market data
CREATE INDEX IF NOT EXISTS idx_market_data_pressing_id ON market_data(pressing_id);

-- Add index for worker queries to find stale pricing data
CREATE INDEX IF NOT EXISTS idx_market_data_updated_at ON market_data(updated_at);

-- Ensure updated_at trigger exists (shared update_updated_at_column function is defined in init.sql)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_trigger
    WHERE tgname = 'update_market_data_updated_at'
  ) THEN
    CREATE TRIGGER update_market_data_updated_at
        BEFORE UPDATE ON market_data
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
  END IF;
END $$;

-- Add documentation comments to clarify table usage
COMMENT ON TABLE market_data IS 'Marketplace pricing data from Discogs for pressings. Updated periodically by pricing worker.';
COMMENT ON COLUMN market_data.median_value IS 'Median marketplace price - primary display value for estimated sales price';
COMMENT ON COLUMN market_data.updated_at IS 'Last time pricing data was fetched from Discogs API. Used to determine when pricing needs refresh (30 day threshold).';
COMMENT ON COLUMN market_data.pressing_id IS 'Foreign key to pressings table. Market data is pressing-level (shared across all users who own the same pressing).';
