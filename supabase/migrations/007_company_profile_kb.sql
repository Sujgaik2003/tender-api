-- Phase 3: Enterprise Knowledge Base & Company Profile
-- Maps to Module 2 of FRD

-- 1. Organization Profile (Tenants extended)
-- Adding explicit profile fields to the existing tenant config or as a separate table
-- Here we create a specific table for structured company data
CREATE TABLE IF NOT EXISTS company_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) NOT NULL UNIQUE, -- One profile per tenant
    legal_name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(50),
    registration_number VARCHAR(50),
    company_address TEXT,
    website VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    
    -- Structured Matrices (Stored as JSON for flexibility)
    capabilities JSONB DEFAULT '[]', -- List of capabilities
    certifications JSONB DEFAULT '[]', -- List of {name, issuer, expiry, file_url}
    insurance JSONB DEFAULT '[]', -- List of {type, provider, amount, expiry}
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Past Performance (Case Studies)
CREATE TABLE IF NOT EXISTS past_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) NOT NULL,
    
    project_title VARCHAR(255) NOT NULL,
    client_name VARCHAR(255),
    project_value DECIMAL(15, 2), -- Supports large contract values
    currency VARCHAR(3) DEFAULT 'USD',
    start_date DATE,
    end_date DATE,
    
    description TEXT,
    challenges TEXT,
    solution TEXT,
    outcomes TEXT,
    
    keywords TEXT[], -- For search
    reference_contact JSONB, -- {name, email, phone}
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Team Profiles (Resume Bank)
CREATE TABLE IF NOT EXISTS team_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) NOT NULL,
    
    full_name VARCHAR(255) NOT NULL,
    designation VARCHAR(100),
    years_experience INTEGER,
    
    skills TEXT[],
    qualifications TEXT[], -- Array of strings
    
    bio_summary TEXT, -- Generated bio for proposals
    full_cv_text TEXT, -- Parsed full CV content for searching
    
    linkedin_url VARCHAR(255),
    
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Content Library Templates
CREATE TABLE IF NOT EXISTS content_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) NOT NULL,
    
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100), -- e.g., "Cover Letter", "Executive Summary"
    content_structure JSONB, -- Structured content blocks
    
    is_default BOOLEAN DEFAULT FALSE,
    version INTEGER DEFAULT 1,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Policies
ALTER TABLE company_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE past_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_templates ENABLE ROW LEVEL SECURITY;

-- Helper to get tenant (reused)
-- CREATE OR REPLACE FUNCTION get_current_tenant_id() ... (Already exists from Phase 1)

CREATE POLICY "Users can view own company profile" ON company_profiles
    FOR ALL USING (tenant_id = get_current_tenant_id());

CREATE POLICY "Users can manage past performance" ON past_performance
    FOR ALL USING (tenant_id = get_current_tenant_id());

CREATE POLICY "Users can manage team profiles" ON team_profiles
    FOR ALL USING (tenant_id = get_current_tenant_id());

CREATE POLICY "Users can manage templates" ON content_templates
    FOR ALL USING (tenant_id = get_current_tenant_id());

-- Indexes for Vector Search Integration (Mental Model: These tables will also be embedded into FAISS)
CREATE INDEX IF NOT EXISTS idx_past_perf_tenant ON past_performance(tenant_id);
CREATE INDEX IF NOT EXISTS idx_team_prof_tenant ON team_profiles(tenant_id);
