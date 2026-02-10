-- Phase 4: Approval Workflows & Audit Trails
-- Maps to Module 4 of FRD

-- 1. Review Comments
CREATE TABLE IF NOT EXISTS review_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    response_id UUID REFERENCES responses(id) NOT NULL,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    tenant_id UUID REFERENCES tenants(id), -- Denormalized for RLS
    
    comment_text TEXT NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Workflow State Transitions (Audit for status changes)
CREATE TABLE IF NOT EXISTS workflow_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL, -- 'response', 'document'
    entity_id UUID NOT NULL,
    tenant_id UUID REFERENCES tenants(id),
    
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_by UUID REFERENCES auth.users(id) NOT NULL,
    
    change_reason TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Policies
ALTER TABLE review_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view tenant comments" ON review_comments
    FOR ALL USING (tenant_id = get_current_tenant_id());

CREATE POLICY "Users can view tenant workflow history" ON workflow_history
    FOR ALL USING (tenant_id = get_current_tenant_id());

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_comments_response ON review_comments(response_id);
CREATE INDEX IF NOT EXISTS idx_workflow_entity ON workflow_history(entity_id);
