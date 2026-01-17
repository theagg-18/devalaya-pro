import sqlite3
from config import Config

def migrate():
    print(f"Connecting to {Config.DB_PATH}...")
    conn = sqlite3.connect(Config.DB_PATH)
    c = conn.cursor()
    
    try:
        # Check columns
        c.execute("PRAGMA table_info(bills)")
        columns = [row[1] for row in c.fetchall()]
        print(f"Current columns: {columns}")
        
        if 'bill_seq' not in columns:
            print("Adding 'bill_seq' column to bills table...")
            c.execute("ALTER TABLE bills ADD COLUMN bill_seq INTEGER")
            conn.commit()
            print("Migration successful: bill_seq added.")
            
            # Optional: Backfill existing printed bills
            print("Backfilling sequence for existing printed bills...")
            rows = c.execute("SELECT id FROM bills WHERE status='printed' ORDER BY created_at ASC").fetchall()
            for idx, row in enumerate(rows):
                seq = idx + 1
                c.execute("UPDATE bills SET bill_seq = ? WHERE id = ?", (seq, row[0]))
            conn.commit()
            print(f"Backfilled {len(rows)} bills.")
            
        else:
            print("'bill_seq' column already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
