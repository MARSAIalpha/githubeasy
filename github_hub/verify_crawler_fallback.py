import sys
from crawler import CrawlerAgent

# Windows Encode Fix
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def verify_fallback():
    print("=== Verifying Crawler Fallback ===")
    crawler = CrawlerAgent()
    
    # URL known to fail with 403 in the previous debug run
    url = "https://github.com/JimmyLv/BibiGPT-v1"
    
    print(f"Fetching {url}...")
    # This should trigger the 403 (hopefully) or just work if rate limit reset, 
    # but we want to confirm it returns a valid project dict regardless.
    project = crawler.fetch_project_by_url(url)
    
    if project:
        print("✅ Project Fetched Successfully!")
        print(f"Name: {project.get('name')}")
        print(f"Description: {project.get('description')}")
        print(f"Category: {project.get('category')}") # Should be 'manual' or 'manual_scraped'
        
        if project.get('category') == 'manual_scraped':
            print("🎉 Verified: Fallback mechanism was used (HTML Scrape).")
        else:
            print("ℹ️ Note: API worked normal (Rate limit might have reset). Fallback not triggered but basic functionality is OK.")
    else:
        print("❌ Failed to fetch project.")

if __name__ == "__main__":
    verify_fallback()
