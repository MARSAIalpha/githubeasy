"""Check how many projects still need AI analysis"""
import sys
sys.path.insert(0, '.')

from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Total projects
total_res = client.table("projects").select("id", count="exact").execute()
total = total_res.count

# Analyzed (has ai_summary)
analyzed_res = client.table("projects").select("id", count="exact").not_.is_("ai_summary", "null").execute()
analyzed = analyzed_res.count

# Pending
pending = total - analyzed

print(f"Total Projects: {total}")
print(f"Already Analyzed: {analyzed}")
print(f"Pending Analysis: {pending}")
