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
            backup_enabled INTEGER DEFAULT 0,
            print_template_content TEXT,
            subtitle_mal TEXT,
            subtitle_eng TEXT
        )
    ''')
    
    # Ensure at least one setting row exists
    c.execute('SELECT count(*) FROM temple_settings')
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO temple_settings (id, name_mal, name_eng, place, receipt_footer)
            VALUES (1, 'TEMPLE NAME', 'Temple Name', 'Place', 'Thank You')
        ''')

    # Migration: Add print_template_content if missing
    c.execute("PRAGMA table_info(temple_settings)")
    setting_cols = [row[1] for row in c.fetchall()]
    
    # Check for subtitles
    if 'subtitle_mal' not in setting_cols:
        c.execute("ALTER TABLE temple_settings ADD COLUMN subtitle_mal TEXT")
    if 'subtitle_eng' not in setting_cols:
        c.execute("ALTER TABLE temple_settings ADD COLUMN subtitle_eng TEXT")
    
    # Check for color_theme
    if 'color_theme' not in setting_cols:
        c.execute("ALTER TABLE temple_settings ADD COLUMN color_theme TEXT DEFAULT 'kerala'")
        
    if 'custom_theme_colors' not in setting_cols:
        # Default to a safe fallback JSON
        import json
        default_custom = json.dumps({
            'primary': '#000000',
            'secondary': '#ffffff',
            'background': '#f0f0f0',
            'success': '#00ff00'
        })
        c.execute("ALTER TABLE temple_settings ADD COLUMN custom_theme_colors TEXT")
        c.execute("UPDATE temple_settings SET custom_theme_colors = ?", (default_custom,))

    if 'logo_path' not in setting_cols:
        c.execute("ALTER TABLE temple_settings ADD COLUMN logo_path TEXT")

    # Set default template (Defined here so it's available for updates)
    default_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Receipt</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Malayalam:wght@400;700;900&display=swap');

        body {
            margin: 0;
            padding: 0;
            font-family: 'Inter', 'Noto Sans Malayalam', sans-serif;
            background: #fff;
            color: #000;
            -webkit-font-smoothing: antialiased;
        }

        .receipt-container {
            width: 80mm;
            margin: 0 auto;
            box-sizing: border-box;
        }

        .slip {
            width: 80mm;
            padding: 4mm;
            box-sizing: border-box;
            page-break-after: always;
            border-bottom: 1.5px dashed #000;
            margin-bottom: 10px;
        }

        .slip:last-child {
            border-bottom: none;
            margin-bottom: 0;
        }

        /* --- VISUAL HIERARCHY --- */

        .header {
            text-align: center;
            margin-bottom: 10px;
        }

        .temple-name-mal {
            font-size: 22px;
            font-weight: 900;
            margin: 0;
            line-height: 1.1;
        }

        .temple-name-eng {
            font-size: 14px;
            font-weight: 700;
            margin: 4px 0 0 0;
            text-transform: uppercase;
        }

        .meta-section {
            font-size: 12px;
            border-top: 1px solid #000;
            border-bottom: 1px solid #000;
            margin: 8px 0;
            padding: 5px 0;
        }

        .meta-row {
            display: flex;
            justify-content: space-between;
        }

        .devotee-highlight {
            margin: 12px 0;
            text-align: center;
            padding: 6px;
            border: 1px solid #000;
            border-radius: 4px;
        }

        .devotee-name {
            font-size: 20px;
            font-weight: 800;
            display: block;
        }

        .star-name {
            font-size: 18px;
            font-weight: 700;
            display: block;
        }

        /* --- SINGLE ITEM FOCUS --- */
        .item-container {
            margin: 15px 0;
            padding: 10px 0;
            border-bottom: 2px solid #000;
        }

        .item-label {
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            display: block;
            margin-bottom: 5px;
        }

        .item-name {
            font-size: 20px;
            font-weight: 700;
            line-height: 1.3;
        }

        .item-price-row {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-top: 10px;
        }

        .item-qty {
            font-size: 14px;
            font-weight: 600;
        }

        .item-amount {
            font-size: 24px;
            font-weight: 900;
        }

        .system-info {
            text-align: center;
            font-size: 10px;
            margin-top: 15px;
            padding-top: 5px;
            border-top: 1px dotted #888;
        }

        .footer-text {
            text-align: center;
            font-size: 12px;
            font-weight: 700;
            margin-top: 5px;
        }

        .text-right { text-align: right; }

        @media print {
            body { width: 80mm; }
            .receipt-container { width: 80mm; padding: 0; margin: 0; }
            .slip { border-bottom: none; margin-bottom: 0; }
        }
    </style>
