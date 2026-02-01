-- Migration 13: Optimize Drivers Table Search
-- Problem: Sequential scan on drivers table for ILIKE pattern matching
-- Solution: Add trigram index on drivers.name for fast pattern matching

-- Enable pg_trgm extension if not already enabled
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create trigram GIN index on drivers.name for fast ILIKE searches
CREATE INDEX IF NOT EXISTS idx_drivers_name_trgm 
ON drivers USING GIN (name gin_trgm_ops);

-- Analyze to update statistics
ANALYZE drivers;
