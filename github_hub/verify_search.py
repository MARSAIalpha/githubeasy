import requests
import json
import sys

# Windows Encode Fix
# try:
#     sys.stdout.reconfigure(encoding='utf-8')
# except AttributeError:
#     pass

BASE_URL = "http://localhost:5001/api/search"


# Helper for safe printing
def safe_print(text):
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        # Fallback for terminals that can't handle emojis/utf-8
        print(text.encode('ascii', 'replace').decode('ascii'), flush=True)

def test_search(query, type_desc):
    safe_print(f"\n{'='*60}")
    safe_print(f"🔍 Testing [{type_desc}]: '{query}'")
    safe_print(f"{'='*60}")
    
    try:
        safe_print("... Sending request ...")
        response = requests.post(BASE_URL, json={"query": query}, timeout=30)
        if response.status_code != 200:
            safe_print(f"❌ Error: {response.status_code} - {response.text}")
            return
            
        data = response.json()
        results = data.get("results", [])
        recommendation = data.get("recommendation", "")
        
        safe_print(f"✅ Found {len(results)} projects.\n")
        
        # Print Recommendation
        if recommendation:
            safe_print(f"🤖 AI Recommendation:\n{'-'*20}\n{recommendation}\n{'-'*20}\n")
            
        # Print Top 5 Results (to show if we got remote ones)
        safe_print("📋 Top Results:")
        for i, p in enumerate(results[:5], 1):
            name = p.get('name', 'Unknown')
            desc = p.get('description', 'No description')
            rag_summary = p.get('ai_rag_summary', 'N/A')
            rag_snippet = rag_summary[:60] + "..." if rag_summary else "N/A"
            stars = p.get('stars', 0)
            
            source_tag = "[GitHub Live]" if "GitHub Live" in rag_summary else "[Local DB]"
            
            safe_print(f"{i}. {name} (⭐{stars}) {source_tag}")
            safe_print(f"   Desc: {desc[:80]}...")
            safe_print("")
            
    except Exception as e:
        safe_print(f"❌ Connection Error: {e}")
        safe_print("Make sure the server is running on port 5001")

if __name__ == "__main__":
    tests = [
        ("FastAPI", "Hybrid Check: Local or Remote?"),
        ("Generative UI Agents", "Rare Topic (Should trigger Remote Search)")
    ]
    
    for q, t in tests:
        test_search(q, t)
