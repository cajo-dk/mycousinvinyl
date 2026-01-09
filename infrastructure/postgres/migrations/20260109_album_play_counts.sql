-- Migration: Album Play Counts
-- Date: 2026-01-09
-- Description: Adds per-user album play counts with yearly totals

CREATE TABLE IF NOT EXISTS user_album_plays (
    user_id UUID NOT NULL,
    album_id UUID NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    play_count INT DEFAULT 0 CHECK (play_count >= 0),
    last_played_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, album_id)
);

CREATE TABLE IF NOT EXISTS user_album_play_years (
    user_id UUID NOT NULL,
    album_id UUID NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    year INT NOT NULL,
    play_count INT DEFAULT 0 CHECK (play_count >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, album_id, year)
);

CREATE INDEX IF NOT EXISTS idx_user_album_plays_user ON user_album_plays(user_id);
CREATE INDEX IF NOT EXISTS idx_user_album_plays_last_played ON user_album_plays(user_id, last_played_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_album_play_years_user_year ON user_album_play_years(user_id, year);
CREATE INDEX IF NOT EXISTS idx_user_album_play_years_user_year_count ON user_album_play_years(user_id, year, play_count DESC, album_id);

CREATE TRIGGER update_user_album_plays_updated_at
    BEFORE UPDATE ON user_album_plays
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_album_play_years_updated_at
    BEFORE UPDATE ON user_album_play_years
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE user_album_plays IS 'Per-user album play counts and last played timestamp';
COMMENT ON TABLE user_album_play_years IS 'Per-user album play counts by year';
