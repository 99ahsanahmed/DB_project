-- Migration 10: Fix Computed Column - Convert to Regular Column
-- Problem: STORED generated columns can't be backfilled for existing data
-- Solution: Use a regular column and backfill it, then index it

-- Drop the generated column
ALTER TABLE finance_invoices DROP COLUMN IF EXISTS amount_cents;

-- Add as regular column
ALTER TABLE finance_invoices ADD COLUMN amount_cents INT;

-- Backfill the column from JSONB
UPDATE finance_invoices 
SET amount_cents = (raw_invoice_data->>'amount_cents')::INT
WHERE amount_cents IS NULL;

-- Create index on the regular column
CREATE INDEX IF NOT EXISTS idx_finance_invoices_amount_cents 
ON finance_invoices(amount_cents);

-- Analyze to update statistics
ANALYZE finance_invoices;
