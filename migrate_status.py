import sqlite3
from config import Config

def migrate():
    print(f"Connecting to {Config.DB_PATH}...")
    conn = sqlite3.connect(Config.DB_PATH)
    c = conn.cursor()
    
    try:
        # Check columns in bills
        c.execute("PRAGMA table_info(bills)")
        columns = [row[1] for row in c.fetchall()]
        print(f"Current columns: {columns}")
        
        if 'status' not in columns:
            print("Adding 'status' column to bills table...")
            c.execute("ALTER TABLE bills ADD COLUMN status TEXT DEFAULT 'printed'")
            conn.commit()
            print("Migration successful: status column added.")
        else:
            print("'status' column already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
