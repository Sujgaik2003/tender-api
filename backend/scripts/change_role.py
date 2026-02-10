import sys
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Add the backend directory to the path so we can import from app
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

def change_role(email: str, new_role: str):
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        return

    supabase: Client = create_client(url, key)
    
    # 1. Get user by email from auth schema is hard with client, 
    # so we jump to user_profiles directly if we have the id or search by email metadata if possible.
    # Better: Search in user_profiles by full_name or id.
    
    # Let's just list users and ask to pick one if email not provided
    profiles = supabase.table("user_profiles").select("*").execute()
    
    if not profiles.data:
        print("No user profiles found.")
        return

    print("\nCurrent Users:")
    for p in profiles.data:
        print(f"- ID: {p['id']} | Name: {p['full_name']} | Role: {p['role']}")

    target_user = None
    if not email:
        # Pick the first one for convenience in demo
        target_user = profiles.data[0]
    else:
        # Try to find by name (since we updated email to name in auto-creation)
        for p in profiles.data:
            if email in p['full_name'] or email == p['id']:
                target_user = p
                break
    
    if not target_user:
        print(f"\nUser '{email}' not found.")
        return

    print(f"\nChanging role for {target_user['full_name']} to {new_role}...")
    
    res = supabase.table("user_profiles").update({"role": new_role}).eq("id", target_user['id']).execute()
    
    if res.data:
        print(f"Success! {target_user['full_name']} is now an {new_role}.")
        print("\nDemonstration Guide:")
        if new_role == "AUDITOR":
            print("- Log back in/Refresh: You can view responses but 'Approve' or 'Submit' will fail.")
        elif new_role == "BID_WRITER":
            print("- Log back in/Refresh: You can edit/submit, but 'Approve' will return a 403 Forbidden.")
        elif new_role == "ADMIN" or new_role == "MANAGER":
            print("- Log back in/Refresh: You have full permissions, including 'Approve'.")
    else:
        print("Failed to update role.")

if __name__ == "__main__":
    role = sys.argv[1].upper() if len(sys.argv) > 1 else "ADMIN"
    email_or_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    valid_roles = ["ADMIN", "MANAGER", "BID_WRITER", "AUDITOR"]
    if role not in valid_roles:
        print(f"Invalid role. Use one of: {', '.join(valid_roles)}")
    else:
        change_role(email_or_id, role)
