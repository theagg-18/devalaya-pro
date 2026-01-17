import sqlite3
import datetime
from config import Config

def fix():
    print(f"Connecting to {Config.DB_PATH}...")
    conn = sqlite3.connect(Config.DB_PATH)
    c = conn.cursor()
    year = datetime.datetime.now().year
    
    try:
        # Get all bills with matching year format
        # Filter for printed only? Or just any that have a B- No.
        rows = c.execute("SELECT id, bill_no, bill_seq FROM bills WHERE bill_no LIKE ?", (f'B-{year}-%',)).fetchall()
        
        print(f"Found {len(rows)} bills to check.")
        
        changes = 0
        for row in rows:
            b_id = row[0]
            b_no = row[1]
            b_seq = row[2]
            
            try:
                # Extract 34 from B-2024-34
                correct_seq = int(b_no.split('-')[-1])
                
                if b_seq != correct_seq:
                    print(f"Fixing ID {b_id}: Seq {b_seq} -> {correct_seq}")
                    c.execute("UPDATE bills SET bill_seq = ? WHERE id = ?", (correct_seq, b_id))
                    changes += 1
            except:
                print(f"Skipping malformed: {b_no}")
                
        conn.commit()
        print(f"Fixed {changes} bills.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix()
