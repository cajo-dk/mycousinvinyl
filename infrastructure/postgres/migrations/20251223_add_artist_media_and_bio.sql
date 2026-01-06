-- Add image, disambiguation, and bio fields to artists
ALTER TABLE artists
  ADD COLUMN IF NOT EXISTS image_url TEXT,
  ADD COLUMN IF NOT EXISTS disambiguation VARCHAR(500),
  ADD COLUMN IF NOT EXISTS bio TEXT;
