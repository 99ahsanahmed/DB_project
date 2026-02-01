-- Migration 07: Optimize Telemetry Query Performance
-- Problem: Telemetry query still slow despite composite index
-- Solution: Ensure optimal index usage and add covering index if needed

-- Drop and recreate composite index with better column order
DROP INDEX IF EXISTS idx_telemetry_truck_timestamp;

-- Create composite index: truck_license_plate first (for filtering), then timestamp DESC (for ordering)
-- This matches the query pattern: WHERE truck_license_plate = X ORDER BY timestamp DESC LIMIT 100
CREATE INDEX idx_telemetry_truck_timestamp 
ON truck_telemetry(truck_license_plate, timestamp DESC);

-- Also create a separate index on truck_license_plate for cases where we don't need ordering
CREATE INDEX IF NOT EXISTS idx_telemetry_truck_plate 
ON truck_telemetry(truck_license_plate);

-- Analyze to update statistics and help query planner
ANALYZE truck_telemetry;

-- Verify index will be used (this is informational, actual verification via EXPLAIN)
-- The query planner should use idx_telemetry_truck_timestamp for:
-- SELECT * FROM truck_telemetry WHERE truck_license_plate = 'X' ORDER BY timestamp DESC LIMIT 100
