import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.supabase import get_supabase

try:
    supabase = get_supabase()
    data = supabase.table('company_profiles').select('*').execute().data
    with open('db_test.txt', 'w') as f:
        f.write(f"Count: {len(data)}\n")
        f.write(str(data))
except Exception as e:
    with open('db_test.txt', 'w') as f:
        f.write(f"Error: {e}")
