-- UPGRADE: SMART ENTERPRISE TENANT DYNAMICS
-- This logic handles the signup operation by looking at the "Organization Name" 
-- provided during signup. It either attaches the user to an existing corp environment
-- or establishes a brand new one with Founder Authority.

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
DECLARE
    target_tenant_id UUID;
    target_org_name TEXT;
    member_count INTEGER;
    assigned_role VARCHAR(50);
BEGIN
    -- 1. Extract the Organization Name from the signup metadata
    target_org_name := COALESCE(new.raw_user_meta_data->>'org_name', 'Default Organization');

    -- 2. Find or Create the Tenant
    SELECT id INTO target_tenant_id FROM public.tenants WHERE name = target_org_name LIMIT 1;
    
    IF target_tenant_id IS NULL THEN
        INSERT INTO public.tenants (name, subscription_tier)
        VALUES (target_org_name, 'ENTERPRISE')
        RETURNING id INTO target_tenant_id;
    END IF;

    -- 3. Check if this is the first user of THIS specific organization
    SELECT count(*) INTO member_count FROM public.user_profiles WHERE tenant_id = target_tenant_id;

    -- 4. Logic: First user gets ADMIN (Founder), everyone else is a BID_WRITER
    IF member_count = 0 THEN
        assigned_role := 'ADMIN';
    ELSE
        assigned_role := 'BID_WRITER';
    END IF;

    -- 5. Create the profile
    INSERT INTO public.user_profiles (id, full_name, role, tenant_id)
    VALUES (
        new.id, 
        COALESCE(new.raw_user_meta_data->>'full_name', new.email),
        assigned_role,
        target_tenant_id
    );
    
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
