import requests
import json
import sys

# Windows Encode Fix
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

BASE_URL = "http://localhost:5001"

def test_vague_input(query, expected_action="question"):
    print(f"\n🧪 Testing Vague Input: '{query}'")
    
    history = [{"role": "user", "content": query}]
    try:
        res = requests.post(f"{BASE_URL}/api/agent/refine", json={"history": history})
        data = res.json()
        
        action = data.get('action')
        content = data.get('content')
        reasoning = data.get('reasoning')
        
        print(f"Action: {action}")
        print(f"Content: {content}")
        print(f"Reasoning: {reasoning}")
        
        if action == expected_action:
            print(f"✅ Pass: Correctly decided to '{expected_action}'")
        else:
            print(f"❌ Fail: Expected '{expected_action}' but got '{action}'")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=== Verifying Proactive Agent Behavior ===")
    
    # Case 1: Extremely Vague
    test_vague_input("I want a crawler")
    
    # Case 2: Partial Info (Has Language, missing context/features)
    test_vague_input("Python crawler")
    
    # Case 3: Almost Complete (Has Language + Scenario, missing features?) -> Might search or ask
    # Let's see how strict we made it. The prompt says "If ANY ... missing ... MUST ask".
    test_vague_input("Python crawler for news sites", "question")
    
    # Case 4: Explicit "Just Search" command
    test_vague_input("Search for python crawler", "search")
