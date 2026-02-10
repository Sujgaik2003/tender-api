-- Clean Fix for Tenants & Profiles
-- Run these one by one or as a block

-- 1. Check and fix column name manually (Standard PostgreSQL doesn't support IF EXISTS for RENAME COLUMN in some versions)
DO $$ 
BEGIN 
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tenants' AND column_name='subscription_plan') THEN
    ALTER TABLE tenants RENAME COLUMN subscription_plan TO subscription_tier;
  END IF;
END $$;

-- 2. Create the default tenant if missing
INSERT INTO tenants (name, subscription_tier)
SELECT 'Default Organization', 'ENTERPRISE'
WHERE NOT EXISTS (SELECT 1 FROM tenants);

-- 3. Ensure your user profile exists and HAS this tenant
-- This will link EVERY user to the first tenant if they are currently orphans
UPDATE user_profiles
SET tenant_id = (SELECT id FROM tenants LIMIT 1)
WHERE tenant_id IS NULL;

-- 4. Check if company_profiles table has any issues
-- (Sometimes unique constraints block updates if logic is slightly off)
SELECT * FROM tenants;
SELECT * FROM user_profiles;
