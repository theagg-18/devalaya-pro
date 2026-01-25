import sys
import os
# Ensure root dir is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, g
from database import get_db, get_cached_settings, init_db
from modules.panchang import get_nakshatra
import datetime
import time

app = Flask(__name__)
from config import Config
app.config.from_object(Config)

def verify():
    print("--- Starting Verification ---")
    with app.app_context():
        # Ensure DB is init
        init_db()
        
        # 1. Check Indexes
        db = get_db()
        indices = db.execute("PRAGMA index_list('bills')").fetchall()
        print("\n[Indexes on 'bills']")
        found_idx = [row['name'] for row in indices]
        for name in found_idx:
            print(f" - {name}")
        
        required = ['idx_bills_created_at', 'idx_bills_payment_status']
        for r in required:
            if r in found_idx:
                print(f"[PASS] Found {r}")
            else:
                print(f"[FAIL] Missing {r}")

        # 2. Check Cache Size Pragma
        # Need to re-open explicit connection or use get_db which sets it
        # sqlite cache_size is usually pages. standard page is 4096 bytes.
        # -64000 KB = 64MB.
        # If set to positive N, it is N pages.
        # PRAGMA cache_size returns number of pages.
        # So if we set -64000, it sets roughly 16000 pages (if page size 4096).
        row = db.execute("PRAGMA cache_size").fetchone()
        cache_size = row[0]
        print(f"\n[SQLite Cache] Size: {cache_size} pages")
        # We just want to ensure it's not the default 2000 (-2000kb)
        if abs(cache_size) > 2000:
             print("[PASS] Cache size increased")
        else:
             print("[WARN] Cache size might be default")

        # 3. Check Settings Cache
        print("\n[Settings Cache]")
        s1 = get_cached_settings()
        s2 = get_cached_settings()
        if s1 is s2:
            print(f"[PASS] Settings cache returned identical object ID: {id(s1)}")
        else:
            print(f"[FAIL] Settings cache returned different objects: {id(s1)} vs {id(s2)}")

        # 4. Check Panchang Cache
        print("\n[Panchang Cache]")
        today = datetime.date.today()
        
        t0 = time.time()
        n1 = get_nakshatra(today)
        t1 = time.time()
        print(f"Call 1 (Cold): {t1-t0:.4f}s")
        
        t2 = time.time()
        n2 = get_nakshatra(today)
        t3 = time.time()
        print(f"Call 2 (Cached): {t3-t2:.4f}s")
        
        info = get_nakshatra.cache_info()
        print(f"Cache Info: {info}")
        if info.hits >= 1:
             print("[PASS] Hit count incremented")
        else:
             print("[FAIL] Hit count not incremented")

if __name__ == "__main__":
    verify()
