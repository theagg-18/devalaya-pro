import sqlite3
import os
from flask import g
from config import Config

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            Config.DB_PATH,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        
        # Optimize performance
        g.db.execute('PRAGMA journal_mode=WAL;')
        g.db.execute('PRAGMA synchronous=NORMAL;')
        g.db.execute('PRAGMA foreign_keys=ON;')

    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # 1. Temple Settings
    c.execute('''
        CREATE TABLE IF NOT EXISTS temple_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            name_mal TEXT NOT NULL,
            name_eng TEXT,
            place TEXT,
            receipt_footer TEXT,
            backup_enabled INTEGER DEFAULT 0
        )
    ''')
    
    # Ensure at least one setting row exists
    c.execute('SELECT count(*) FROM temple_settings')
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO temple_settings (id, name_mal, name_eng, place, receipt_footer)
            VALUES (1, 'TEMPLE NAME', 'Temple Name', 'Place', 'Thank You')
        ''')

    # 2. Printers
    c.execute('''
        CREATE TABLE IF NOT EXISTS printers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            friendly_name TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')

    # 3. Users (Admin/Cashier)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            pin TEXT, 
            role TEXT NOT NULL CHECK(role IN ('admin', 'cashier')),
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Seed default admin if not exists
    c.execute('SELECT count(*) FROM users WHERE role="admin"')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO users (username, pin, role) VALUES (?, ?, ?)', ('admin', '1234', 'admin'))

    # 4. Puja/Item Master
    c.execute('''
        CREATE TABLE IF NOT EXISTS puja_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT DEFAULT 'puja' CHECK(type IN ('puja', 'item')),
            is_active INTEGER DEFAULT 1
        )
    ''')

    # 5. Bills
    c.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_no TEXT UNIQUE,
            bill_seq INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scheduled_date DATE,
            cashier_id INTEGER,
            printer_id INTEGER,
            total_amount REAL NOT NULL,
            devotee_name TEXT,
            star TEXT,
            type TEXT DEFAULT 'vazhipadu',
            status TEXT DEFAULT 'printed',
            FOREIGN KEY(cashier_id) REFERENCES users(id)
        )
    ''') 

    # Migration: Add scheduled_date if missing
    c.execute("PRAGMA table_info(bills)")
    columns = [row[1] for row in c.fetchall()]
    if 'scheduled_date' not in columns:
        c.execute("ALTER TABLE bills ADD COLUMN scheduled_date DATE")
    
    # Migration: Add bill_seq if missing (safety check)
    if 'bill_seq' not in columns:
        c.execute("ALTER TABLE bills ADD COLUMN bill_seq INTEGER")

    # 6. Bill Items
    c.execute('''
        CREATE TABLE IF NOT EXISTS bill_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER NOT NULL,
            puja_id INTEGER NOT NULL,
            price_snapshot REAL NOT NULL,
            count INTEGER DEFAULT 1,
            total REAL NOT NULL,
            FOREIGN KEY(bill_id) REFERENCES bills(id),
            FOREIGN KEY(puja_id) REFERENCES puja_master(id)
        )
    ''')

    # 7. Cashier Sessions (for tracking printer assignment)
    c.execute('''
        CREATE TABLE IF NOT EXISTS cashier_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cashier_id INTEGER NOT NULL,
            printer_id INTEGER,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY(cashier_id) REFERENCES users(id),
            FOREIGN KEY(printer_id) REFERENCES printers(id)
        )
    ''')

    conn.commit()
    conn.close()