</head>
<body>
    <div class="receipt-container">
        {% for slip in slips %}
            {% for item in slip.line_items %}
            <div class="slip">
                <!-- Header -->
                <div class="header">
                    <h1 class="temple-name-mal">{{ settings.name_mal }}</h1>
                    <h2 class="temple-name-eng">{{ settings.name_eng }}</h2>
                </div>

                <!-- Metadata -->
                <div class="meta-section">
                    <div class="meta-row">
                        <span>No: <strong>{{ slip.bill_no }}</strong></span>
                        <span>{{ timestamp }}</span>
                    </div>
                    {% if slip.scheduled_date %}
                    <div class="meta-row" style="margin-top: 2px;">
                        <span>Date: <strong>{{ slip.scheduled_date }}</strong></span>
                    </div>
                    {% endif %}
                </div>

                <!-- Devotee -->
                <div class="devotee-highlight">
                    <span class="devotee-name">{{ slip.devotee_name }}</span>
                    {% if slip.star %}
                    <span class="star-name">({{ slip.star }})</span>
                    {% endif %}
                </div>

                <!-- Focused Single Item -->
                <div class="item-container">
                    <span class="item-label">Vazhipadu Item</span>
                    <div class="item-name">{{ item.name }}</div>
                    <div class="item-price-row">
                        <span class="item-qty">Qty: {{ item.count }}</span>
                        <span class="item-amount">{{ "%.0f"|format(item.total) }}</span>
                    </div>
                </div>

                <!-- System Info -->
                <div class="system-info">
                    {% if slip.cashier_name %}User: {{ slip.cashier_name }}{% endif %}
                    {% if slip.printer_name %} | Term: {{ slip.printer_name }}{% endif %}
                </div>

                <!-- Footer -->
                {% if settings.receipt_footer %}
                <div class="footer-text">
                    {{ settings.receipt_footer }}
                </div>
                {% endif %}
            </div>
            {% endfor %}
        {% endfor %}
    </div>
</body>
</html>"""

    if 'print_template_content' not in setting_cols:
        c.execute("ALTER TABLE temple_settings ADD COLUMN print_template_content TEXT")
        c.execute("UPDATE temple_settings SET print_template_content = ? WHERE id = 1", (default_template,))
    
    # Always update the template on startup to ensure latest version
    c.execute("UPDATE temple_settings SET print_template_content = ? WHERE id = 1", (default_template,))

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
            remarks TEXT,
            original_bill_id INTEGER,
            FOREIGN KEY(cashier_id) REFERENCES users(id),
            FOREIGN KEY(original_bill_id) REFERENCES bills(id)
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

    # Migration: Add remarks if missing
    if 'remarks' not in columns:
        c.execute("ALTER TABLE bills ADD COLUMN remarks TEXT")

    # Migration: Add original_bill_id if missing
    if 'original_bill_id' not in columns:
        c.execute("ALTER TABLE bills ADD COLUMN original_bill_id INTEGER REFERENCES bills(id)")

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

    # Migration: Add payment_status and phone if missing
    if 'payment_status' not in columns:
        c.execute("ALTER TABLE bills ADD COLUMN payment_status TEXT DEFAULT 'paid'")
    
    if 'phone' not in columns:
        c.execute("ALTER TABLE bills ADD COLUMN phone TEXT")

    if 'payment_received_by' not in columns:
        c.execute("ALTER TABLE bills ADD COLUMN payment_received_by INTEGER REFERENCES users(id)")

    if 'payment_date' not in columns:
        c.execute("ALTER TABLE bills ADD COLUMN payment_date TIMESTAMP")

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
