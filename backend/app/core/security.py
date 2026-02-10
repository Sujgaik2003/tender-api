from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.core.config import get_settings
from app.core.supabase import get_supabase

settings = get_settings()
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Validate JWT token and return user info with tenant context."""
    token = credentials.credentials
    supabase = get_supabase()
    
    # 1. Get User ID
    try:
        # Try local decode first
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm], options={"verify_aud": False})
        user_id = payload.get("sub")
        email = payload.get("email")
    except JWTError:
        # Fallback to Supabase API
        try:
            resp = supabase.auth.get_user(token)
            user = resp.user if hasattr(resp, 'user') else resp.get('user')
            user_id = user.id if hasattr(user, 'id') else user.get('id')
            email = user.email if hasattr(user, 'email') else user.get('email')
        except Exception as e:
            print(f"[AUTH ERROR] Token invalid: {e}")
            raise HTTPException(status_code=401, detail="Invalid session")

    # 2. Fetch/Heal Tenant Association & Role
    tenant_id = None
    role = "USER"
    try:
        # Use service key to bypass RLS and ensure we see the result
        profile = supabase.table("user_profiles").select("tenant_id, role").eq("id", user_id).execute()
        
        if not profile.data:
            print(f"[AUTH] No profile for {user_id}. Auto-creating...")
            # Ensure a tenant exists
            tenants = supabase.table("tenants").select("id").limit(1).execute()
            if not tenants.data:
                print("[AUTH] Creating missing default tenant...")
                tenants = supabase.table("tenants").insert({"name": "Default Org", "subscription_tier": "ENTERPRISE"}).execute()
            
            tenant_id = tenants.data[0]['id']
            supabase.table("user_profiles").insert({
                "id": user_id,
                "tenant_id": tenant_id,
                "full_name": email.split("@")[0] if email else "User",
                "role": "ADMIN" # First user is admin
            }).execute()
            role = "ADMIN"
        else:
            tenant_id = profile.data[0].get("tenant_id")
            role = profile.data[0].get("role", "USER")
            
            if not tenant_id:
                print(f"[AUTH] Profile exists for {user_id} but tenant_id is NULL. Fixing...")
                tenants = supabase.table("tenants").select("id").limit(1).execute()
                tenant_id = tenants.data[0]['id']
                supabase.table("user_profiles").update({"tenant_id": tenant_id}).eq("id", user_id).execute()
                
    except Exception as e:
        print(f"[AUTH ERROR] Profile resolution failed: {e}")
        # Fallback
        role = "USER"

    return {
        "id": user_id, 
        "email": email,
        "tenant_id": tenant_id,
        "role": role
    }

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict | None:
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
