import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase import get_supabase

def seed_company_profile():
    supabase = get_supabase()
    
    # Get first tenant
    tenants = supabase.table('tenants').select('id').limit(1).execute()
    tenant_id = tenants.data[0]['id'] if tenants.data else None
    
    if not tenant_id:
        print("Error: No tenant found.")
        return

    # Check if profile exists
    existing = supabase.table('company_profiles').select('*').eq('tenant_id', tenant_id).execute()
    if existing.data:
        print("Company profile already exists. Updating...")
        supabase.table('company_profiles').update({
            'name': 'TechSolutions India Pvt Ltd',
            'tagline': 'Enterprise Digital Transformation Partners',
            'address': 'Level 5, Cyber Tower, IT Park, Mumbai - 400076, Maharashtra',
            'phone': '+91 22 4567 8900',
            'email': 'proposals@techsolutions.in',
            'website': 'www.techsolutions.in',
            'primary_color': '#0ea5e9',
            'accent_color': '#6366f1'
        }).eq('tenant_id', tenant_id).execute()
    else:
        print("Creating new company profile...")
        supabase.table('company_profiles').insert({
            'tenant_id': tenant_id,
            'name': 'TechSolutions India Pvt Ltd',
            'tagline': 'Enterprise Digital Transformation Partners',
            'address': 'Level 5, Cyber Tower, IT Park, Mumbai - 400076, Maharashtra',
            'phone': '+91 22 4567 8900',
            'email': 'proposals@techsolutions.in',
            'website': 'www.techsolutions.in',
            'primary_color': '#0ea5e9',
            'accent_color': '#6366f1'
        }).execute()
    
    print("Done!")

if __name__ == "__main__":
    seed_company_profile()
