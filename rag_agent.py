import os
from ddgs import DDGS
from openai import OpenAI

# ==============================================================================
# CONFIGURATION
# ==============================================================================
# Default to localhost if running on the same machine.
# If running this script from a DIFFERENT machine, change this IP to the AI395 IP.
# Example: "http://192.168.1.X:1234/v1"
LM_STUDIO_API_BASE = "http://localhost:1234/v1"
LM_STUDIO_API_KEY = "lm-studio" # Not typically checked by local server, but required by client

def search_web(query, max_results=3):
    """
    Searches the web using DuckDuckGo (Free, no API key).
    Returns a list of result dictionaries.
    """
    print(f"\n[SEARCH] Searching the web for: '{query}'...")
    results = []
    try:
        with DDGS() as ddgs:
            # text() returns a generator, we take 'max_results' items
            ddgs_gen = ddgs.text(query, max_results=max_results)
            for r in ddgs_gen:
                results.append(r)
    except Exception as e:
        print(f"[Error] Search failed: {e}")
    
    return results

def format_context(search_results):
    """Turns search results into a text block for the LLM."""
    if not search_results:
        return "No current news found."
    
    context_str = "Here is the latest information found on the web:\n\n"
    for i, res in enumerate(search_results, 1):
        context_str += f"Source {i}: {res['title']}\n"
        context_str += f"Content: {res['body']}\n"
        context_str += f"Link: {res['href']}\n\n"
    
    return context_str

def rag_query_local_llm(user_question):
    """
    1. Searches web for the question.
    2. Sends context + question to Local LLM.
    """
    # 1. Retrieve
    results = search_web(user_question)
    context = format_context(results)
    
    print(f"[CONTEXT] Retrieved {len(results)} sources.")
    
    # 2. Augment (Create Prompt)
    system_prompt = (
        "You are a helpful News Assistant. "
        "Use the provided 'Web Search Results' to answer the user's question accurately. "
        "If the answer isn't in the results, say you don't know."
    )
    
    user_prompt = f"""
    Web Search Results:
    {context}
    
    User Question: {user_question}
    """
    
    # 3. Generate
    print("[AI] Querying Local Model...")
    try:
        client = OpenAI(base_url=LM_STUDIO_API_BASE, api_key=LM_STUDIO_API_KEY)
        
        completion = client.chat.completions.create(
            model="local-model", # The ID is usually ignored by LM Studio in single-model mode
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )
        
        answer = completion.choices[0].message.content
        print("\n" + "="*50)
        print("AI ANSWER:")
        print("="*50)
        print(answer)
        print("="*50)
        
    except Exception as e:
        print(f"\n[CONNECTION ERROR] Could not talk to LM Studio at {LM_STUDIO_API_BASE}")
        print(f"Details: {e}")
        print("TIP: Make sure LM Studio Local Server is running and listening on the correct port.")

if __name__ == "__main__":
    # Test Interaction
    print("=== Local RAG System (News Agent) ===")
    print(f"Connecting to: {LM_STUDIO_API_BASE}")
    
    while True:
        q = input("\nEnter a topic to search (or 'q' to quit): ")
        if q.lower() in ['q', 'quit', 'exit']:
            break
        rag_query_local_llm(q)
