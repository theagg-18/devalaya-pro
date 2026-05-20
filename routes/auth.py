import functools
import random
import logging

from flask import Blueprint, render_template, request, flash, redirect, url_for, session, g
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db
from extensions import limiter

auth_bp = Blueprint('auth', __name__)

# Werkzeug hash method prefixes — more reliable than checking for '$'
_HASH_PREFIXES = ('pbkdf2:', 'scrypt:', 'argon2')

def _is_hashed(value):
    return value.startswith(_HASH_PREFIXES)

def _pin_valid(pin):
    """Return error string or None if PIN meets strength requirements."""
    if len(pin) < 4:
        return 'PIN must be at least 4 characters.'
    if len(pin) > 20:
        return 'PIN must not exceed 20 characters.'
    return None

@auth_bp.route('/login', methods=('GET', 'POST'))
@limiter.limit("10 per minute", error_message="Too many login attempts. Please wait a minute.")
def login():
    if request.method == 'POST':
        username = request.form['username']
        pin = request.form['pin']
        captcha_answer = request.form.get('captcha_answer')

        db = get_db()
        error = None

        # Verify CAPTCHA
        stored_answer = session.get('captcha_result')
        if not captcha_answer or str(captcha_answer) != str(stored_answer):
            error = 'Invalid CAPTCHA answer.'

        if error is None:
            user = db.execute(
                'SELECT * FROM users WHERE username = ?', (username,)
            ).fetchone()

            if user is None:
                error = 'Incorrect username.'
            else:
                stored = user['pin']
                if _is_hashed(stored):
                    pin_ok = check_password_hash(stored, pin)
                else:
                    # Legacy plain-text PIN — compare then migrate
                    pin_ok = (stored == pin)
                    if pin_ok:
                        db.execute('UPDATE users SET pin = ? WHERE id = ?',
                                   (generate_password_hash(pin), user['id']))
                        db.commit()

                if not pin_ok:
                    error = 'Incorrect PIN.'

            if error is None and not user['is_active']:
                error = 'Account Deactivated. Contact Admin.'

        if error is None:
            session.clear()
            session.permanent = True  # honour PERMANENT_SESSION_LIFETIME from config
            session['user_id'] = user['id']
            session['role'] = user['role']

            if user['role'] == 'admin':
                return redirect(url_for('admin.index'))
            else:
                return redirect(url_for('cashier.index'))

        flash(error, 'error')

    # Generate new CAPTCHA for next attempt
    num1 = random.randint(1, 9)
    num2 = random.randint(1, 9)
    session['captcha_result'] = num1 + num2

    return render_template('login.html', captcha_q=f"{num1} + {num2}")

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user['role'] != 'admin':
            flash("Admin access required", 'error')
            return redirect(url_for('index'))
        return view(**kwargs)
    return wrapped_view
