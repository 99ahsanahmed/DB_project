-- database/init.sql
DROP TABLE IF EXISTS shipments;
DROP TABLE IF EXISTS truck_telemetry;
DROP TABLE IF EXISTS finance_invoices;
DROP TABLE IF EXISTS drivers;

-- 1. OPS: The Monolith (OPTIMIZED)
CREATE TABLE shipments (
    id SERIAL PRIMARY KEY,
    tracking_uuid TEXT,
    origin_country TEXT,
    destination_country TEXT,
    driver_name TEXT,  -- Extracted from driver_details for fast lookup
    driver_details TEXT,  -- Keep original for compatibility
    truck_details TEXT,
    status TEXT,
    created_at TIMESTAMP  -- Changed from TEXT to TIMESTAMP for proper indexing
);

-- 2. IOT: The Time-Series Trap (OPTIMIZED)
CREATE TABLE truck_telemetry (
    id SERIAL PRIMARY KEY,
    truck_license_plate TEXT,
    latitude FLOAT,
    longitude FLOAT,
    elevation INT,
    speed INT,
    engine_temp FLOAT,
    fuel_level FLOAT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- 3. FINANCE: The JSON Dump (OPTIMIZED)
CREATE TABLE finance_invoices (
    id SERIAL PRIMARY KEY,
    shipment_uuid TEXT,
    raw_invoice_data JSONB,  -- Changed from TEXT to JSONB for fast queries
    issued_date DATE
);