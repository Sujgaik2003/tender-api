-- Migration: 012 Tender Discovery System
-- Objective: Support the autonomous scraping and evaluation of tenders

-- 1. Tender Discovery Table
CREATE TABLE IF NOT EXISTS discovered_tenders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_ref_id VARCHAR(255) NOT NULL, -- Tender ID / Reference Number
    title TEXT NOT NULL,
    authority VARCHAR(255),
    publish_date TIMESTAMPTZ,
    submission_deadline TIMESTAMPTZ,
    category VARCHAR(255),
    department VARCHAR(255),
    source_portal VARCHAR(255),
    location VARCHAR(255),
    description TEXT,
    
    -- Status & Matching
    status VARCHAR(50) DEFAULT 'PENDING', -- PENDING, APPROVED, REJECTED, ARCHIVED
    match_score DECIMAL(5,2) DEFAULT 0,
    match_explanation TEXT,
    domain_tags TEXT[] DEFAULT '{}',
    
    -- Change Detection
    content_hash VARCHAR(64), -- For change detection
    is_updated BOOLEAN DEFAULT FALSE,
    last_scanned_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Multi-tenancy (Global or per-tenant?)
    -- Usually tenders are global until assigned to a tenant for evaluation
    -- But for simplicity and consistency with existing schema:
    tenant_id UUID REFERENCES tenants(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(external_ref_id, source_portal)
);

-- 2. Tender Attachments
CREATE TABLE IF NOT EXISTS tender_attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tender_id UUID REFERENCES discovered_tenders(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    external_url TEXT NOT NULL,
    file_type VARCHAR(50), -- PDF, DOCX, ZIP
    storage_path TEXT, -- If we download them
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Company Domain Knowledge Base (Extensions for Matching)
-- We can reuse the existing knowledge_base or add a specific one for "What we look for"
CREATE TABLE IF NOT EXISTS discovery_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) NOT NULL UNIQUE,
    keywords TEXT[] DEFAULT '{}',
    preferred_domains TEXT[] DEFAULT '{}', -- AI, Data, Infra, etc.
    preferred_authorities TEXT[] DEFAULT '{}',
    min_match_score DECIMAL(5,2) DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Tender Portals (Scanner Management)
CREATE TABLE IF NOT EXISTS discovery_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    source_type VARCHAR(50) DEFAULT 'PUBLIC', -- PUBLIC, LOGIN_REQUIRED
    auth_config JSONB DEFAULT '{}', -- Encrypted credentials or vault refs
    scraping_logic VARCHAR(50), -- name of the scraper class/logic to use
    is_active BOOLEAN DEFAULT TRUE,
    last_scan_success BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS & Policies
ALTER TABLE discovered_tenders ENABLE ROW LEVEL SECURITY;
ALTER TABLE tender_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE discovery_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE discovery_sources ENABLE ROW LEVEL SECURITY;

-- Note: discovered_tenders might be global (admin-only) or tenant-specific.
-- If it's a "Discovery Agent" per tenant, then tenant_id is mandatory.
-- Let's make it tenant-isolated as per the existing app architecture.

CREATE POLICY "Users can manage discovered tenders" ON discovered_tenders
    FOR ALL USING (tenant_id = get_current_tenant_id());

CREATE POLICY "Users can view attachments" ON tender_attachments
    FOR ALL USING (
        tender_id IN (SELECT id FROM discovered_tenders WHERE tenant_id = get_current_tenant_id())
    );

CREATE POLICY "Users can manage discovery config" ON discovery_config
    FOR ALL USING (tenant_id = get_current_tenant_id());

-- Discovery sources are global for now (Admin only can manage, but users can see)
CREATE POLICY "Users can view discovery sources" ON discovery_sources
    FOR SELECT USING (TRUE);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_discovered_tenders_external_id ON discovered_tenders(external_ref_id);
CREATE INDEX IF NOT EXISTS idx_discovered_tenders_status ON discovered_tenders(status);
CREATE INDEX IF NOT EXISTS idx_discovered_tenders_tenant_id ON discovered_tenders(tenant_id);
CREATE INDEX IF NOT EXISTS idx_discovered_tenders_score ON discovered_tenders(match_score);
