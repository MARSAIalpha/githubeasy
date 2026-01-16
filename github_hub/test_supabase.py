"""Test Supabase connection and data"""
import sys
sys.path.insert(0, '.')

from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

print(f"URL: {SUPABASE_URL}")
print(f"Key: {SUPABASE_KEY[:20]}...")

try:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Check projects count
    response = client.table("projects").select("id", count="exact").execute()
    print(f"Projects count: {response.count}")
    
    # Get first 3 projects
    response = client.table("projects").select("id,name,category").limit(3).execute()
    print(f"Sample projects: {response.data}")
    
except Exception as e:
    print(f"Error: {e}")
