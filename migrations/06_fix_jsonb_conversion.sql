-- Migration 06: Fix JSONB Conversion and GIN Index
-- Problem: raw_invoice_data is still TEXT, preventing GIN index creation
-- Solution: Convert TEXT to JSONB and create proper GIN index

-- Step 1: Check current data type and convert if needed
DO $$
BEGIN
    -- Check if column exists and is TEXT type
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'finance_invoices' 
        AND column_name = 'raw_invoice_data' 
        AND data_type = 'text'
    ) THEN
        -- Convert TEXT to JSONB
        -- First, validate that all rows are valid JSON
        ALTER TABLE finance_invoices 
        ALTER COLUMN raw_invoice_data TYPE JSONB 
        USING raw_invoice_data::JSONB;
        
        RAISE NOTICE 'Converted raw_invoice_data from TEXT to JSONB';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'finance_invoices' 
        AND column_name = 'raw_invoice_data' 
        AND data_type = 'jsonb'
    ) THEN
        RAISE NOTICE 'raw_invoice_data is already JSONB';
    END IF;
END $$;

-- Step 2: Drop old index if it exists (might have failed creation)
DROP INDEX IF EXISTS idx_finance_invoices_amount_gin;

-- Step 3: Create indexes for JSONB queries
-- Option A: B-tree index on the extracted numeric value (better for range queries)
CREATE INDEX idx_finance_invoices_amount_btree 
ON finance_invoices (((raw_invoice_data->>'amount_cents')::INT));

-- Option B: GIN index on the entire JSONB column (better for complex JSON queries)
CREATE INDEX IF NOT EXISTS idx_finance_invoices_jsonb_gin 
ON finance_invoices USING GIN (raw_invoice_data);

-- Analyze to update statistics
ANALYZE finance_invoices;
