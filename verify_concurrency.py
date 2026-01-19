
import sqlite3
import threading
import time
import random
import os

DB_PATH = "concurrent_test.db"

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('CREATE TABLE bills (id INTEGER PRIMARY KEY AUTOINCREMENT, bill_seq INTEGER, bill_no TEXT UNIQUE)')
    conn.commit()
    conn.close()

def create_bill(thread_id):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    success = False
    
    for attempt in range(5):
        try:
            # 1. Get Latest Sequence
            # We use 'BEGIN IMMEDIATE' to simulate the safest locking, 
            # BUT our app code uses default which relies on Retry Loop catching IntegrityError.
            # So let's simulate the IntegrityError race condition:
            # We intentionally DON'T use BEGIN IMMEDIATE here to prove the retry loop works
            # even with weak locking.
            
            cursor = conn.execute('SELECT MAX(bill_seq) FROM bills')
            last_seq = cursor.fetchone()[0] or 0
            new_seq = last_seq + 1
            bill_no = f"B-2024-{new_seq}"
            
            # Artificial delay to force collision
            time.sleep(random.uniform(0.001, 0.005))
            
            conn.execute('INSERT INTO bills (bill_seq, bill_no) VALUES (?, ?)', (new_seq, bill_no))
            conn.commit()
            print(f"Thread {thread_id}: Success {bill_no}")
            success = True
            break
        except sqlite3.IntegrityError:
            print(f"Thread {thread_id}: Collision on {new_seq}, retrying...")
            time.sleep(random.uniform(0.001, 0.01))
            continue
            
    conn.close()
    return success

init_db()
threads = []
for i in range(10):
    t = threading.Thread(target=create_bill, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

# Verify
conn = sqlite3.connect(DB_PATH)
count = conn.execute('SELECT count(*) FROM bills').fetchone()[0]
print(f"Total Bills: {count}")
conn.close()
