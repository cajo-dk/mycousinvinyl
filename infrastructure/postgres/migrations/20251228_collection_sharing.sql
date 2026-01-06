-- Migration: Collection Sharing Feature
-- Date: 2025-12-28
-- Description: Adds user_follows table to enable collection sharing functionality

-- Create user_follows table for tracking which users follow each other
CREATE TABLE IF NOT EXISTS user_follows (
    follower_user_id UUID NOT NULL,
    followed_user_id UUID NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (follower_user_id, followed_user_id),
    CONSTRAINT no_self_follow CHECK (follower_user_id != followed_user_id)
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_user_follows_follower ON user_follows(follower_user_id);
CREATE INDEX IF NOT EXISTS idx_user_follows_followed ON user_follows(followed_user_id);

-- Add comment explaining the table
COMMENT ON TABLE user_follows IS 'Tracks user follow relationships for collection sharing. Limited to 3 follows per user (enforced by application layer).';
COMMENT ON COLUMN user_follows.follower_user_id IS 'User ID of the person following';
COMMENT ON COLUMN user_follows.followed_user_id IS 'User ID of the person being followed';
COMMENT ON CONSTRAINT no_self_follow ON user_follows IS 'Prevents users from following themselves';
