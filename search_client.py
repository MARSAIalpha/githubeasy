"""
Multi-Engine RAG Search Client for Local LLM
Supports: DuckDuckGo, GitHub, Brave (via SearXNG)
"""
import os
import sys
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
from openai import OpenAI

# Configuration
API_BASE = "http://198.18.0.1:1234/v1"
API_KEY = "lm-studio"

# SearXNG Configuration
# Set your own instance for best reliability, or leave as None to use public instances
# Example: "http://localhost:8080" or "https://your-searxng.example.com"
SEARXNG_INSTANCE = None  # <-- Set your own SearXNG instance here!

# Public SearXNG instances (fallback if no custom instance set)
SEARXNG_PUBLIC_INSTANCES = [
    "https://searx.be",
    "https://search.sapti.me",
    "https://paulgo.io",
    "https://searx.tiekoetter.com",
]

# ANSI Colors
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ============================================================
# SEARCH ENGINES
# ============================================================

def search_duckduckgo(query, max_results=3):
    """Search DuckDuckGo HTML version."""
    print(f"   {MAGENTA}[DDG]{RESET} Searching DuckDuckGo...")
    url = "https://html.duckduckgo.com/html/"
    payload = {'q': query}
    
    try:
        response = requests.post(url, data=payload, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        search_divs = soup.find_all('div', class_='result', limit=max_results)
        
        for i, div in enumerate(search_divs, 1):
            title_tag = div.find('a', class_='result__a')
            snippet_tag = div.find('a', class_='result__snippet')
            
            if title_tag:
                title = title_tag.get_text(strip=True)
                href = title_tag['href']
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else "No description"
                results.append({"title": title, "url": href, "snippet": snippet})

        return results
            
    except Exception as e:
        print(f"   {YELLOW}DDG Error: {e}{RESET}")
        return []


def search_github(query, max_results=5):
    """
    Search GitHub repositories using the public API (no auth required for basic search).
    Sorted by stars.
    """
    print(f"   {MAGENTA}[GitHub]{RESET} Searching GitHub repos...")
    
    # GitHub API for repo search
    url = "https://api.github.com/search/repositories"
    params = {
        'q': query,
        'sort': 'stars',
        'order': 'desc',
        'per_page': max_results
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for item in data.get('items', []):
            name = item.get('full_name', 'Unknown')
            url = item.get('html_url', '#')
            description = item.get('description', 'No description')
            stars = item.get('stargazers_count', 0)
            language = item.get('language', 'Unknown')
            
            snippet = f"⭐ {stars:,} | {language} | {description}"
            results.append({"title": name, "url": url, "snippet": snippet})
        
        return results
        
    except Exception as e:
        print(f"   {YELLOW}GitHub Error: {e}{RESET}")
        return []


def search_searxng(query, max_results=5, engines="google,bing,brave,duckduckgo"):
    """
    Search via SearXNG (self-hosted or public instances).
    SearXNG aggregates results from multiple search engines.
    
    Args:
        query: Search query
        max_results: Number of results
        engines: Comma-separated list of engines to use
    """
    print(f"   {MAGENTA}[SearXNG]{RESET} Searching via SearXNG...")
    
    # Build instance list: custom first, then public fallbacks
    instances = []
    if SEARXNG_INSTANCE:
        instances.append(SEARXNG_INSTANCE)
    instances.extend(SEARXNG_PUBLIC_INSTANCES)
    
    for instance in instances:
        try:
            url = f"{instance}/search"
            params = {
                'q': query,
                'format': 'json',
                'engines': engines,
                'language': 'auto'
            }
            
            print(f"      Trying: {instance}...")
            response = requests.get(url, params=params, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('results', [])[:max_results]:
                title = item.get('title', 'No Title')
                href = item.get('url', '#')
                snippet = item.get('content', 'No description')
                engine = item.get('engine', 'unknown')
                results.append({
                    "title": title, 
                    "url": href, 
                    "snippet": f"[{engine}] {snippet}"
                })
            
            if results:
                print(f"      {GREEN}Success! Got {len(results)} results from {instance}{RESET}")
                return results
                
        except requests.exceptions.Timeout:
            print(f"      {YELLOW}Timeout: {instance}{RESET}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"      {YELLOW}Error ({instance}): {e}{RESET}")
            continue
        except Exception as e:
            print(f"      {YELLOW}Parse error ({instance}): {e}{RESET}")
            continue
    
    print(f"   {YELLOW}All SearXNG instances failed.{RESET}")
    return []
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('results', [])[:max_results]:
                title = item.get('title', 'No Title')
                href = item.get('url', '#')
                snippet = item.get('content', 'No description')
                results.append({"title": title, "url": href, "snippet": snippet})
            
            if results:
                return results
                
        except Exception as e:
            print(f"   {YELLOW}SearXNG ({instance}) failed: {e}{RESET}")
            continue
    
    return []


# ============================================================
# SMART SEARCH ROUTER
# ============================================================

def detect_query_type(query):
    """Detect if query is asking for GitHub projects, news, or general info."""
    query_lower = query.lower()
    
    github_keywords = ['github', 'repo', 'repository', 'open source', 'library', 'framework', 
                       'package', 'star', 'fork', 'code', 'project', 'npm', 'pip', 'pypi']
    
    if any(kw in query_lower for kw in github_keywords):
        return 'github'
    
    return 'web'


def search_all(query, max_results=3):
    """
    Smart search that routes to appropriate engine based on query.
    Returns formatted string for LLM context.
    """
    print(f"\n{YELLOW}🔍 Searching for: '{query}'...{RESET}")
    
    query_type = detect_query_type(query)
    all_results = []
    
    if query_type == 'github':
        # For GitHub queries, search GitHub first
        gh_results = search_github(query, max_results=5)
        all_results.extend([("GitHub", r) for r in gh_results])
        
        # Also add some web context
        web_results = search_duckduckgo(query, max_results=2)
        all_results.extend([("Web", r) for r in web_results])
    else:
        # For general queries, use DuckDuckGo first, then fallback to Brave/SearXNG
        ddg_results = search_duckduckgo(query, max_results=max_results)
        
        if ddg_results:
            all_results.extend([("Web", r) for r in ddg_results])
        else:
            # Fallback to Brave/SearXNG
            brave_results = search_brave(query, max_results=max_results)
            all_results.extend([("Web", r) for r in brave_results])
    
    # Format results for LLM
    if not all_results:
        print(f"{YELLOW}⚠️ No search results found.{RESET}")
        return ""
    
    formatted = []
    for i, (source, result) in enumerate(all_results, 1):
        formatted.append(
            f"Source {i} [{source}]: [{result['title']}]({result['url']})\n"
            f"Content: {result['snippet']}\n"
        )
    
    print(f"   {GREEN}Found {len(all_results)} results.{RESET}")
    return "\n".join(formatted)


# ============================================================
# MAIN LOOP
# ============================================================

def main():
    client = OpenAI(base_url=API_BASE, api_key=API_KEY)

    print(f"{CYAN}╔══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}║   Local AI + Multi-Engine Internet Search (RAG Client)  ║{RESET}")
    print(f"{CYAN}╚══════════════════════════════════════════════════════════╝{RESET}")
    print(f"Connected to: {API_BASE}")
    print(f"Engines: DuckDuckGo, GitHub, Brave/SearXNG")
    print(f"Type 'exit' to quit.\n")

    while True:
        user_input = input(f"{GREEN}You: {RESET}").strip()
        
        if user_input.lower() in ['exit', 'quit']:
            break
        
        if not user_input:
            continue

        # Smart search
        search_context = search_all(user_input)
        
        # Construct System Prompt - be VERY explicit to prevent function-call hallucinations
        if search_context:
            system_prompt = (
                "You are a helpful AI assistant. I have already searched the internet for you. "
                "DO NOT attempt to search, browse, or call any functions. "
                "DO NOT output any special tokens, channels, or code blocks for tools. "
                "Simply answer the user's question directly using ONLY the search results provided below.\n\n"
                "SEARCH RESULTS:\n" + search_context + "\n\n"
                "NOW ANSWER THE USER'S QUESTION DIRECTLY IN PLAIN TEXT. Cite sources as [Source 1], [Source 2], etc."
            )
        else:
            system_prompt = (
                "You are a helpful AI assistant. Answer the user's question directly. "
                "DO NOT attempt to call any functions or output special tokens."
            )

        # Call Local AI
        print(f"{CYAN}🤖 AI is thinking...{RESET}")
        try:
            stream = client.chat.completions.create(
                model="local-model",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                stream=True,
                temperature=0.7,
            )

            print(f"{CYAN}AI: {RESET}", end="")
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    print(chunk.choices[0].delta.content, end="", flush=True)
            print("\n")

        except Exception as e:
            print(f"\n{YELLOW}❌ API Error: {e}{RESET}")
            print(f"Ensure LM Studio server is running at {API_BASE}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
