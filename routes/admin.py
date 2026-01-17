from flask import Blueprint, render_template, request, flash, redirect, url_for, g
import sqlite3
from database import get_db
from modules.printers import printer_manager

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def require_super_user():
    if g.user is None:
        return redirect(url_for('auth.login'))
    elif g.user['role'] != 'admin':
        flash("Access Denied: Admins only.", "error")
        return redirect(url_for('cashier.index'))

@admin_bp.route('/')
def index():
    return render_template('admin/dashboard.html')

@admin_bp.route('/settings', methods=('GET', 'POST'))
def settings():
    db = get_db()
    
    if request.method == 'POST':
        print(f"DEBUG: Temple Settings POST: {request.form}")
        name_mal = request.form['name_mal']
        name_eng = request.form['name_eng']
        place = request.form['place']
        footer = request.form['receipt_footer']
        backup = 1 if 'backup_enabled' in request.form else 0
        
        db.execute(
            'UPDATE temple_settings SET name_mal=?, name_eng=?, place=?, receipt_footer=?, backup_enabled=? WHERE id=1',
            (name_mal, name_eng, place, footer, backup)
        )
        db.commit()
        flash('Settings updated successfully', 'success')
        return redirect(url_for('admin.settings'))
        
    settings = db.execute('SELECT * FROM temple_settings WHERE id=1').fetchone()
    return render_template('admin/settings.html', settings=settings)

@admin_bp.route('/users', methods=('GET', 'POST'))
def users():
    db = get_db()
    if request.method == 'POST':
        print(f"DEBUG: Users POST: {request.form}")
        if 'create_user' in request.form:
            username = request.form['username']
            pin = request.form['pin']
            role = request.form['role']
            try:
                db.execute('INSERT INTO users (username, pin, role) VALUES (?, ?, ?)',
                           (username, pin, role))
                db.commit()
                flash('User added successfully', 'success')
            except Exception as e:
                flash(f'Error adding user: {e}', 'error')
        elif 'delete_user' in request.form:
            user_id = int(request.form['user_id'])
            
            if user_id == g.user['id']:
                flash('You cannot delete your own account.', 'error')
            else:
                try:
                    # Prevent deleting self or last admin ideally, but keeping simple for now
                    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
                    db.commit()
                    flash('User deleted successfully', 'success')
                except sqlite3.IntegrityError:
                    # Fallback: Deactivate if they have history
                    db.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))
                    db.commit()
                    flash('User has billing history and cannot be deleted. Account deactivated instead.', 'warning')
                except Exception as e:
                    flash(f'Error deleting user: {e}', 'error')
            
        elif 'change_pin' in request.form:
            user_id = request.form['user_id']
            new_pin = request.form['new_pin']
            try:
                db.execute('UPDATE users SET pin = ? WHERE id = ?', (new_pin, user_id))
                db.commit()
                flash('PIN/Password updated successfully', 'success')
            except Exception as e:
                flash(f'Error updating PIN: {e}', 'error')

        elif 'toggle_active' in request.form:
            user_id = request.form['user_id']
            is_active = int(request.form['is_active'])
            db.execute('UPDATE users SET is_active = ? WHERE id = ?', (is_active, user_id))
            db.commit()
            status = "activated" if is_active else "deactivated"
            flash(f'User {status} successfully', 'success')
            
    users = db.execute('SELECT * FROM users').fetchall()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/printers', methods=('GET', 'POST'))
def printers():
    db = get_db()
    
    if request.method == 'POST':
        print(f"DEBUG: Printers POST: {request.form}")
        
        if 'add_web_printer' in request.form:
             try:
                db.execute('INSERT INTO printers (name, friendly_name) VALUES (?, ?)',
                           ('WEB_BROWSER_PRINT', 'Browser Printer'))
                db.commit()
                flash('Browser Virtual Printer added successfully', 'success')
             except Exception as e:
                flash(f'Error adding browser printer: {e}', 'error')
                
        elif 'add_printer' in request.form:
            cups_name = request.form['cups_name']
            friendly_name = request.form['friendly_name']
            try:
                db.execute('INSERT INTO printers (name, friendly_name) VALUES (?, ?)',
                           (cups_name, friendly_name))
                db.commit()
                flash('Printer added successfully', 'success')
            except Exception as e:
                flash(f'Error adding printer: {e}', 'error')
        
        elif 'toggle_active' in request.form:
            printer_id = request.form['printer_id']
            is_active = int(request.form['is_active'])
            db.execute('UPDATE printers SET is_active = ? WHERE id = ?', (is_active, printer_id))
            db.commit()
            
        elif 'delete_printer' in request.form:
            printer_id = request.form['printer_id']
            try:
                db.execute('DELETE FROM printers WHERE id = ?', (printer_id,))
                db.commit()
                flash('Printer removed', 'success')
            except sqlite3.IntegrityError:
                # Fallback: Disable if in use
                db.execute('UPDATE printers SET is_active = 0 WHERE id = ?', (printer_id,))
                db.commit()
                flash('Printer is in use, so it was disabled instead of deleted.', 'warning')
            except Exception as e:
                flash(f'Error removing printer: {e}', 'error')

    # Get registered printers from DB
    registered_printers = db.execute('SELECT * FROM printers').fetchall()
    registered_cups_names = [p['name'] for p in registered_printers]

    # Get system printers from CUPS/Mock
    system_printers = printer_manager.get_system_printers()
    
    # Filter out already registered ones
    available_printers = [p for p in system_printers if p not in registered_cups_names]

    return render_template('admin/printers.html', 
                           registered_printers=registered_printers,
                           available_printers=available_printers)

