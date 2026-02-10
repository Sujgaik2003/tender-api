-- Enterprise Foundation Migration
-- 1. Create Tenants Table
-- 2. Add tenant_id to all major tables
-- 3. Update RLS policies for strict isolation

-- 1. Tenants Table
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(50) DEFAULT 'FREE', -- FREE, PRO, ENTERPRISE
    config JSONB DEFAULT '{}', -- Feature flags, customization
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. User Profiles - Link to Tenant
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);

CREATE INDEX IF NOT EXISTS idx_user_profiles_tenant_id ON user_profiles(tenant_id);

-- 3. Documents - Link to Tenant
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);

CREATE INDEX IF NOT EXISTS idx_documents_tenant_id ON documents(tenant_id);

-- 4. Requirements - Link to Tenant
ALTER TABLE requirements 
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);

CREATE INDEX IF NOT EXISTS idx_requirements_tenant_id ON requirements(tenant_id);

-- 5. Knowledge Base - Link to Tenant
ALTER TABLE knowledge_base 
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);

CREATE INDEX IF NOT EXISTS idx_knowledge_base_tenant_id ON knowledge_base(tenant_id);

-- 6. Responses - Link to Tenant
ALTER TABLE responses 
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);

CREATE INDEX IF NOT EXISTS idx_responses_tenant_id ON responses(tenant_id);

-- 7. Match Results - Link to Tenant (Optimization for queries)
ALTER TABLE match_results 
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);

CREATE INDEX IF NOT EXISTS idx_match_results_tenant_id ON match_results(tenant_id);

-- 8. Audit Logs - Link to Tenant
ALTER TABLE audit_log 
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);

CREATE INDEX IF NOT EXISTS idx_audit_log_tenant_id ON audit_log(tenant_id);


-- 9. ENABLE RLS & POLICIES (Strict Tenant Isolation)

-- Helper function to get current tenant_id from JWT or Session
-- Note: In Supabase, we often store tenant_id in app_metadata
-- For now, we assume we can cast a claim or join users. 
-- A reliable way in Supabase is checking the user_profile of the auth.uid()

CREATE OR REPLACE FUNCTION get_current_tenant_id()
RETURNS UUID AS $$
BEGIN
    RETURN (
        SELECT tenant_id 
        FROM user_profiles 
        WHERE id = auth.uid()
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Update RLS for Tenants
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own tenant" ON tenants
    FOR SELECT USING (
        id = get_current_tenant_id()
    );

-- Update RLS for Documents
DROP POLICY IF EXISTS "Users can manage own documents" ON documents;
CREATE POLICY "Users can manage tenant documents" ON documents
    FOR ALL USING (
        tenant_id = get_current_tenant_id()
    );

-- Update RLS for Requirements
DROP POLICY IF EXISTS "Users can view requirements for own documents" ON requirements;
CREATE POLICY "Users can manage tenant requirements" ON requirements
    FOR ALL USING (
        tenant_id = get_current_tenant_id()
    );

-- Update RLS for Knowledge Base
DROP POLICY IF EXISTS "Authenticated users can read knowledge base" ON knowledge_base;
CREATE POLICY "Users can manage tenant knowledge base" ON knowledge_base
    FOR ALL USING (
        tenant_id = get_current_tenant_id()
    );

-- Update RLS for Responses
DROP POLICY IF EXISTS "Users can manage responses for own documents" ON responses;
CREATE POLICY "Users can manage tenant responses" ON responses
    FOR ALL USING (
        tenant_id = get_current_tenant_id()
    );

-- Update RLS for Match Results
DROP POLICY IF EXISTS "Users can view matches for own documents" ON match_results;
CREATE POLICY "Users can view tenant matches" ON match_results
    FOR SELECT USING (
        tenant_id = get_current_tenant_id()
    );

-- Update RLS for Exports
DROP POLICY IF EXISTS "Users can view own exports" ON exports;
ALTER TABLE exports ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
CREATE POLICY "Users can view tenant exports" ON exports
    FOR ALL USING (
        tenant_id = get_current_tenant_id()
    );

-- Update RLS for Audit Log
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view tenant audit logs" ON audit_log
    FOR SELECT USING (
        tenant_id = get_current_tenant_id()
    );

-- Trigger to auto-set tenant_id on insert if null (optional, but good for consistency)
CREATE OR REPLACE FUNCTION set_tenant_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tenant_id IS NULL THEN
        NEW.tenant_id := get_current_tenant_id();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER documents_set_tenant
    BEFORE INSERT ON documents
    FOR EACH ROW EXECUTE FUNCTION set_tenant_id();

CREATE TRIGGER requirements_set_tenant
    BEFORE INSERT ON requirements
    FOR EACH ROW EXECUTE FUNCTION set_tenant_id();

CREATE TRIGGER knowledge_base_set_tenant
    BEFORE INSERT ON knowledge_base
    FOR EACH ROW EXECUTE FUNCTION set_tenant_id();

CREATE TRIGGER responses_set_tenant
    BEFORE INSERT ON responses
    FOR EACH ROW EXECUTE FUNCTION set_tenant_id();
