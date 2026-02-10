-- AUTO-FIX SCRIPT: Assign Tenant to Orphaned Users

-- 1. Create a Default Tenant if none exists
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM tenants) THEN
        INSERT INTO tenants (name, subscription_tier) VALUES ('Default Organization', 'enterprise');
    END IF;
END $$;

-- 2. Link orphan users in user_profiles to the first available tenant
UPDATE user_profiles
SET tenant_id = (SELECT id FROM tenants LIMIT 1)
WHERE tenant_id IS NULL;

-- 3. (Optional) Ensure auth.users metadata is also updated if you rely on it
-- NOTE: This requires direct access to auth schema which might be restricted in SQL Editor
-- Instead, we just trust the user_profiles table which our API checks directly.
