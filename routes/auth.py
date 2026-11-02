import datetime
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

# PIN rules: admins control the whole system, so they need a longer PIN
MIN_PIN_LENGTH = {'admin': 6, 'cashier': 4}
MAX_PIN_LENGTH = 20
DEFAULT_PIN = '1234'

# Lockout: this many wrong PINs in a row locks the account for LOCKOUT_MINUTES
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

# Pages a user with a pending forced PIN change may still reach
_PIN_CHANGE_ALLOWED = {'auth.change_pin', 'auth.logout', 'static', 'health_check'}

def validate_pin(pin, role='cashier'):
    """Return error string or None if PIN meets strength requirements for role."""
    min_len = MIN_PIN_LENGTH.get(role, 4)
    if len(pin) < min_len:
        return f'PIN must be at least {min_len} characters.'
    if len(pin) > MAX_PIN_LENGTH:
        return f'PIN must not exceed {MAX_PIN_LENGTH} characters.'
    if pin == DEFAULT_PIN:
        return 'The default PIN cannot be used.'
    return None

def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

def _locked_minutes_left(user):
    """Minutes until the account unlocks, or 0 if not locked."""
    if not user['locked_until']:
        return 0
    try:
        until = datetime.datetime.fromisoformat(user['locked_until'])
    except ValueError:
        return 0
    remaining = (until - _utcnow()).total_seconds()
    return max(0, int(remaining // 60) + 1) if remaining > 0 else 0

def _record_failed_login(db, user):
    attempts = (user['failed_attempts'] or 0) + 1
    if attempts >= MAX_FAILED_ATTEMPTS:
        until = (_utcnow() + datetime.timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
        db.execute('UPDATE users SET failed_attempts = 0, locked_until = ? WHERE id = ?',
                   (until, user['id']))
        logging.warning(f"Account '{user['username']}' locked after {attempts} failed logins")
    else:
        db.execute('UPDATE users SET failed_attempts = ? WHERE id = ?', (attempts, user['id']))
    db.commit()

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
        # pop() so a known answer can't be replayed with the same cookie
        stored_answer = session.pop('captcha_result', None)
        if stored_answer is None or not captcha_answer or str(captcha_answer) != str(stored_answer):
            error = 'Invalid CAPTCHA answer.'

        if error is None:
            user = db.execute(
                'SELECT * FROM users WHERE username = ?', (username,)
            ).fetchone()

            if user is None:
                error = 'Incorrect username.'
            elif _locked_minutes_left(user):
                error = (f'Account locked after too many wrong PINs. '
                         f'Try again in {_locked_minutes_left(user)} minute(s) or ask an admin.')
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
                    _record_failed_login(db, user)
                    error = 'Incorrect PIN.'

            if error is None and not user['is_active']:
                error = 'Account Deactivated. Contact Admin.'

        if error is None:
            # Successful login: clear the failure counter. Force a PIN change if
            # it's the default or too weak for the role (e.g. old 4-digit admin PIN).
            must_change = 1 if (user['must_change_pin'] or validate_pin(pin, user['role'])) else 0
            db.execute('UPDATE users SET failed_attempts = 0, locked_until = NULL, '
                       'must_change_pin = ? WHERE id = ?', (must_change, user['id']))
            db.commit()

            session.clear()
            session.permanent = True  # honour PERMANENT_SESSION_LIFETIME from config
            session['user_id'] = user['id']
            session['role'] = user['role']

            if must_change:
                return redirect(url_for('auth.change_pin'))
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

@auth_bp.route('/change-pin', methods=('GET', 'POST'))
@limiter.limit("10 per minute")
def change_pin():
    if g.user is None:
        return redirect(url_for('auth.login'))

    forced = bool(g.user['must_change_pin'])

    if request.method == 'POST':
        current_pin = request.form.get('current_pin', '')
        new_pin = request.form.get('new_pin', '')
        confirm_pin = request.form.get('confirm_pin', '')
        db = get_db()

        error = None
        if not check_password_hash(g.user['pin'], current_pin):
            error = 'Current PIN is incorrect.'
        elif new_pin != confirm_pin:
            error = 'New PINs do not match.'
        elif new_pin == current_pin:
            error = 'New PIN must be different from the current PIN.'
        else:
            error = validate_pin(new_pin, g.user['role'])

        if error is None:
            db.execute('UPDATE users SET pin = ?, must_change_pin = 0 WHERE id = ?',
                       (generate_password_hash(new_pin), g.user['id']))
            db.commit()
            flash('PIN changed successfully.', 'success')
            return redirect(url_for('dashboard'))

        flash(error, 'error')

    return render_template('change_pin.html', forced=forced,
                           min_length=MIN_PIN_LENGTH.get(g.user['role'], 4))

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
        user = get_db().execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()
        # A deleted or deactivated account must not keep a live session
        if user is None or not user['is_active']:
            session.clear()
            user = None
        g.user = user

        # Until a forced PIN change is done, only the change page is reachable
        if user is not None and user['must_change_pin'] and request.endpoint not in _PIN_CHANGE_ALLOWED:
            return redirect(url_for('auth.change_pin'))

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
