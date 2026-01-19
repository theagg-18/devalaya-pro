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

    if 'print_template_content' not in setting_cols:
        c.execute("ALTER TABLE temple_settings ADD COLUMN print_template_content TEXT")
        # Set default template
        default_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Receipt</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Malayalam:wght@400;500;600;700&display=swap');

        body {
            margin: 0;
            padding: 0;
            font-family: 'Inter', 'Noto Sans Malayalam', sans-serif;
            background: #fff;
            color: #000;
        }

        .receipt-container {
            width: 80mm; /* Standard thermal printer width */
            margin: 0 auto;
            padding: 10px;
            box-sizing: border-box;
        }

        .slip {
            page-break-after: always;
            border-bottom: 2px dashed #000; /* Separator for visualization in browser */
            padding-bottom: 20px;
            margin-bottom: 20px;
        }

        .slip:last-child {
            page-break-after: auto;
            border-bottom: none;
        }

        .header {
            text-align: center;
            margin-bottom: 15px;
        }

        .temple-name-mal {
            font-size: 16px;
            font-weight: 700;
            margin: 0;
        }

        .temple-name-eng {
            font-size: 14px;
            font-weight: 600;
            margin: 2px 0 0 0;
            text-transform: uppercase;
        }
        
        .subtitle-mal {
            font-size: 12px;
            font-weight: 500;
            margin: 2px 0 0 0;
        }

        .subtitle-eng {
            font-size: 10px;
            font-weight: 400;
            margin: 0;
            text-transform: uppercase;
        }

        .meta-info {
            font-size: 12px;
            margin-bottom: 10px;
            border-bottom: 1px solid #000;
            padding-bottom: 5px;
        }

        .meta-row {
            display: flex;
            justify-content: space-between;
        }

        .bill-details {
            margin-bottom: 10px;
        }

        .devotee-info {
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .star-info {
            font-size: 12px;
            font-weight: 500;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-bottom: 10px;
        }

        th {
            text-align: left;
            border-bottom: 1px solid #000;
            padding: 2px 0;
        }

        td {
            padding: 4px 0;
            vertical-align: top;
        }

        .text-right {
            text-align: right;
        }

        .total-row {
            border-top: 1px solid #000;
            font-weight: 700;
            font-size: 14px;
        }

        .footer {
            text-align: center;
            font-size: 10px;
            margin-top: 15px;
        }

        @media print {
            body {
                width: auto;
                margin: 0;
            }
            .receipt-container {
                width: 100%;
                padding: 0;
                margin: 0;
            }
            .slip {
                border-bottom: none; /* Hide visual separator in actual print */
                margin-bottom: 0;
                height: auto;
            }
        }
    </style>
</head>
<body>
    <div class="receipt-container">
        {% for slip in slips %}
        <div class="slip">
            <div class="header">
                <h1 class="temple-name-mal">{{ settings.name_mal }}</h1>
                <h2 class="temple-name-eng">{{ settings.name_eng }}</h2>
                {% if settings.subtitle_mal %}
                <h3 class="subtitle-mal">{{ settings.subtitle_mal }}</h3>
                {% endif %}
                {% if settings.subtitle_eng %}
                <h4 class="subtitle-eng">{{ settings.subtitle_eng }}</h4>
                {% endif %}
            </div>

            <div class="meta-info">
                <div class="meta-row">
                    <span>Bill No: {{ slip.bill_no }}</span>
                    <span>{{ timestamp }}</span>
                </div>
                {% if slip.scheduled_date %}
                <div class="meta-row" style="margin-top: 4px;">
                    <span><strong>Vazhipadu Date: {{ slip.scheduled_date }}</strong></span>
                </div>
                {% endif %}
            </div>

            <div class="bill-details">
                <div class="devotee-info">
                    {{ slip.devotee_name }}
                    {% if slip.star %}
                    <span class="star-info">({{ slip.star }})</span>
                    {% endif %}
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th style="width: 60%;">Item</th>
                        <th style="width: 20%;">Qty</th>
                        <th class="text-right" style="width: 20%;">Amt</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in slip.line_items %}
                    <tr>
                        <td>{{ item.name }}</td>
                        <td>{{ item.count }}</td>
                        <td class="text-right">{{ "%.0f"|format(item.total) }}</td>
                    </tr>
                    {% endfor %}
                    
                    {% if slip.line_items|length > 1 %}
                    <tr class="total-row">
                        <td colspan="2">Total</td>
                        <td class="text-right">{{ "%.0f"|format(slip.total) }}</td>
                    </tr>
                    {% endif %}
                </tbody>
            </table>

            <div class="footer">
                {{ settings.receipt_footer }}
            </div>
        </div>
        {% endfor %}
    </div>

    <script>
        // Auto-print only if loaded with instructions or standalone
        // window.onload = function() { window.print(); }
    </script>
</body>
</html>"""
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
