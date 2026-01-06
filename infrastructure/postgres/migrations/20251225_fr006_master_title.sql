-- FR-006: Replace master_id FK with master_title field
-- This migration corrects the relationship between Pressings and Discogs Master Releases
-- by removing the incorrect internal master_id FK and adding a master_title field

-- Step 1: Add master_title column
ALTER TABLE pressings
  ADD COLUMN IF NOT EXISTS master_title VARCHAR(500);

-- Step 2: Drop the master_id self-reference constraint
ALTER TABLE pressings
  DROP CONSTRAINT IF EXISTS chk_pressing_master_not_self;

-- Step 3: Drop the index on master_id
DROP INDEX IF EXISTS idx_pressings_master;

-- Step 4: Drop the master_id column (CASCADE to remove FK)
-- Note: This will fail if there are any pressings with master_id set
-- In production, you may want to first check and clear any master_id references
ALTER TABLE pressings
  DROP COLUMN IF EXISTS master_id CASCADE;

-- Step 5: Create index on master_title for grouping queries
CREATE INDEX IF NOT EXISTS idx_pressings_master_title ON pressings(master_title);

-- Verification query (uncomment to run manually):
-- SELECT column_name, data_type, character_maximum_length
-- FROM information_schema.columns
-- WHERE table_name = 'pressings'
-- AND column_name IN ('master_id', 'master_title', 'discogs_master_id', 'discogs_release_id')
-- ORDER BY column_name;
