import requests
import sys

# Windows Encode Fix
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

GITHUB_API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def debug_fetch(url):
    print(f"Testing URL: {url}")
    
    parts = url.rstrip('/').split('/')
    if len(parts) < 2:
        print("❌ URL parse failed: too short")
        return
        
    repo_full_name = f"{parts[-2]}/{parts[-1]}"
    print(f"Parsed Repo Name: {repo_full_name}")
    
    api_url = f"{GITHUB_API}/repos/{repo_full_name}"
    print(f"Requesting API: {api_url}")
    
    try:
        response = requests.get(api_url, headers=HEADERS, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success! Data fetched.")
            data = response.json()
            print(f"Name: {data.get('name')}")
            print(f"Stars: {data.get('stargazers_count')}")
        else:
            print(f"❌ Failed. Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def debug_scrape_html(url):
    print(f"\nTesting HTML Scrape: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success! HTML fetched.")
            # Simple check for keywords
            if "<title>" in response.text:
                 print("Found <title> tag")
            
            # Try to find description
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Stars (Often in a span with id or specific class, fragile but worth a try)
            # GitHub moves classes around, but usually 'star-count' or checking aria-label on star button
            # Better: use meta tags
            og_desc = soup.find("meta", property="og:description")
            if og_desc:
                print(f"OG Description: {og_desc['content']}")
                
            # Stars are harder to find reliably in HTML without classes, but let's try finding the number
            # usually in the Counter span inside the Star button
            # This is just a debug test
            
        else:
            print(f"❌ Failed. Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    url = "https://github.com/JimmyLv/BibiGPT-v1"
    debug_fetch(url)
    debug_scrape_html(url)
