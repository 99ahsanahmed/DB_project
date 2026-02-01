-- Migration 01: Create index on shipments.status for faster filtering

CREATE INDEX idx_shipments_status
ON shipments(status);
