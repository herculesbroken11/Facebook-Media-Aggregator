-- Facebook Media Aggregator Database Schema
-- Run this script to create the database and table structure

-- Create database (run this as superuser)
-- CREATE DATABASE facebook_aggregator;

-- Connect to the database
-- \c facebook_aggregator;

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table for authentication
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  name TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,
  is_admin BOOLEAN DEFAULT FALSE
);

-- Create the fb_media_posts table
CREATE TABLE IF NOT EXISTS fb_media_posts (
  id SERIAL PRIMARY KEY,
  
  -- Core identifiers
  post_url TEXT UNIQUE NOT NULL,
  group_id TEXT,
  
  -- Author details
  author_name TEXT,
  author_url TEXT,
  
  -- Post content
  text_content TEXT,
  image_urls JSONB DEFAULT '[]',
  video_urls JSONB DEFAULT '[]',
  
  -- Metadata
  created_at TIMESTAMP,
  reactions INTEGER DEFAULT 0,
  comments INTEGER DEFAULT 0,
  content_type VARCHAR(20) DEFAULT 'text',
  
  -- Optional raw JSON for debugging or analytics
  raw_data JSONB
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_fb_media_posts_group_id ON fb_media_posts(group_id);
CREATE INDEX IF NOT EXISTS idx_fb_media_posts_created_at ON fb_media_posts(created_at);

-- Full-text search index on content (optional)
-- CREATE INDEX IF NOT EXISTS idx_fb_posts_content_fts ON fb_posts USING gin(to_tsvector('english', content));

-- Note: To create admin users, use the create_user.py script:
--   python create_user.py
-- 
-- This ensures passwords are properly hashed using werkzeug.security
-- Only users with is_admin=true can login to the dashboard
--
-- Example manual insert (NOT RECOMMENDED - use create_user.py instead):
-- Note: UUID will be auto-generated, but you can specify one if needed
-- INSERT INTO users (id, email, password_hash, name, is_admin) VALUES (
--   '634d09bf-73e4-4384-8014-d33707b04770'::uuid,  -- Optional: specify UUID or let it auto-generate
--   'admin@example.com',
--   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJ5KJ5K5K',  -- Replace with actual hash from create_user.py
--   'Admin User',
--   TRUE  -- Set to TRUE for admin access
-- );

-- Example insert for fb_media_posts (for testing)
-- INSERT INTO fb_media_posts (
--   post_url,
--   author_name,
--   author_url,
--   text_content,
--   image_urls,
--   group_id,
--   reactions,
--   comments,
--   created_at
-- ) VALUES (
--   'https://facebook.com/groups/example/permalink/123/',
--   'John Doe',
--   'https://facebook.com/john.doe',
--   'This is a test post with some content.',
--   '["https://cdn.fb.com/photo1.jpg", "https://cdn.fb.com/photo2.jpg"]'::jsonb,
--   'group123',
--   24,
--   12,
--   NOW()
-- );
