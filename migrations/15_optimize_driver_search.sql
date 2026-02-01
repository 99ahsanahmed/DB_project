-- Migration 15: Further Optimize Driver Search
-- Goal: Make /shipments/driver/{name} extremely fast by:
--   1. Providing a composite index on (driver_id, created_at DESC) for shipments
--   2. Refreshing planner statistics

-- Create composite index to support the JOIN + ORDER BY pattern:
--   JOIN drivers d ON s.driver_id = d.id
--   WHERE d.name ILIKE ?
--   ORDER BY s.created_at DESC
--   LIMIT 20
CREATE INDEX IF NOT EXISTS idx_shipments_driver_id_created_at
ON shipments(driver_id, created_at DESC);

-- Update statistics so the planner chooses the new index
ANALYZE shipments;

