from crawler import CrawlerAgent
import time
import requests

def debug_query():
    print("=== Debugging GitHub Search API ===")
    crawler = CrawlerAgent()
    
    # 1. Test Trending
    print("\n[1] Testing Trending Query...")
    try:
        results = crawler.get_trending()
        print(f"Trending results: {len(results)}")
        if len(results) == 0:
            # Manually run the query to see the error
            offset_date = crawler._get_date_offset(7)
            query = f"stars:>1000 pushed:>{offset_date}"
            url = f"https://api.github.com/search/repositories"
            params = {"q": query, "sort": "stars", "order": "desc", "per_page": 30}
            resp = requests.get(url, headers=crawler.headers, params=params)
            print(f"Status Code: {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
    except Exception as e:
        print(f"Trending Error: {e}")

    time.sleep(2)

    # 2. Test New Releases
    print("\n[2] Testing New Releases Query...")
    try:
        results = crawler.get_new_releases()
        print(f"New Releases results: {len(results)}")
        if len(results) == 0:
             # Manually run
            offset_date = crawler._get_date_offset(30)
            query = f"stars:>100 created:>{offset_date}"
            url = f"https://api.github.com/search/repositories"
            params = {"q": query, "sort": "stars", "order": "desc", "per_page": 30}
            resp = requests.get(url, headers=crawler.headers, params=params)
            print(f"Status Code: {resp.status_code}")
            print(f"Response: {resp.json()}")
    except Exception as e:
        print(f"New Releases Error: {e}")

if __name__ == "__main__":
    debug_query()
