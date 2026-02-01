-- Migration 09: Add Computed Column for Amount
-- Problem: Parsing JSON at query time is slow, especially for 180k+ rows
-- Solution: Add a computed/stored column for amount_cents and index it

-- Add computed column that extracts amount_cents from JSONB
ALTER TABLE finance_invoices 
ADD COLUMN IF NOT EXISTS amount_cents INT 
GENERATED ALWAYS AS ((raw_invoice_data->>'amount_cents')::INT) STORED;

-- Create index on the computed column (much faster than parsing JSON each time)
CREATE INDEX IF NOT EXISTS idx_finance_invoices_amount_cents 
ON finance_invoices(amount_cents);

-- Analyze to update statistics
ANALYZE finance_invoices;
