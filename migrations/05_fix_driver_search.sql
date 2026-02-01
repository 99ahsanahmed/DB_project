-- Migration 05: Fix Driver Search with Trigram Index
-- Problem: ILIKE '%pattern%' can't use regular B-tree indexes efficiently
-- Solution: Use pg_trgm extension with trigram index for pattern matching

-- Enable pg_trgm extension for trigram pattern matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Drop existing index if it exists (we'll replace it with trigram)
DROP INDEX IF EXISTS idx_shipments_driver_name;

-- Create trigram GIN index on driver_name for fast ILIKE pattern matching
CREATE INDEX idx_shipments_driver_name_trgm 
ON shipments USING GIN (driver_name gin_trgm_ops);

-- Analyze to update statistics
ANALYZE shipments;
