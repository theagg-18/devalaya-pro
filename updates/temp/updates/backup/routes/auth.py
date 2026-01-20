from flask import Blueprint, render_template, request, flash, redirect, url_for, session, g
from database import get_db
import functools

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=('GET', 'POST'))
def login():
    import random
    if request.method == 'POST':
        username = request.form['username']
        pin = request.form['pin']
        captcha_answer = request.form.get('captcha_answer')
        
        db = get_db()
        error = None
        
        # Verify Captcha
        stored_answer = session.get('captcha_result')
        if not captcha_answer or str(captcha_answer) != str(stored_answer):
            error = 'Invalid CAPTCHA answer.'
        
        if error is None:
            user = db.execute(
                'SELECT * FROM users WHERE username = ?', (username,)
            ).fetchone()

            if user is None:
                error = 'Incorrect username.'
            elif user['pin'] != pin:
                error = 'Incorrect PIN.'
            elif not user['is_active']:
                error = 'Account Deactivated. Contact Admin.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['role'] = user['role']
            
            if user['role'] == 'admin':
                return redirect(url_for('admin.index'))
            else:
                return redirect(url_for('cashier.index'))

        flash(error, 'error')

    # Generate new captcha for the next attempt
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
