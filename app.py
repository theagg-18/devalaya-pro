from flask import Flask, render_template, g
from config import Config
from database import close_db, init_db
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.cashier import cashier_bp
from utils.timezone_utils import now_ist
from version import get_version, get_version_display
import os
import sys

# Ensure the script's directory is in sys.path.
# This is required for embedded Python distributions which might not add the CWD/Script dir by default.
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Determine base directory for static and template files
if getattr(sys, 'frozen', False):
    basedir = sys._MEIPASS
else:
    basedir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
            static_folder=os.path.join(basedir, 'static'),
            template_folder=os.path.join(basedir, 'templates'))



app.config.from_object(Config)

# Configure Logging
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/error.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.ERROR)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Devalaya Billing System startup')
else:
    logging.basicConfig(level=logging.INFO)


app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(cashier_bp)

from routes.utility import utility_bp
app.register_blueprint(utility_bp)

@app.route('/health')
def health_check():
    return 'OK', 200

@app.before_request
def check_maintenance():
    from modules import updater
    from flask import request, abort
    if updater.MAINTENANCE_MODE:
        # Allow static (for styles), updater status polling, and health check
        if request.path.startswith('/static') or \
           request.path.startswith('/admin/updates/status') or \
           request.path == '/health':
            return None
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta http-equiv="refresh" content="2">
            <title>System Updating</title>
            <style>
                body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background: #f8fafc; color: #334155; }
                .loader { border: 4px solid #e2e8f0; border-top: 4px solid #3b82f6; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin-bottom: 20px; }
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            </style>
        </head>
        <body>
            <div class="loader"></div>
            <h2>System is updating...</h2>
            <p>Please wait. This page will reload automatically.</p>
        </body>
        </html>
        """, 503

@app.template_filter('from_json')
def from_json_filter(value):
    import json
    try:
        if not value:
            return {}
        return json.loads(value)
    except:
        return {}

@app.context_processor
def inject_settings():
    from database import get_cached_settings
    from routes.cashier import STARS
    import datetime
    
    settings, theme_css = get_cached_settings()
    
    star_map = {s['eng']: s['mal'] for s in STARS}
    
    return {
        'temple_settings': settings,
        'now_year': now_ist().year,
        'stars': STARS,
        'star_map': star_map,
        'app_version': get_version(),
        'app_version_display': get_version_display(),
        'theme_css': theme_css
    }

# Register Database Teardown
app.teardown_appcontext(close_db)

# Initialize DB on first run (simple check)
if not os.path.exists(Config.DB_PATH):
    print("Database not found. Initializing...")
    init_db()
else:
    # Optional: Check if tables exist or just run init to ensure (safe with IF NOT EXISTS)
    init_db()

@app.route('/')
def index():
    from flask import session, redirect, url_for
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.index'))
        else:
            return redirect(url_for('cashier.index'))
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    from flask import session, redirect, url_for
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.index'))
        else:
            return redirect(url_for('cashier.index'))
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    # Security: Disable debug mode in production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)

# Trigger Reload v1.5.1
