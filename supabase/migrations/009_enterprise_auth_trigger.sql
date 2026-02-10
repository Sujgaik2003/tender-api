-- ENTERPRISE AUTH FIX: Auto-create Profiles & Tenants
-- Run this in Supabase SQL Editor

-- 1. Ensure Default Tenant exists
INSERT INTO tenants (name, subscription_tier)
SELECT 'Default Organization', 'ENTERPRISE'
WHERE NOT EXISTS (SELECT 1 FROM tenants);

-- 2. Trigger Function to create user_profile and assign tenant ALWAYS on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
DECLARE
    default_tenant_id UUID;
BEGIN
    -- Get the first tenant
    SELECT id INTO default_tenant_id FROM public.tenants LIMIT 1;

    INSERT INTO public.user_profiles (id, full_name, role, tenant_id)
    VALUES (
        new.id, 
        COALESCE(new.raw_user_meta_data->>'full_name', new.email),
        'USER',
        default_tenant_id
    );
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 3. Register Trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 4. Fix ALL Existing Profiles that are missing tenant_id
UPDATE public.user_profiles
SET tenant_id = (SELECT id FROM public.tenants LIMIT 1)
WHERE tenant_id IS NULL;

-- 5. Fix users who don't even have a row in user_profiles
INSERT INTO public.user_profiles (id, full_name, role, tenant_id)
SELECT 
    u.id, 
    COALESCE(u.raw_user_meta_data->>'full_name', u.email),
    'USER',
    (SELECT id FROM public.tenants LIMIT 1)
FROM auth.users u
LEFT JOIN public.user_profiles p ON u.id = p.id
WHERE p.id IS NULL;
