import sqlite3
from config import Config

def diagnose():
    print(f"Connecting to {Config.DB_PATH}...")
    conn = sqlite3.connect(Config.DB_PATH)
    c = conn.cursor()
    
    try:
        # Check Max Seq
        max_seq = c.execute("SELECT MAX(bill_seq) FROM bills").fetchone()[0]
        print(f"MAX(bill_seq): {max_seq}")
        
        # Check for potential conflicts
        # Bills that look like 'B-%' but have NULL bill_seq
        conflicts = c.execute("SELECT id, bill_no, status FROM bills WHERE bill_no LIKE 'B-%' AND bill_seq IS NULL").fetchall()
        
        if conflicts:
            print(f"FOUND {len(conflicts)} CONFLICTING BILLS (B- prefix but NULL seq):")
            for row in conflicts:
                print(row)
        else:
            print("No bills found with 'B-' prefix and NULL sequence.")
            
        # Check for Drafts
        drafts = c.execute("SELECT id, bill_no, status FROM bills WHERE status='draft'").fetchall()
        print(f"Found {len(drafts)} drafts.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    diagnose()