@admin_bp.route('/items', methods=('GET', 'POST'))
def items():
    db = get_db()
    if request.method == 'POST':
        print(f"DEBUG: Items POST: {request.form}")
        if 'add_item' in request.form:
            name = request.form['name']
            amount = float(request.form['amount'])
            type_ = request.form['type']
            try:
                db.execute('INSERT INTO puja_master (name, amount, type) VALUES (?, ?, ?)',
                           (name, amount, type_))
                db.commit()
                flash('Item added successfully', 'success')
            except Exception as e:
                flash(f'Error adding item: {e}', 'error')
        
        elif 'delete_item' in request.form:
            item_id = request.form['item_id']
            db.execute('DELETE FROM puja_master WHERE id = ?', (item_id,))
            db.commit()
            flash('Item deleted', 'success')

        elif 'edit_item' in request.form:
            item_id = request.form['item_id']
            name = request.form['name']
            amount = float(request.form['amount'])
            type_ = request.form['type']
            try:
                db.execute('UPDATE puja_master SET name=?, amount=?, type=? WHERE id=?',
                           (name, amount, type_, item_id))
                db.commit()
                flash('Item updated successfully', 'success')
            except Exception as e:
                flash(f'Error updating item: {e}', 'error')

    items = db.execute('SELECT * FROM puja_master ORDER BY name').fetchall()
    return render_template('admin/items.html', items=items)

@admin_bp.route('/reports')
def reports():
    db = get_db()
    
    # Filter params
    date_filter = request.args.get('date', None)
    search_query = request.args.get('q', '')
    
    query = '''
        SELECT 
            b.*,
            u.username as cashier_name
        FROM bills b
        JOIN users u ON b.cashier_id = u.id
        WHERE 1=1
    '''
    params = []
    
    # If searching, ignore date filter (usually user wants to find specific bill across time)
    # OR follow search + date if both provided. Let's do optional date.
    if search_query:
        query += ' AND (b.bill_no LIKE ? OR b.devotee_name LIKE ?)'
        wildcard = f'%{search_query}%'
        params.extend([wildcard, wildcard])
        
        if date_filter:
            query += ' AND date(b.created_at) = ?'
            params.append(date_filter)
    else:
        if date_filter:
            query += ' AND date(b.created_at) = ?'
            params.append(date_filter)
        else:
            # Default to today
            import datetime
            today = datetime.date.today().isoformat()
            query += ' AND date(b.created_at) = ?'
            params.append(today)
            date_filter = today
        
    query += ' ORDER BY b.created_at DESC LIMIT 100'
    
    bills = db.execute(query, params).fetchall()
    
    # Fetch items for each bill for full transparency
    bill_list = []
    for bill in bills:
        b_dict = dict(bill)
        b_dict['line_items'] = db.execute('''
            SELECT bi.*, pm.name 
            FROM bill_items bi 
            JOIN puja_master pm ON bi.puja_id = pm.id 
            WHERE bi.bill_id = ?
        ''', (bill['id'],)).fetchall()
        bill_list.append(b_dict)
    
    # Calculate totals
    total_amount = sum(b['total_amount'] for b in bill_list)
    count = len(bill_list)
    
    return render_template('admin/reports.html', 
                           bills=bill_list, 
                           total_amount=total_amount, 
                           count=count, 
                           date_filter=date_filter,
                           search_query=search_query)

@admin_bp.route('/reports/export')
def export_reports():
    import csv
    import io
    from flask import Response
    
    db = get_db()
    date_filter = request.args.get('date')
    
    # Export full dump for the day
    cursor = db.execute('''
        SELECT b.id, b.created_at, u.username, b.devotee_name, b.star, b.total_amount
        FROM bills b
        JOIN users u ON b.cashier_id = u.id
        WHERE date(b.created_at) = ?
    ''', (date_filter,))
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Bill ID', 'Date', 'Cashier', 'Devotee', 'Star', 'Amount'])
    
    for row in cursor:
        writer.writerow(list(row))
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=report_{date_filter}.csv"}
    )
@admin_bp.route('/backup/trigger', methods=['POST'])
def trigger_backup():
    import shutil
    import datetime
    from config import Config
    
    try:
        # Create backup directory if not exists
        if not os.path.exists(Config.BACKUP_PATH):
            os.makedirs(Config.BACKUP_PATH)
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(Config.BACKUP_PATH, backup_filename)
        
        # Lock DB? WAL mode allows hot backup usually, but safest is to copy using SQLite API or just shutil if file lock permits
        # SQLite Online Backup API is best but shutil works for WAL often if careful.
        # Ideally: use sqlite3 connection.backup()
        
        db = get_db()
        # We need the underlying connection object, not the row wrapper if possible, or just open new raw connection
        import sqlite3
        
        # Use Python's sqlite3 backup API
        bck = sqlite3.connect(backup_path)
        db.backup(bck)
        bck.close()
        
        # Check cloud backup setting
        settings = db.execute('SELECT backup_enabled FROM temple_settings WHERE id=1').fetchone()
        cloud_msg = ""
        if settings['backup_enabled']:
             # Placeholder for cloud upload
             cloud_msg = " (Cloud upload skipped in offline mode)"
             
        flash(f'Backup created successfully: {backup_filename}{cloud_msg}', 'success')
        
    except Exception as e:
        flash(f'Backup failed: {e}', 'error')
        
    return redirect(url_for('admin.settings'))
