import requests
import json
import sys

# Force UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def test_remote_only():
    url = "http://localhost:5001/api/search/remote"
    
    # Simulate a "refined" query from the Analyzer
    # User said "Python crawler", Analyzer produced "crawler language:python pushed:>2024-01-01"
    query = "crawler language:python pushed:>2024-01-01"
    
    print(f"Testing Remote Search with refined query: '{query}'")
    
    try:
        res = requests.post(url, json={"query": query})
        data = res.json()
        results = data.get('results', [])
        
        print(f"Found {len(results)} projects.")
        
        for i, p in enumerate(results[:5]):
            print(f"{i+1}. {p['name']} (⭐{p['stars']})")
            print(f"   Desc: {p.get('description', '')[:60]}...")
            
        # Check for spam
        spam_keywords = ["book", "interview", "tutorial", "list"]
        spam_count = sum(1 for p in results if any(k in p['name'].lower() or k in (p.get('description') or '').lower() for k in spam_keywords))
        
        if spam_count == 0:
            print("✅ Quality Check Passed: No obvious spam/books found.")
        else:
            print(f"⚠️ Warning: Found {spam_count} potential spam items.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_remote_only()
