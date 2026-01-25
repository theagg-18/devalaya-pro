from flask import Blueprint, render_template, request, flash, redirect, url_for, g, current_app
import sqlite3
from database import get_db
from modules.printers import printer_manager
import os
import datetime
from config import Config
from flask import send_file
from utils.timezone_utils import now_ist, format_ist_datetime

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
    db = get_db()
    
    # 1. Today's Total (Cash Basis: Paid Today)
    today = datetime.date.today().isoformat()
    today_total = db.execute('''
        SELECT SUM(total_amount) 
        FROM bills 
        WHERE date(COALESCE(payment_date, created_at)) = ? 
          AND status != 'cancelled' 
          AND status != 'draft'
          AND payment_status = 'paid'
    ''', (today,)).fetchone()[0] or 0
    
    # 2. This Month's Total (Cash Basis: Paid this Month)
    today_date = datetime.date.today()
    month_start = today_date.replace(day=1).isoformat()
    month_total = db.execute('''
        SELECT SUM(total_amount) 
        FROM bills 
        WHERE date(COALESCE(payment_date, created_at)) >= ? 
          AND status != 'cancelled' 
          AND status != 'draft'
          AND payment_status = 'paid'
    ''', (month_start,)).fetchone()[0] or 0

    # 2.5 Pending Payments Total (Outstanding)
    pending_total = db.execute("SELECT SUM(total_amount) FROM bills WHERE payment_status = 'pending' AND status != 'cancelled' AND status != 'draft'").fetchone()[0] or 0

    # 3. Revenue Trend (Last 30 Days)
    thirty_days_ago_date = today_date - datetime.timedelta(days=29)
    thirty_days_ago = thirty_days_ago_date.isoformat()
    
    trend_data = db.execute('''
        SELECT date(COALESCE(payment_date, created_at)) as day, SUM(total_amount) as total
        FROM bills 
        WHERE date(COALESCE(payment_date, created_at)) >= ? 
          AND status != 'cancelled' 
          AND status != 'draft'
          AND payment_status = 'paid'
        GROUP BY day
        ORDER BY day
    ''', (thirty_days_ago,)).fetchall()
    
    trend_dict = {row['day']: row['total'] for row in trend_data}
    
    trend_dates = []
    trend_revenues = []
    
    curr = thirty_days_ago_date
    while curr <= today_date:
        d_str = curr.isoformat()
        trend_dates.append(curr.strftime('%b %d')) # Format: Jan 01
        trend_revenues.append(trend_dict.get(d_str, 0))
        curr += datetime.timedelta(days=1)

    # 4. Popular Vazhipadus (Top 5 Last 30 Days)
    top_items_data = db.execute('''
        SELECT pm.name, SUM(bi.count) as count
        FROM bill_items bi
        JOIN puja_master pm ON bi.puja_id = pm.id
        JOIN bills b ON bi.bill_id = b.id
        WHERE date(b.created_at) >= ?
        GROUP BY pm.name
        ORDER BY count DESC
        LIMIT 5
    ''', (thirty_days_ago,)).fetchall()
    
    top_item_names = [row['name'] for row in top_items_data]
    top_item_counts = [row['count'] for row in top_items_data]

    # 5. Peak Hours (Last 30 Days)
    # Using substr for sqlite compatibility if strftime behaves oddly, but strftime('%H', ...) is standard sqlite
    peak_hours_data = db.execute('''
        SELECT strftime('%H', created_at) as hour, COUNT(*) as count
        FROM bills
        WHERE date(created_at) >= ?
        GROUP BY hour
        ORDER BY hour
    ''', (thirty_days_ago,)).fetchall()
    
    hours_map = {int(row['hour']): row['count'] for row in peak_hours_data if row['hour'] is not None}
    
    # Hours of operation typically 5 AM to 9 PM (05 to 21)
    hours_labels = []
    hours_counts = []
    for h in range(5, 22): 
        hours_labels.append(f"{h:02d}:00")
        hours_counts.append(hours_map.get(h, 0))

    today_star = None
    today_mal_date_str = ""
    try:
        from modules.panchang import get_nakshatra, get_malayalam_date
        today_date_obj = datetime.date.today()
        today_star = get_nakshatra(today_date_obj)
        mal_date = get_malayalam_date(today_date_obj)
        today_mal_date_str = f"{mal_date['day']} {mal_date['mal_month']} {mal_date['mal_year']}"
    except:
        pass

    return render_template('admin/dashboard.html',
                           now=format_ist_datetime(now_ist(), "%d-%m-%Y %I:%M %p"),
                           today_star=today_star,
                           today_mal_date_str=today_mal_date_str,
                           today_total=today_total,
                           month_total=month_total,
                           pending_total=pending_total,
                           trend_dates=trend_dates,
                           trend_revenues=trend_revenues,
                           top_item_names=top_item_names,
                           top_item_counts=top_item_counts,
                           hours_labels=hours_labels,
                           hours_counts=hours_counts)

