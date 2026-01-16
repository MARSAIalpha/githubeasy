import threading
import time
import random
from database import Database

def test_concurrency():
    print("Initializing Database...")
    db = Database("data/test_concurrency.db")
    db.clear_database()
    
    errors = []
    
    def writer_task(n):
        try:
            for i in range(50):
                project = {
                    "id": f"p_{n}_{i}",
                    "name": f"Project {n}-{i}",
                    "full_name": f"user/project_{n}_{i}",
                    "category": "test",
                    "stars": random.randint(0, 1000),
                    "forks": 0,
                    "url": "http://example.com"
                }
                db.upsert_project(project)
                
                # Also update something else
                if i % 5 == 0:
                    db.update_ai_analysis(f"p_{n}_{i}", {"summary": "Updated analysis"})
                    
                # time.sleep(0.01) # Simulate some work
        except Exception as e:
            print(f"Writer {n} Error: {e}")
            errors.append(e)

    def reader_task(n):
        try:
            for i in range(50):
                db.get_projects_by_category("test", limit=10)
                db.get_all_categories_summary()
                # time.sleep(0.01)
        except Exception as e:
            print(f"Reader {n} Error: {e}")
            errors.append(e)

    print("Starting concurrent threads...")
    threads = []
    
    # Spawn 5 writers and 5 readers
    for i in range(5):
        t = threading.Thread(target=writer_task, args=(i,))
        threads.append(t)
        t.start()
        
    for i in range(5):
        t = threading.Thread(target=reader_task, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    print(f"Test Finished. Errors: {len(errors)}")
    if len(errors) == 0:
        print("✅ SUCCESS: No database locked errors with high concurrency.")
    else:
        print("❌ FAILED: Errors occurred.")
        for e in errors:
            print(e)
            
    db.close()

if __name__ == "__main__":
    test_concurrency()
