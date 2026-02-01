-- Migration 04: Create Materialized View for Analytics

-- Drop existing materialized view if it exists
DROP MATERIALIZED VIEW IF EXISTS daily_stats_cache;

-- Create materialized view for fast analytics queries
CREATE MATERIALIZED VIEW daily_stats_cache AS
SELECT 
    (SELECT COUNT(*) FROM shipments WHERE status='DELIVERED') as delivered,
    (SELECT AVG(speed) FROM truck_telemetry WHERE speed > 0) as avg_speed,
    (SELECT SUM((raw_invoice_data->>'amount_cents')::INT) FROM finance_invoices) as revenue;

-- Create unique index on the materialized view (required for refresh)
CREATE UNIQUE INDEX ON daily_stats_cache (delivered, avg_speed, revenue);

-- Note: This view should be refreshed periodically or on-demand
-- REFRESH MATERIALIZED VIEW daily_stats_cache;
