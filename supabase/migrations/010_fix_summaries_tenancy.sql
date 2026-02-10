-- FIX: Add tenant_id to match_summaries
-- This was missing from the initial enterprise migration

ALTER TABLE match_summaries 
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);

CREATE INDEX IF NOT EXISTS idx_match_summaries_tenant_id ON match_summaries(tenant_id);

-- Backfill existing summaries if any (optional but recommended)
UPDATE match_summaries ms
SET tenant_id = d.tenant_id
FROM documents d
WHERE ms.document_id = d.id AND ms.tenant_id IS NULL;

-- Notify PostgREST to reload schema
NOTIFY pgrst, 'reload schema';