@admin_bp.route('/settings', methods=('GET', 'POST'))
def settings():
    db = get_db()
    
    if request.method == 'POST':
        print(f"DEBUG: Temple Settings POST: {request.form}")
        name_mal = request.form['name_mal']
        name_eng = request.form['name_eng']
        place = request.form['place']
        footer = request.form['receipt_footer']
        template_content = request.form['print_template_content']
        subtitle_mal = request.form.get('subtitle_mal', '')
        subtitle_eng = request.form.get('subtitle_eng', '')
        color_theme = request.form.get('color_theme', 'kerala')
        
        # Handle Custom Theme Colors
        import json
        custom_colors = {
            'primary': request.form.get('custom_primary', '#000000'),
            'secondary': request.form.get('custom_secondary', '#ffffff'),
            'background': request.form.get('custom_background', '#f5f5f5')
        }
        custom_theme_colors = json.dumps(custom_colors)
        
        
        backup = 1 if 'backup_enabled' in request.form else 0
        
        # Handle Logo Upload
        logo_path = None
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '':
                from werkzeug.utils import secure_filename
                import os
                
                # Create upload dir
                upload_folder = os.path.join(current_app.static_folder, 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                # Save file with timestamp to prevent cache
                filename = secure_filename(file.filename)
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                new_filename = f"logo_{timestamp}_{filename}"
                file.save(os.path.join(upload_folder, new_filename))
                
                # Store relative path for static url_for
                logo_path = f"uploads/{new_filename}"

        # Construct Query
        # Extract latitude and longitude from form, with defaults
        latitude = request.form.get('latitude', '10.85')
        longitude = request.form.get('longitude', '76.27')

        if logo_path:
             db.execute(
                '''UPDATE temple_settings SET name_mal=?, name_eng=?, place=?, receipt_footer=?, backup_enabled=?, 
                   print_template_content=?, subtitle_mal=?, subtitle_eng=?, color_theme=?, custom_theme_colors=?, logo_path=?, latitude=?, longitude=? WHERE id=1''',
                (name_mal, name_eng, place, footer, backup, template_content, subtitle_mal, subtitle_eng, color_theme, custom_theme_colors, logo_path, latitude, longitude)
            )
        else:
             db.execute(
                '''UPDATE temple_settings SET name_mal=?, name_eng=?, place=?, receipt_footer=?, backup_enabled=?, 
                   print_template_content=?, subtitle_mal=?, subtitle_eng=?, color_theme=?, custom_theme_colors=?, latitude=?, longitude=? WHERE id=1''',
                (name_mal, name_eng, place, footer, backup, template_content, subtitle_mal, subtitle_eng, color_theme, custom_theme_colors, latitude, longitude)
            )
        db.commit()
        
        # Invalidate Cache
        from database import clear_settings_cache
        clear_settings_cache()
        
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
                import logging
                logging.error(f"Error adding user: {e}", exc_info=True)
                flash('An error occurred while adding the user.', 'error')
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
                    import logging
                    logging.error(f"Error deleting user: {e}", exc_info=True)
                    flash('An error occurred while deleting the user.', 'error')
            
        elif 'change_pin' in request.form:
            user_id = request.form['user_id']
            new_pin = request.form['new_pin']
            try:
                db.execute('UPDATE users SET pin = ? WHERE id = ?', (new_pin, user_id))
                db.commit()
                flash('PIN/Password updated successfully', 'success')
            except Exception as e:
                import logging
                logging.error(f"Error updating PIN: {e}", exc_info=True)
                flash('An error occurred while updating the PIN.', 'error')

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
                import logging
                logging.error(f"Error adding browser printer: {e}", exc_info=True)
                flash('An error occurred while adding the browser printer.', 'error')
                
        elif 'add_printer' in request.form:
            cups_name = request.form['cups_name']
            friendly_name = request.form['friendly_name']
            try:
                db.execute('INSERT INTO printers (name, friendly_name) VALUES (?, ?)',
                           (cups_name, friendly_name))
                db.commit()
                flash('Printer added successfully', 'success')
            except Exception as e:
                import logging
                logging.error(f"Error adding printer: {e}", exc_info=True)
                flash('An error occurred while adding the printer.', 'error')
        
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
                import logging
                logging.error(f"Error removing printer: {e}", exc_info=True)
                flash('An error occurred while removing the printer.', 'error')

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
                import logging
                logging.error(f"Error adding item: {e}", exc_info=True)
                flash('An error occurred while adding the item.', 'error')
        
        elif 'delete_item' in request.form:
            item_id = request.form['item_id']
            try:
                # Try Hard Delete first (if unused)
                db.execute('DELETE FROM puja_master WHERE id = ?', (item_id,))
                db.commit()
                flash('Item permanently deleted', 'success')
            except sqlite3.IntegrityError:
                # Fallback to Soft Delete (Archive)
                db.execute('UPDATE puja_master SET is_active = 0 WHERE id = ?', (item_id,))
                db.commit()
                flash('Item archived because it has billing history (Soft Deleted)', 'warning')
            except Exception as e:
                import logging
                logging.error(f"Error deleting item: {e}", exc_info=True)
                flash('An error occurred while deleting the item.', 'error')

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
                import logging
                logging.error(f"Error updating item: {e}", exc_info=True)
                flash('An error occurred while updating the item.', 'error')

        elif 'upload_csv' in request.files:
            file = request.files['upload_csv']
            if file and (file.filename.endswith('.csv') or file.filename.endswith('.txt')):
                try:
                    import csv
                    import io
                    # Read file content safely
                    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                    csv_input = csv.DictReader(stream)
                    
                    # Normalize headers to support case-insensitive upload
                    headers = [h.lower().strip() for h in csv_input.fieldnames or []]
                    
                    if 'name' not in headers or 'amount' not in headers:
                         flash('Invalid CSV format. Header must contain "Name" and "Amount".', 'error')
                    else:
                        success_count = 0
                        updated_count = 0
                        
                        # Prepare mapped reader
                        stream.seek(0)
                        csv_input = csv.DictReader(stream)
                        # We need to map actual optional headers dynamically if they differ in case
                        # But for simplicity, let's strictly require 'Name', 'Amount', 'Type' (optional)
                        # Or better, just case-insensitive lookup per row.
                        
                        for row in csv_input:
                            # Normalize keys
                            row_norm = {k.lower().strip(): v for k, v in row.items() if k}
                            
                            name = row_norm.get('name')
                            amount_str = row_norm.get('amount')
                            type_ = row_norm.get('type', 'puja')
                            
                            if not name or not amount_str:
                                continue # Skip invalid rows
                                
                            try:
                                amount = float(amount_str)
                            except ValueError:
                                continue # Skip invalid amount
                                
                            # Check existence
                            exist = db.execute('SELECT id FROM puja_master WHERE name = ?', (name,)).fetchone()
                            
                            if exist:
                                db.execute('UPDATE puja_master SET amount=?, type=?, is_active=1 WHERE id=?', 
                                           (amount, type_, exist['id']))
                                updated_count += 1
                            else:
                                db.execute('INSERT INTO puja_master (name, amount, type) VALUES (?, ?, ?)',
                                           (name, amount, type_))
                                success_count += 1
                                
                        db.commit()
                        flash(f'Bulk upload complete. Created: {success_count}, Updated: {updated_count}.', 'success')
                        
                except Exception as e:
                    flash(f'Error processing CSV: {e}', 'error')
            else:
                flash('Invalid file. Please upload a CSV file.', 'error')

    items = db.execute('SELECT * FROM puja_master WHERE is_active = 1 ORDER BY name').fetchall()
    return render_template('admin/items.html', items=items)

@admin_bp.route('/items/template')
def items_template():
    import io
    import csv
    from flask import Response
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Amount', 'Type'])
    writer.writerow(['Ganapathi Homam', '100', 'puja'])
    writer.writerow(['Ghee (100ml)', '50', 'item'])
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=item_template.csv"}
    )

