-- Add image URL field to pressings
ALTER TABLE pressings
  ADD COLUMN IF NOT EXISTS image_url TEXT;
