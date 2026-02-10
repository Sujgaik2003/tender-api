-- Migration to add priority column to requirements table
ALTER TABLE requirements
ADD COLUMN IF NOT EXISTS priority VARCHAR(50) DEFAULT 'Optional';

-- Index for analytics
CREATE INDEX IF NOT EXISTS idx_requirements_priority ON requirements(priority);
