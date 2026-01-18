from flask import Flask, render_template, g
from config import Config
from database import close_db, init_db
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.cashier import cashier_bp
from utils.timezone_utils import now_ist
import os

app = Flask(__name__)
app.config.from_object(Config)

app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(cashier_bp)

@app.context_processor
def inject_settings():
    from database import get_db
    from routes.cashier import STARS
    import datetime
    
    star_map = {s['eng']: s['mal'] for s in STARS}
    
    with app.app_context():
        try:
            db = get_db()
            settings = db.execute('SELECT * FROM temple_settings WHERE id=1').fetchone()
            return {
                'temple_settings': settings,
                'now_year': now_ist().year,
                'stars': STARS,
                'star_map': star_map
            }
        except:
            return {
                'temple_settings': None,
                'now_year': datetime.datetime.now().year,
                'stars': STARS,
                'star_map': star_map
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
    app.run(host='0.0.0.0', port=5000, debug=True)
