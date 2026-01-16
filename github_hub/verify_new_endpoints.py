import requests
import json
import time
import sys

# Force UTF-8 encoding for Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

BASE_URL = "http://localhost:5001"

def print_section(title):
    print(f"\n{'='*50}")
    try:
        print(f"🧪 Testing: {title}")
    except UnicodeEncodeError:
        print(f"Testing: {title}")
    print(f"{'='*50}")

def test_refine_agent():
    print_section("/api/agent/refine")
    
    # Scene 1: Vague intent (expecting a question)
    history_vague = [{"role": "user", "content": "I want a crawler"}]
    try:
        res = requests.post(f"{BASE_URL}/api/agent/refine", json={"history": history_vague})
        data = res.json()
        print(f"Input: 'I want a crawler'")
        print(f"Action: {data.get('action')}")
        print(f"Content: {data.get('content')}")
        if data.get('action') == 'question':
            print("✅ Pass: Agent asked a clarifying question.")
        else:
            print(f"⚠️ Warning: Agent did not ask a question (Got {data.get('action')})")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("-" * 30)

    # Scene 2: Specific intent (expecting search)
    history_specific = [
        {"role": "user", "content": "I want a crawler"},
        {"role": "assistant", "content": "What language?"},
        {"role": "user", "content": "Python, for news sites"}
    ]
    try:
        res = requests.post(f"{BASE_URL}/api/agent/refine", json={"history": history_specific})
        data = res.json()
        print(f"Input: History ending in 'Python, for news sites'")
        print(f"Action: {data.get('action')}")
        content = data.get('content', '')
        print(f"Content: {content}")
        
        if data.get('action') == 'search':
            print("✅ Pass: Agent decided to search.")
            # Quality Check
            if "language:" in content or "pushed:" in content:
                print("✅ Pass: Query contains advanced qualifiers.")
            else:
                print("⚠️ Warning: Query is simple (missing language/pushed filters).")
        else:
            print(f"⚠️ Warning: Agent did not search (Got {data.get('action')})")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_local_search():
    print_section("/api/search/local")
    query = "FastAPI" 
    try:
        start = time.time()
        res = requests.post(f"{BASE_URL}/api/search/local", json={"query": query})
        data = res.json()
        duration = time.time() - start
        
        results = data.get('results', [])
        print(f"Query: '{query}'")
        print(f"Found: {len(results)} projects in {duration:.2f}s")
        
        if len(results) > 0:
            print(f"First result: {results[0].get('name')}")
        
        print("✅ Pass: Local search responded.")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_remote_search():
    print_section("/api/search/remote")
    # Query with filters to test bypass logic
    query = "crawler language:python stars:>1000 -tutorial"
    try:
        print(f"Sending remote search request for: '{query}'")
        start = time.time()
        res = requests.post(f"{BASE_URL}/api/search/remote", json={"query": query})
        data = res.json()
        duration = time.time() - start
        
        results = data.get('results', [])
        print(f"Found: {len(results)} projects in {duration:.2f}s")
        
        if len(results) > 0:
            for i, p in enumerate(results[:3]):
                print(f"{i+1}. {p.get('name')} (⭐{p.get('stars')}): {p.get('description')[:50]}...")
                
            if "GitHub Live" in str(results[0].get('ai_rag_summary', '')):
                print("✅ Pass: Result marked as GitHub Live.")
        else:
            print("⚠️ Note: No results found (GitHub API rate limit or empty?)")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Starting Endpoint Verification...")
    test_local_search()
    test_refine_agent()
    test_remote_search()
