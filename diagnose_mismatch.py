import sqlite3
import datetime
from config import Config

def diagnose():
    print(f"Connecting to {Config.DB_PATH}...")
    conn = sqlite3.connect(Config.DB_PATH)
    c = conn.cursor()
    year = datetime.datetime.now().year
    
    try:
        # Get Max Seq
        max_seq = c.execute("SELECT MAX(bill_seq) FROM bills").fetchone()[0] or 0
        print(f"MAX(bill_seq): {max_seq}")
        
        # Get Max Bill No suffix
        # SQLite doesn't have regex, so we iterate
        rows = c.execute("SELECT id, bill_no, bill_seq FROM bills WHERE bill_no LIKE ?", (f'B-{year}-%',)).fetchall()
        
        max_no_val = 0
        for row in rows:
            try:
                # B-2026-34 -> 34
                val = int(row[1].split('-')[-1])
                if val > max_no_val:
                    max_no_val = val
            except:
                pass
                
        print(f"MAX(bill_no suffix): {max_no_val}")
        
        if max_no_val > max_seq:
            print("MISMATCH DETECTED: Bill No suffix is ahead of Sequence Column.")
            print("Run FIX to align bill_seq with max_no_val?")
            
            # Auto-Fix option (since I can't prompt user interactively effectively)
            # Just do it? NO, I should separate fix.
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    diagnose()