@admin_bp.route('/reports')
def reports():
    db = get_db()
    
    # Filter params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search_query = request.args.get('q', '')
    payment_status_filter = request.args.get('payment_status', 'all')
    
    # Defaults
    import datetime

    today = datetime.date.today().isoformat()
    if not start_date: start_date = today
    if not end_date: end_date = today

    # Base Conditions
    conditions = ["b.status != 'draft'"]
    params = []

    # If status is pending, we ignore date filter as per requirement "view all pending"
    # Otherwise, we apply date filter based on Effective Date (Payment Date if Paid, else Created Date)
    if payment_status_filter != 'pending':
         conditions.append('date(COALESCE(b.payment_date, b.created_at)) BETWEEN ? AND ?')
         params.extend([start_date, end_date])
    
    # Payment Status Filter

    # Payment Status Filter
    if payment_status_filter != 'all':
        conditions.append('b.payment_status = ?')
        params.append(payment_status_filter)
    
    # Search Logic

    if search_query:
        # Search Bill No, Devotee, OR Item Name (Subquery)
        conditions.append('''
            (b.bill_no LIKE ? OR b.devotee_name LIKE ? OR EXISTS (
                SELECT 1 FROM bill_items bi 
                JOIN puja_master pm ON bi.puja_id = pm.id 
                WHERE bi.bill_id = b.id AND pm.name LIKE ?
            ))
        ''')
        wildcard = f'%{search_query}%'
        params.extend([wildcard, wildcard, wildcard])
        
    where_clause = ' AND '.join(conditions)
    
    # 1. Calculate Global Totals (Revenue & Count) for the filtered set
    # Exclude CANCELLED bills from Revenue and Pending Amount
    grand_total_sql = f'''
        SELECT 
            COUNT(*), 
            SUM(CASE WHEN b.status != 'cancelled' THEN b.total_amount ELSE 0 END),
            SUM(CASE WHEN b.payment_status = 'pending' AND b.status != 'cancelled' THEN b.total_amount ELSE 0 END)
        FROM bills b
        WHERE {where_clause}
    '''
    stats = db.execute(grand_total_sql, params).fetchone()
    total_records = stats[0] or 0
    total_revenue = stats[1] or 0.0
    pending_amount = stats[2] or 0.0

    # 2. Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_pages = (total_records + per_page - 1) // per_page
    offset = (page - 1) * per_page
    
    # 3. Fetch Paginated Records
    data_sql = f'''
        SELECT 
            b.*,
            u.username as cashier_name,
            u2.username as receiver_name
        FROM bills b
        JOIN users u ON b.cashier_id = u.id
        LEFT JOIN users u2 ON b.payment_received_by = u2.id
        WHERE {where_clause}
        ORDER BY b.created_at DESC
        LIMIT ? OFFSET ?
    '''
    # We need a fresh params list for the data query because we append limit/offset
    data_params = list(params) 
    data_params.extend([per_page, offset])
    
    bills = db.execute(data_sql, data_params).fetchall()
    
    # Fetch items for display
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
    
    return render_template('admin/reports.html', 
                           bills=bill_list, 
                           total_amount=total_revenue, 
                           pending_amount=pending_amount,
                           count=total_records, 
                           start_date=start_date,
                           end_date=end_date,
                           search_query=search_query,
                           payment_status=payment_status_filter,
                           current_page=page,
                           total_pages=total_pages)

