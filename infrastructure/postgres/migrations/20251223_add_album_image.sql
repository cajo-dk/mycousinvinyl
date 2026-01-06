-- Add image URL field to albums
ALTER TABLE albums
  ADD COLUMN IF NOT EXISTS image_url TEXT;
