-- Migration 08: Optimize JSON Query with Partial Index
-- Problem: Query matches 90% of rows, making index scan inefficient
-- Solution: Create partial index for high-value invoices only, or use expression index differently

-- The current query: WHERE (raw_invoice_data->>'amount_cents')::INT > 50000
-- This matches most rows, so seq scan is actually optimal
-- But we can optimize by:
-- 1. Creating a computed column for amount_cents
-- 2. Or using a partial index for the high-value subset

-- Option: Create a functional index that might be more efficient
-- But since 90% match, we might need to accept seq scan is optimal

-- However, let's try creating a covering index that includes all columns
-- This won't help with the filter, but might help with the SELECT *
DROP INDEX IF EXISTS idx_finance_invoices_amount_btree;

-- Create index with INCLUDE to make it a covering index
-- This won't help the filter, but PostgreSQL might use it if it's more efficient
CREATE INDEX idx_finance_invoices_amount_covering 
ON finance_invoices (((raw_invoice_data->>'amount_cents')::INT))
INCLUDE (id, shipment_uuid, raw_invoice_data, issued_date);

-- Actually, for this case where most rows match, we should optimize the query itself
-- Let's create a materialized column or use a different approach
-- But first, let's ensure the planner has good statistics
ANALYZE finance_invoices;

-- Note: When >90% of rows match, seq scan is often optimal
-- The real optimization would be to filter earlier or use a different data structure
