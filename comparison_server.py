"""
Multi-Engine RAG Search Comparison Server
Flask backend with real-time logging via SSE
"""
import os
import sys
import requests
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from openai import OpenAI
import concurrent.futures
import threading
import queue

# Global log queue for SSE
log_queue = queue.Queue()

# ============================================================
# CONFIGURATION
# ============================================================
API_BASE = "http://198.18.0.1:1234/v1"
API_KEY = "lm-studio"

SEARXNG_INSTANCE = None  # Set your own: "http://localhost:8080"
SEARXNG_PUBLIC_INSTANCES = [
    "https://baresearch.org",
    "https://find.xenorio.xyz",
    "https://grep.vim.wtf",
    "https://opnxng.com",
    "https://etsi.me",
    "https://searx.tiekoetter.com",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

app = Flask(__name__, static_folder='static')
CORS(app)

# ============================================================
# LOGGING
# ============================================================

def log_event(engine, message, level="info"):
    """Add log event to queue for SSE streaming."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {"time": timestamp, "engine": engine, "message": message, "level": level}
    log_queue.put(log_entry)
    print(f"[{timestamp}] [{engine}] {message}")


# ============================================================
# SEARCH ENGINES
# ============================================================

def search_duckduckgo(query, max_results=3):
    """Search DuckDuckGo HTML version."""
    log_event("DDG", f"Starting search...")
    url = "https://html.duckduckgo.com/html/"
    payload = {'q': query}
    
    try:
        response = requests.post(url, data=payload, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for div in soup.find_all('div', class_='result', limit=max_results):
            title_tag = div.find('a', class_='result__a')
            snippet_tag = div.find('a', class_='result__snippet')
            
            if title_tag:
                results.append({
                    "title": title_tag.get_text(strip=True),
                    "url": title_tag['href'],
                    "snippet": snippet_tag.get_text(strip=True) if snippet_tag else ""
                })
        
        log_event("DDG", f"Found {len(results)} results", "success" if results else "warning")
        return results if results else [{"error": "No DDG results"}]
    except Exception as e:
        log_event("DDG", f"Error: {str(e)}", "error")
        return [{"error": str(e)}]


def search_github(query, max_results=5):
    """Search GitHub repositories sorted by stars."""
    log_event("GitHub", f"Starting search...")
    url = "https://api.github.com/search/repositories"
    params = {'q': query, 'sort': 'stars', 'order': 'desc', 'per_page': max_results}
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = []
        
        for item in data.get('items', []):
            results.append({
                "title": item.get('full_name', 'Unknown'),
                "url": item.get('html_url', '#'),
                "snippet": f"Stars: {item.get('stargazers_count', 0):,} | {item.get('language', 'N/A')} | {item.get('description', '')}"
            })
        log_event("GitHub", f"Found {len(results)} repos", "success")
        return results
    except Exception as e:
        log_event("GitHub", f"Error: {str(e)}", "error")
        return [{"error": str(e)}]


def search_searxng(query, max_results=5):
    """Search via SearXNG instances."""
    log_event("SearXNG", f"Starting search...")
    instances = ([SEARXNG_INSTANCE] if SEARXNG_INSTANCE else []) + SEARXNG_PUBLIC_INSTANCES
    
    for instance in instances:
        try:
            log_event("SearXNG", f"Trying {instance}...")
            url = f"{instance}/search"
            params = {'q': query, 'format': 'json', 'engines': 'google,bing,brave'}
            response = requests.get(url, params=params, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = []
            
            for item in data.get('results', [])[:max_results]:
                results.append({
                    "title": item.get('title', 'No Title'),
                    "url": item.get('url', '#'),
                    "snippet": f"[{item.get('engine', '?')}] {item.get('content', '')}"
                })
            
            if results:
                log_event("SearXNG", f"Found {len(results)} results", "success")
                return results
        except Exception as e:
            log_event("SearXNG", f"{instance} failed: {str(e)[:50]}", "warning")
            continue
    
    log_event("SearXNG", "All instances failed", "error")
    return [{"error": "All SearXNG instances failed"}]


def search_bing_news(query, max_results=5):
    """Search Bing News via scraping."""
    log_event("BingNews", f"Starting search...")
    url = "https://www.bing.com/news/search"
    params = {'q': query, 'FORM': 'HDRSC6', 'qft': 'sortbydate%3d"1"'}
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Multiple selector strategies for Bing News
        selectors = [
            'div.news-card',
            'div.newsitem', 
            'article',
            'div[data-id]',
            'a.title'
        ]
        
        for selector in selectors:
            items = soup.select(selector)[:max_results]
            for item in items:
                # Try to extract title and link
                link = item if item.name == 'a' else item.select_one('a')
                if link:
                    title = link.get('title') or link.get_text(strip=True)
                    href = link.get('href', '#')
                    if title and len(title) > 5:
                        results.append({"title": title[:100], "url": href, "snippet": "Bing News"})
            
            if results:
                break
        
        log_event("BingNews", f"Found {len(results)} results", "success" if results else "warning")
        return results if results else [{"error": "No Bing News results - page structure may have changed"}]
    except Exception as e:
        log_event("BingNews", f"Error: {str(e)}", "error")
        return [{"error": str(e)}]


def search_hackernews(query, max_results=5):
    """Search Hacker News via Algolia API."""
    log_event("HackerNews", f"Starting search...")
    url = "https://hn.algolia.com/api/v1/search"
    params = {'query': query, 'tags': 'story', 'hitsPerPage': max_results}
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = []
        
        for hit in data.get('hits', []):
            title = hit.get('title', 'No Title')
            item_url = hit.get('url') or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
            points = hit.get('points', 0)
            comments = hit.get('num_comments', 0)
            
            results.append({
                "title": title,
                "url": item_url,
                "snippet": f"Points: {points} | Comments: {comments}"
            })
        
        log_event("HackerNews", f"Found {len(results)} results", "success" if results else "warning")
        return results if results else [{"error": "No HN results"}]
    except Exception as e:
        log_event("HackerNews", f"Error: {str(e)}", "error")
        return [{"error": str(e)}]


# ============================================================
# AI RESPONSE GENERATION
# ============================================================

def sanitize_text(text):
    """Remove special characters that might cause LLM parsing issues."""
    if not text:
        return ""
    # Remove or replace problematic characters
    import re
    # Remove markdown-like syntax and special chars
    text = re.sub(r'[<>{}|\[\]\\^~`]', '', str(text))
    # Replace emojis with text
    text = text.replace('⭐', 'Stars:').replace('🔥', '').replace('💬', 'Comments:')
    return text[:500]  # Limit length


def generate_ai_response(query, search_results, engine_name):
    """Generate AI response based on search results."""
    log_event(engine_name, "Generating AI response...")
    client = OpenAI(base_url=API_BASE, api_key=API_KEY)
    
    # Format search results with sanitized text
    context_parts = []
    for i, r in enumerate(search_results):
        if 'error' not in r:
            title = sanitize_text(r.get('title', 'N/A'))
            snippet = sanitize_text(r.get('snippet', ''))
            context_parts.append(f"Result {i+1}: {title}\n{snippet}")
    
    context = "\n\n".join(context_parts)
    
    if not context:
        log_event(engine_name, "No valid search results for AI", "warning")
        return {"engine": engine_name, "response": "No search results available.", "results": search_results}
    
    system_prompt = (
        "You are a helpful AI assistant.\n\n"
        f"I searched using {engine_name} and got these results:\n\n"
        f"{context}\n\n"
        "Answer the user's question based on these search results.\n"
        "Cite sources as [Source 1], [Source 2], etc.\n"
        "Be concise and informative."
    )
    
    try:
        response = client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.7,
            max_tokens=500
        )
        log_event(engine_name, "AI response complete", "success")
        return {
            "engine": engine_name,
            "response": response.choices[0].message.content,
            "results": search_results
        }
    except Exception as e:
        log_event(engine_name, f"AI Error: {str(e)}", "error")
        return {
            "engine": engine_name,
            "response": f"AI Error: {str(e)}",
            "results": search_results
        }


# ============================================================
# API ROUTES
# ============================================================

@app.route('/')
def index():
    return send_from_directory('.', 'comparison_ui.html')

@app.route('/api/logs')
def stream_logs():
    """SSE endpoint for real-time logs."""
    def generate():
        while True:
            try:
                log_entry = log_queue.get(timeout=30)
                yield f"data: {json.dumps(log_entry)}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'ping': True})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/compare', methods=['POST'])
def compare_search():
    """Run all 5 searches in parallel and generate AI responses."""
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    log_event("System", f"Starting comparison for: {query}")
    
    # Parallel search (5 engines)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            'ddg': executor.submit(search_duckduckgo, query),
            'github': executor.submit(search_github, query),
            'searxng': executor.submit(search_searxng, query),
            'bingnews': executor.submit(search_bing_news, query),
            'hackernews': executor.submit(search_hackernews, query),
        }
        
        search_results = {k: f.result() for k, f in futures.items()}
    
    log_event("System", "All searches complete, generating AI responses...")
    
    # Parallel AI generation
    engine_names = {
        'ddg': 'DuckDuckGo',
        'github': 'GitHub', 
        'searxng': 'SearXNG',
        'bingnews': 'Bing News',
        'hackernews': 'Hacker News'
    }
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        ai_futures = {
            k: executor.submit(generate_ai_response, query, results, engine_names[k])
            for k, results in search_results.items()
        }
        
        responses = [f.result() for f in ai_futures.values()]
    
    log_event("System", "All AI responses complete")
    return jsonify({"query": query, "responses": responses})


@app.route('/api/search/<engine>', methods=['POST'])
def single_search(engine):
    """Search a single engine."""
    data = request.json
    query = data.get('query', '')
    
    if engine == 'duckduckgo':
        results = search_duckduckgo(query)
    elif engine == 'github':
        results = search_github(query)
    elif engine == 'searxng':
        results = search_searxng(query)
    elif engine == 'bingnews':
        results = search_bing_news(query)
    elif engine == 'hackernews':
        results = search_hackernews(query)
    else:
        return jsonify({"error": "Unknown engine"}), 400
    
    return jsonify({"engine": engine, "results": results})


if __name__ == '__main__':
    print("\n" + "="*60)
    print("=== Search Comparison Server with Real-time Logs ===")
    print("Base URL: http://localhost:5000")
    print("Open http://localhost:5000 in your browser")
    print("Logs: http://localhost:5000/api/logs (SSE stream)")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