@admin_bp.route('/reports/export')
def export_reports():
    import csv
    import io
    from flask import Response, stream_with_context
    import datetime
    
    db = get_db()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Defaults to today if missing
    today = datetime.date.today().isoformat()
    if not start_date: start_date = today
    if not end_date: end_date = today
    
    # Export full dump for the date range with Items
    cursor = db.execute('''
        SELECT 
            b.bill_no, 
            b.created_at, 
            u.username, 
            b.devotee_name, 
            b.star, 
            GROUP_CONCAT(pm.name || ' (' || bi.count || ')', ', ') as items,
            b.total_amount,
            b.payment_status,
            u2.username as received_by
        FROM bills b
        JOIN users u ON b.cashier_id = u.id
        LEFT JOIN users u2 ON b.payment_received_by = u2.id
        LEFT JOIN bill_items bi ON b.id = bi.bill_id
        LEFT JOIN puja_master pm ON bi.puja_id = pm.id
        WHERE date(b.created_at) BETWEEN ? AND ?
        GROUP BY b.id
        ORDER BY b.created_at DESC
    ''', (start_date, end_date))
    
    # Use distinct BOM for Excel to recognize UTF-8
    def generate():
        # Write BOM
        yield '\ufeff'
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['Bill No', 'Date', 'Cashier', 'Devotee', 'Star', 'Items', 'Amount'])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)
        
        for row in cursor:
            # Handle potential None for items if bill has no lines (unlikely but safe)
            row_list = list(row)
            if row_list[5] is None:
                row_list[5] = ""
            
            writer.writerow(row_list)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    filename = f"report_{start_date}.csv" if start_date == end_date else f"report_{start_date}_to_{end_date}.csv"
    return Response(
        stream_with_context(generate()),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

@admin_bp.route('/backups')
def backups():
    import os
    from config import Config
    import datetime
    
    # Ensure backup directory exists
    if not os.path.exists(Config.BACKUP_PATH):
        try:
            os.makedirs(Config.BACKUP_PATH)
        except OSError:
            pass
            
    # List files
    backup_files = []
    if os.path.exists(Config.BACKUP_PATH):
        for filename in os.listdir(Config.BACKUP_PATH):
            if filename.endswith('.db'):
                filepath = os.path.join(Config.BACKUP_PATH, filename)
                stat = os.stat(filepath)
                backup_files.append({
                    'name': filename,
                    'size': f"{stat.st_size / (1024*1024):.2f} MB",
                    'created_at': datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
    
    # Sort by created_at desc
    backup_files.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('admin/backups.html', backups=backup_files)

@admin_bp.route('/backups/trigger', methods=['POST'])
def trigger_backup():
    import shutil
    import datetime
    from config import Config
    
    try:
        # Create backup directory if not exists
        if not os.path.exists(Config.BACKUP_PATH):
            os.makedirs(Config.BACKUP_PATH)
            
        timestamp = format_ist_datetime(now_ist(), "%Y%m%d_%H%M%S")
        backup_filename = f"temple_backup_{timestamp}.db"
        backup_path = os.path.join(Config.BACKUP_PATH, backup_filename)
        
        db = get_db()
        # Use Python's sqlite3 backup API
        # Connect to destination
        import sqlite3
        bck = sqlite3.connect(backup_path)
        db.backup(bck)
        bck.close()
        
        flash(f'Backup created successfully: {backup_filename}', 'success')
        
    except Exception as e:
        import logging
        logging.error(f"Backup failed: {e}", exc_info=True)
        flash('Backup failed. Check logs for details.', 'error')
        
    # Redirect back to where we came from if possible, or support both settings and backups page
    # simpliest is just go to backups page now
    return redirect(url_for('admin.backups'))

@admin_bp.route('/backups/download/<filename>')
def download_backup(filename):
    from config import Config
    import os
    from werkzeug.utils import secure_filename
    
    safe_filename = secure_filename(filename)
    file_path = os.path.join(Config.BACKUP_PATH, safe_filename)
    
    if not os.path.exists(file_path):
        flash('File not found', 'error')
        return redirect(url_for('admin.backups'))
        
    return send_file(file_path, as_attachment=True)

@admin_bp.route('/backups/delete/<filename>', methods=['POST'])
def delete_backup(filename):
    from config import Config
    import os
    from werkzeug.utils import secure_filename
    
    safe_filename = secure_filename(filename)
    file_path = os.path.join(Config.BACKUP_PATH, safe_filename)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            flash(f'Backup deleted: {safe_filename}', 'success')
        else:
            flash('File not found', 'error')
    except Exception as e:
        import logging
        logging.error(f"Error deleting file: {e}", exc_info=True)
        flash('An error occurred while deleting the file.', 'error')
        
    return redirect(url_for('admin.backups'))

@admin_bp.route('/backups/restore/<filename>', methods=['POST'])
def restore_backup(filename):
    from config import Config
    import os
    import sqlite3
    from werkzeug.utils import secure_filename
    
    safe_filename = secure_filename(filename)
    backup_path = os.path.join(Config.BACKUP_PATH, safe_filename)
    
    if not os.path.exists(backup_path):
        flash('Backup file not found.', 'error')
        return redirect(url_for('admin.backups'))
        
    try:
        # Online Restore using SQLite Backup API
        # 1. Open connection to source (backup file)
        src = sqlite3.connect(backup_path)
        
        # 2. Open connection to destination (current DB)
        # We need the direct file path from Config, or get it from active app
        # Config.DB_PATH is reliable here
        dst = sqlite3.connect(Config.DB_PATH)
        
        # 3. Perform backup from Source -> Dest
        with dst:
            src.backup(dst)
            
        dst.close()
        src.close()
        
        flash(f'Database restored successfully from {safe_filename}.', 'success')
        
    except Exception as e:
        import logging
        logging.error(f"Restore failed: {e}", exc_info=True)
        flash('Database restore failed. Check logs for details.', 'error')
        
    return redirect(url_for('admin.backups'))

@admin_bp.route('/backups/upload', methods=['POST'])
def upload_backup():
    from werkzeug.utils import secure_filename
    from config import Config
    import os
    
    if 'backup_file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('admin.backups'))
        
    file = request.files['backup_file']
    
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('admin.backups'))
        
    if file and file.filename.endswith('.db'):
        filename = secure_filename(file.filename)
        # Ensure unique name if exists, or just overwrite?
        # Appending timestamp usually safer if user uploads generic 'temple.db'
        # But user might want specific name. Let's keep name but ensure backup path exists.
        
        if not os.path.exists(Config.BACKUP_PATH):
            os.makedirs(Config.BACKUP_PATH)
            
        save_path = os.path.join(Config.BACKUP_PATH, filename)
        file.save(save_path)
        flash(f'Backup uploaded successfully: {filename}', 'success')
    else:
        flash('Invalid file type. Only .db files are allowed.', 'error')
        
    return redirect(url_for('admin.backups'))

@admin_bp.route('/backups/reset', methods=['POST'])
def reset_database():
    import os
    import datetime
    from config import Config
    import sqlite3
    from database import init_db, get_db
    
    # 1. Force Backup First
    try:
        if not os.path.exists(Config.BACKUP_PATH):
            os.makedirs(Config.BACKUP_PATH)
            
        timestamp = format_ist_datetime(now_ist(), "%Y%m%d_%H%M%S")
        backup_filename = f"pre_reset_backup_{timestamp}.db"
        backup_path = os.path.join(Config.BACKUP_PATH, backup_filename)
        
        # Connect to current DB and backup
        db = get_db()
        bck = sqlite3.connect(backup_path)
        db.backup(bck)
        bck.close()
        
    except Exception as e:
        import logging
        logging.error(f"Reset cancelled: Critical backup failed ({e})", exc_info=True)
        flash('Reset cancelled due to backup failure.', 'error')
        return redirect(url_for('admin.backups'))
        
    # 2. Drop all tables
    try:
        # We need a fresh connection to drop everything or use existing
        # Disable foreign keys to allow dropping tables
        db.execute('PRAGMA foreign_keys=OFF;')
        
        # Get all tables
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        for table in tables:
            if table[0] != 'sqlite_sequence': # Optional: keep sequence or not? Better to drop.
                db.execute(f"DROP TABLE IF EXISTS {table[0]}")
                
        db.commit()
        
        # 3. Re-initialize
        init_db()
        
        flash(f'Database has been reset to factory settings. A backup was saved as {backup_filename}.', 'success')
        
    except Exception as e:
        import logging
        logging.error(f"Reset failed: {e}", exc_info=True)
        flash('Database reset failed. Check logs.', 'error')
        
    return redirect(url_for('admin.backups'))


@admin_bp.route('/updates')
def updates():
    from modules import updater
    from version import get_version
    import requests
    
    # Check for github updates? (Optional, maybe strictly on demand to save quota)
    # Just rendering page for now
    return render_template('admin/updates.html', 
                           current_version=get_version(),
                           updater_status=updater.get_status())

@admin_bp.route('/updates/check')
def check_updates():
    from version import get_version
    current_ver = get_version().lstrip('v')
    
    def parse_version(v_str):
        # Handle v1.2.0 -> [1, 2, 0]
        v_str = v_str.lstrip('v')
        return [int(x) for x in v_str.split('.') if x.isdigit()]

    def is_newer(remote, current):
        r = parse_version(remote)
        c = parse_version(current)
        return r > c

    # Helper to check github releases
    try:
        import requests
        repo_api = "https://api.github.com/repos/theagg-18/devalaya-pro/releases/latest"
        tags_api = "https://api.github.com/repos/theagg-18/devalaya-pro/tags"
        
        headers = {'User-Agent': 'Devalaya-Admin'}

        # 1. Try Releases
        resp = requests.get(repo_api, headers=headers, timeout=5)
        latest_version = None
        download_url = None
        
        if resp.status_code == 200:
            data = resp.json()
            latest_version = data.get('tag_name', 'Unknown')
            download_url = data.get('zipball_url', '')
            
        # 2. Fallback to Tags (if 404 on releases)
        elif resp.status_code == 404:
            resp_tags = requests.get(tags_api, headers=headers, timeout=5)
            if resp_tags.status_code == 200:
                tags = resp_tags.json()
                if tags:
                    latest_tag = tags[0] # First is usually latest
                    latest_version = latest_tag.get('name', 'Unknown')
                    download_url = latest_tag.get('zipball_url', '')

        if latest_version:
             if is_newer(latest_version, current_ver):
                return {
                    'available': True,
                    'version': latest_version,
                    'url': download_url
                }
             else:
                return {
                    'available': False, 
                    'error': f"You are up to date (Latest: {latest_version})"
                }

        return {'available': False, 'error': f"No releases found (GitHub {resp.status_code})"}
            
    except Exception as e:
        import logging
        logging.error(f"Check updates failed: {e}", exc_info=True)
        return {'available': False, 'error': 'Failed to check for updates.'}

@admin_bp.route('/updates/install', methods=['POST'])
def install_update():
    from modules import updater
    
    source = request.form.get('source') # URL or 'local'
    is_url = True
    
    if source == 'local':
        if 'update_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('admin.updates'))
        
        file = request.files['update_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin.updates'))
            
        # Save temp
        import os
        from werkzeug.utils import secure_filename
        update_path = os.path.join(current_app.root_path, 'update_package.zip')
        file.save(update_path)
        source = update_path
        is_url = False
    
    # Start Update Thread
    updater.start_update_thread(source, is_url)
    flash('Update process started. System will restart automatically.', 'info')
    return redirect(url_for('admin.updates'))

@admin_bp.route('/updates/status')
def update_status():
    from modules import updater
    return updater.get_status()
