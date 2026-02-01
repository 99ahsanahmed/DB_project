-- Migration 03: Comprehensive Performance Optimizations

-- 1. Convert created_at from TEXT to TIMESTAMP (if not already done)
-- Note: This requires data migration, but for new installs it's already TIMESTAMP
-- For existing data, you'd need: ALTER TABLE shipments ALTER COLUMN created_at TYPE TIMESTAMP USING created_at::TIMESTAMP;

-- 2. Extract driver_name column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'shipments' AND column_name = 'driver_name'
    ) THEN
        ALTER TABLE shipments ADD COLUMN driver_name TEXT;
        -- Extract driver name from driver_details (format: "Name,Phone,License")
        UPDATE shipments 
        SET driver_name = SPLIT_PART(driver_details, ',', 1) 
        WHERE driver_name IS NULL AND driver_details IS NOT NULL;
    END IF;
END $$;

-- 3. Create index on created_at for date range queries (B-tree index on TIMESTAMP)
CREATE INDEX IF NOT EXISTS idx_shipments_created_at_btree 
ON shipments(created_at);

-- 4. Create index on driver_name for fast driver lookups
CREATE INDEX IF NOT EXISTS idx_shipments_driver_name 
ON shipments(driver_name);

-- 5. Convert raw_invoice_data to JSONB if it's still TEXT, then create GIN index
-- Note: This is handled by migration 06, skip here to avoid errors
-- The GIN index creation is moved to migration 06_fix_jsonb_conversion.sql

-- 6. Create composite index on truck_telemetry for fast truck history queries
CREATE INDEX IF NOT EXISTS idx_telemetry_truck_timestamp 
ON truck_telemetry(truck_license_plate, timestamp DESC);

-- 7. Create index on status for analytics queries
CREATE INDEX IF NOT EXISTS idx_shipments_status 
ON shipments(status) WHERE status = 'DELIVERED';

-- 8. Create index on telemetry speed for analytics
CREATE INDEX IF NOT EXISTS idx_telemetry_speed 
ON truck_telemetry(speed);

-- 9. Analyze tables to update statistics
ANALYZE shipments;
ANALYZE truck_telemetry;
ANALYZE finance_invoices;
