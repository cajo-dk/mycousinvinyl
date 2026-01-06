-- Add Discogs master/release fields and master relationship to pressings
ALTER TABLE pressings
  ADD COLUMN IF NOT EXISTS discogs_release_id INT,
  ADD COLUMN IF NOT EXISTS discogs_master_id INT,
  ADD COLUMN IF NOT EXISTS master_id UUID REFERENCES pressings(id) ON DELETE SET NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'chk_pressing_master_not_self'
  ) THEN
    ALTER TABLE pressings
      ADD CONSTRAINT chk_pressing_master_not_self
      CHECK (master_id IS NULL OR master_id <> id);
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_pressings_master ON pressings(master_id);
CREATE INDEX IF NOT EXISTS idx_pressings_discogs_release ON pressings(discogs_release_id);
CREATE INDEX IF NOT EXISTS idx_pressings_discogs_master ON pressings(discogs_master_id);
