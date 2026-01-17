import sqlite3
from config import Config

def migrate():
    print(f"Connecting to {Config.DB_PATH}...")
    conn = sqlite3.connect(Config.DB_PATH)
    c = conn.cursor()
    
    try:
        # Check if type column exists
        c.execute("PRAGMA table_info(bills)")
        columns = [row[1] for row in c.fetchall()]
        
        if 'type' not in columns:
            print("Adding 'type' column to bills table...")
            c.execute("ALTER TABLE bills ADD COLUMN type TEXT DEFAULT 'vazhipadu'")
            conn.commit()
            print("Migration successful.")
        else:
            print("'type' column already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
