from rag_agent import search_web

print("Testing Web Search...")
results = search_web("python programming language", max_results=1)
if results:
    print("[V] Search Success!")
    print(f"Title: {results[0]['title']}")
else:
    print("[X] Search returned no results.")
