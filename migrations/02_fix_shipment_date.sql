-- Migration 02: Create index on shipments.shipment_date for faster date queries

CREATE INDEX idx_shipments_date
ON shipments(created_at);
