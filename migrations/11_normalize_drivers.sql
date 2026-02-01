-- Migration 11: Normalize Drivers Table (Per Requirements Document)
-- Goal: Reduce database size and I/O by removing duplicate text
-- Following Phase 4: The Redundancy Cleanup (Normalization)

-- Step 1: Create drivers table
CREATE TABLE IF NOT EXISTS drivers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    phone TEXT,
    license_plate TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Step 2: Extract distinct drivers from shipments
-- Parse driver_details format: "Name,Phone,License"
INSERT INTO drivers (name, phone, license_plate)
SELECT DISTINCT
    SPLIT_PART(driver_details, ',', 1) as name,
    SPLIT_PART(driver_details, ',', 2) as phone,
    SPLIT_PART(driver_details, ',', 3) as license_plate
FROM shipments
WHERE driver_details IS NOT NULL
  AND driver_name IS NOT NULL
ON CONFLICT (name) DO NOTHING;

-- Step 3: Add driver_id column to shipments
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS driver_id INT;

-- Step 4: Populate driver_id based on driver_name match
UPDATE shipments s
SET driver_id = d.id
FROM drivers d
WHERE s.driver_name = d.name
  AND s.driver_id IS NULL;

-- Step 5: Create foreign key constraint
ALTER TABLE shipments 
ADD CONSTRAINT fk_shipments_driver 
FOREIGN KEY (driver_id) REFERENCES drivers(id);

-- Step 6: Create index on driver_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_shipments_driver_id 
ON shipments(driver_id);

-- Step 7: Create index on drivers.name for fast name searches
CREATE INDEX IF NOT EXISTS idx_drivers_name 
ON drivers(name);

-- Analyze to update statistics
ANALYZE drivers;
ANALYZE shipments;
