import sqlite3
from config import Config

def migrate():
    print(f"Connecting to {Config.DB_PATH}...")
    conn = sqlite3.connect(Config.DB_PATH)
    c = conn.cursor()
    
    try:
        # Check if column exists
        c.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in c.fetchall()]
        
        if 'is_active' not in columns:
            print("Adding 'is_active' column to users table...")
            c.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
            conn.commit()
            print("Migration successful.")
        else:
            print("'is_active' column already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
