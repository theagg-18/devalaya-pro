from flask import Blueprint, render_template, request, flash, redirect, url_for, g, session
from database import get_db
from routes.auth import login_required

cashier_bp = Blueprint('cashier', __name__, url_prefix='/cashier')

@cashier_bp.route('/')
@login_required
def index():
    if g.user['role'] != 'cashier':
        return redirect(url_for('admin.index'))
        
    db = get_db()
    
    # Check for active session
    active_session = db.execute(
        'SELECT * FROM cashier_sessions WHERE cashier_id = ? AND is_active = 1',
        (g.user['id'],)
    ).fetchone()
    
    if not active_session:
        return redirect(url_for('cashier.select_printer'))
        
    # Load printer details
    printer = db.execute('SELECT * FROM printers WHERE id = ?', (active_session['printer_id'],)).fetchone()
    
    return render_template('cashier/dashboard.html', printer=printer)

@cashier_bp.route('/select-printer', methods=('GET', 'POST'))
@login_required
def select_printer():
    if g.user['role'] != 'cashier':
        return redirect(url_for('admin.index'))
    
    db = get_db()
    
    if request.method == 'POST':
        printer_id = request.form['printer_id']
        
        # Deactivate any old sessions
        db.execute('UPDATE cashier_sessions SET is_active = 0 WHERE cashier_id = ?', (g.user['id'],))
        
        # Create new session
        db.execute('INSERT INTO cashier_sessions (cashier_id, printer_id) VALUES (?, ?)',
                   (g.user['id'], printer_id))
        db.commit()
        
        return redirect(url_for('cashier.index'))

    # Show only active printers
    printers = db.execute('SELECT * FROM printers WHERE is_active = 1').fetchall()
    return render_template('cashier/select_printer.html', printers=printers)

@cashier_bp.route('/release-printer')
@login_required
def release_printer():
    db = get_db()
    db.execute('UPDATE cashier_sessions SET is_active = 0 WHERE cashier_id = ?', (g.user['id'],))
    db.commit()
    flash('Printer released', 'info')
    return redirect(url_for('cashier.select_printer'))

# --- Billing Logic ---

STARS = [
    {"eng": "Ashwati", "mal": "അശ്വതി"},
    {"eng": "Bharani", "mal": "ഭരണി"},
    {"eng": "Karthika", "mal": "കാർത്തിക"},
    {"eng": "Rohini", "mal": "രോഹിണി"},
    {"eng": "Makayiram", "mal": "മകയിരം"},
    {"eng": "Thiruvathira", "mal": "തിരുവാതിര"},
    {"eng": "Punartham", "mal": "പുണർതം"},
    {"eng": "Pooyam", "mal": "പൂയം"},
    {"eng": "Ayilyam", "mal": "ആയില്യം"},
    {"eng": "Makam", "mal": "മകം"},
    {"eng": "Pooram", "mal": "പൂരം"},
    {"eng": "Uthram", "mal": "ഉത്രം"},
    {"eng": "Atham", "mal": "അത്തം"},
    {"eng": "Chithira", "mal": "ചിത്തിര"},
    {"eng": "Choti", "mal": "ചോതി"},
    {"eng": "Vishakham", "mal": "വിശാഖം"},
    {"eng": "Anizham", "mal": "അനിഴം"},
    {"eng": "Thrikketta", "mal": "തൃക്കേട്ട"},
    {"eng": "Moolam", "mal": "മൂലം"},
    {"eng": "Pooradam", "mal": "പൂരാടം"},
    {"eng": "Uthradam", "mal": "ഉത്രാടം"},
    {"eng": "Thiruvonam", "mal": "തിരുവോണം"},
    {"eng": "Avittam", "mal": "അവിട്ടം"},
    {"eng": "Chathayam", "mal": "ചതയം"},
    {"eng": "Pooruruttathi", "mal": "പൂരുരുട്ടാതി"},
    {"eng": "Uthrattathi", "mal": "ഉത്രട്ടാതി"},
    {"eng": "Revathi", "mal": "രേവതി"}
]

@cashier_bp.route('/history')
@login_required
def history():
    db = get_db()
    query = request.args.get('q', '')
    
    sql = "SELECT * FROM bills WHERE cashier_id = ? AND status != 'draft'"
    params = [g.user['id']]
    
    # Date Filter Logic (Same as Admin Reports)
    date_filter = request.args.get('date')
    
    if query:
        # Search by Bill No or Devotee Name (Global Search)
        sql += ' AND (bill_no LIKE ? OR devotee_name LIKE ?)'
        wildcard = f'%{query}%'
        params.extend([wildcard, wildcard])
        
        # Explicitly clear date filter so UI shows we searched everywhere
        date_filter = ''
    else:
        if date_filter:
            sql += ' AND date(created_at) = ?'
            params.append(date_filter)
        else:
            # Default to today
            import datetime
            today = datetime.date.today().isoformat()
            sql += ' AND date(created_at) = ?'
            params.append(today)
            date_filter = today

    sql += ' ORDER BY created_at DESC LIMIT 50'
    
    bills = db.execute(sql, params).fetchall()
    
    # Fetch items for each bill
    bill_list = []
    for bill in bills:
        # Convert row to dict to add items
        b_dict = dict(bill)
        b_dict['line_items'] = db.execute('''
            SELECT bi.*, pm.name 
            FROM bill_items bi 
            JOIN puja_master pm ON bi.puja_id = pm.id 
            WHERE bi.bill_id = ?
        ''', (bill['id'],)).fetchall()
        
        # Format Dates
        try:
             from datetime import datetime as dt, timezone
             
             # Format created_at
             if b_dict.get('created_at'):
                 raw_ts = b_dict['created_at']
                 if isinstance(raw_ts, str):
                     # Handle potential ISO format with or without T, and microseconds
                     # Simple approach: try parsing common formats
                     try:
                        ts_obj = dt.strptime(raw_ts, '%Y-%m-%d %H:%M:%S')
                     except ValueError:
                        try:
                            # Try with T separator
                            ts_obj = dt.strptime(raw_ts, '%Y-%m-%dT%H:%M:%S')
                        except ValueError:
                             # Try with microseconds
                             ts_obj = dt.strptime(raw_ts.split('.')[0], '%Y-%m-%d %H:%M:%S')
                     
                     # Convert UTC (DB Default) to System Local Time
                     local_ts = ts_obj.replace(tzinfo=timezone.utc).astimezone()
                     b_dict['created_at'] = local_ts.strftime('%d-%m-%Y %I:%M %p')
                 elif isinstance(raw_ts, dt):
                      # If it's already a datetime object, assume it's naive UTC from SQL
                      local_ts = raw_ts.replace(tzinfo=timezone.utc).astimezone()
                      b_dict['created_at'] = local_ts.strftime('%d-%m-%Y %I:%M %p')

             # Format scheduled_date
             if b_dict.get('scheduled_date'):
                 raw_date = b_dict['scheduled_date']
                 if isinstance(raw_date, str):
                     try:
                        date_obj = dt.strptime(raw_date, '%Y-%m-%d')
                        b_dict['scheduled_date'] = date_obj.strftime('%d-%m-%Y')
                     except:
                        pass # Keep original string if parse fails
                 elif hasattr(raw_date, 'strftime'):
                     b_dict['scheduled_date'] = raw_date.strftime('%d-%m-%Y')
                     
        except Exception as e:
            print(f"Date formatting error: {e}")
            import traceback
            traceback.print_exc()
            
        bill_list.append(b_dict)
    
    return render_template('cashier/history.html', bills=bill_list, query=query, date_filter=date_filter)

@cashier_bp.route('/billing/mode/<mode>')
@login_required
def start_billing(mode):
    if g.user['role'] != 'cashier':
        return redirect(url_for('admin.index'))
    
    if mode not in ['vazhipadu', 'donation']:
        return redirect(url_for('cashier.index'))
    
    # Initialize connection specific to this request
    db = get_db()
    
    # Check session
    active_session = db.execute(
        'SELECT * FROM cashier_sessions WHERE cashier_id = ? AND is_active = 1',
        (g.user['id'],)
    ).fetchone()
    if not active_session:
        return redirect(url_for('cashier.select_printer'))

    # Load Puja/Items based on mode
    # If mode is vazhipadu, show only 'puja' type, else 'item' type? 
    # Or show all but filter? Requirements implication: 
    # Mode 1: Puja (Vazhipadu). Mode 2: Items/Donation.
    type_filter = 'puja' if mode == 'vazhipadu' else 'item'
    items = db.execute('SELECT * FROM puja_master WHERE type = ? ORDER BY name', (type_filter,)).fetchall()
    return render_template('cashier/billing.html', mode=mode, stars=STARS, items=items, 
                           cart=session.get('cart', {'items': [], 'total': 0}), 
                           batch=session.get('batch', []))

@cashier_bp.route('/billing/cart/update', methods=['POST'])
@login_required
def update_cart():
    # Helper to manage cart in session
    # Expects JSON: { action: 'add'|'remove'|'set_details', ... }
    data = request.json
    cart = session.get('cart', {'items': [], 'total': 0})
    
    if data['action'] == 'init':
        # Preserve details if changing modes? No, clear mostly.
        cart = {'mode': data['mode'], 'items': [], 'total': 0, 'devotee_name': '', 'star': '', 'scheduled_date': ''}
        
    elif data['action'] == 'set_details':
        cart['devotee_name'] = data.get('name', '')
        cart['star'] = data.get('star', '')
        cart['scheduled_date'] = data.get('scheduled_date', '')
        
    elif data['action'] == 'add':
        item_id = int(data['id'])
        name = data['name']
        amount = float(data['amount'])
        
        # Check if item exists
        found = False
        for item in cart['items']:
            if item['id'] == item_id:
                item['count'] += 1
                item['total'] = item['count'] * item['amount']
                found = True
                break
        if not found:
            cart['items'].append({
                'id': item_id, 'name': name, 'amount': amount, 'count': 1, 'total': amount
            })
            
    elif data['action'] == 'remove':
        item_id = int(data['id'])
        cart['items'] = [i for i in cart['items'] if i['id'] != item_id]

    elif data['action'] == 'update_quantity':
        item_id = int(data['id'])
        new_qty = int(data['count'])
        
        if new_qty <= 0:
            # Remove item if quantity is zero or less
            cart['items'] = [i for i in cart['items'] if i['id'] != item_id]
        else:
            # Update quantity
            for item in cart['items']:
                if item['id'] == item_id:
                    item['count'] = new_qty
                    item['total'] = new_qty * item['amount']
                    break

    # Recalculate global total
    cart['total'] = sum(i['total'] for i in cart['items'])
    session['cart'] = cart
    session.modified = True
    
    return {'status': 'success', 'cart': cart}

@cashier_bp.route('/billing/batch/add', methods=['POST'])
@login_required
def add_to_batch():
    cart = session.get('cart')
    if not cart or not cart['items']:
        return {'status': 'error', 'message': 'Cart is empty'}

    data = request.json or {}
    replication_dates = data.get('dates', []) # List of "YYYY-MM-DD" strings

    batch = session.get('batch', [])
    
    if replication_dates:
        # Replicate Mode
        import copy
        count_added = 0
        for date_str in replication_dates:
            # Deep copy to ensure unique objects
            cart_copy = copy.deepcopy(cart)
            cart_copy['scheduled_date'] = date_str
            batch.append(cart_copy)
            count_added += 1
    else:
        # Standard Single Add
        batch.append(cart)
    
    session['batch'] = batch
    
    # Clear cart but keep mode
    session['cart'] = {'mode': cart.get('mode', 'vazhipadu'), 'items': [], 'total': 0, 'devotee_name': '', 'star': '', 'scheduled_date': ''}
    session.modified = True
    
    return {'status': 'success', 'batch_count': len(batch)}

@cashier_bp.route('/billing/batch/clear', methods=['POST'])
@login_required
def clear_batch():
    session.pop('batch', None)
    return {'status': 'success'}

@cashier_bp.route('/billing/batch/recall', methods=['POST'])
@login_required
def recall_batch_entry():
    idx = request.json.get('index')
    batch = session.get('batch', [])
    
    if idx is None or idx < 0 or idx >= len(batch):
        return {'status': 'error', 'message': 'Invalid batch index'}
        
    # Check if current cart is empty to avoid overwriting
    current_cart = session.get('cart')
    if current_cart and current_cart.get('items'):
        return {'status': 'error', 'message': 'Current cart is not empty. Please clear or batch it first.'}
        
    # Pop from batch and set as cart
    entry = batch.pop(idx)
    session['batch'] = batch
    session['cart'] = entry
    session.modified = True
    
    return {'status': 'success'}

@cashier_bp.route('/billing/batch/remove-entry', methods=['POST'])
@login_required
def remove_batch_entry():
    idx = request.json.get('index')
    batch = session.get('batch', [])
    
    if idx is None or idx < 0 or idx >= len(batch):
        return {'status': 'error', 'message': 'Invalid batch index'}
        
    batch.pop(idx)
    session['batch'] = batch
    session.modified = True
    
    return {'status': 'success'}

@cashier_bp.route('/billing/checkout', methods=['POST'])
@login_required
def checkout():
    # Supports both Single Checkout (from Cart) and Batch Checkout
    data = request.json
    is_batch = data.get('is_batch', False)
    group_by = data.get('group_by', 'devotee') # 'devotee' or 'puja'
    
    items_to_process = []
    
    if is_batch:
        batch = session.get('batch', [])
        if not batch:
             return {'status': 'error', 'message': 'Batch is empty'}
        items_to_process = batch
    else:
        cart = session.get('cart')
        if not cart or not cart['items']:
            return {'status': 'error', 'message': 'Cart is empty'}
        items_to_process = [cart]

    db = get_db()
    
    # Get active session info
    c_session = db.execute(
        'SELECT * FROM cashier_sessions WHERE cashier_id = ? AND is_active = 1',
        (g.user['id'],)
    ).fetchone()
    
    if not c_session:
        return {'status': 'error', 'message': 'Printer session invalid'}

    try:
        printer_name = db.execute('SELECT name FROM printers WHERE id=?', (c_session['printer_id'],)).fetchone()[0]
        
        from modules.printers import printer_manager
        
        full_print_content = ""
        bill_ids = []

        # 1. Get Initial Sequence (Start from Max)
        last_seq = db.execute('SELECT MAX(bill_seq) FROM bills').fetchone()[0]
        if last_seq is None:
            last_seq = 0
            
        current_seq_counter = last_seq

        # Process each "Cart" in the batch
        for bill_data in items_to_process:
             # Create Bill
            name = bill_data.get('devotee_name')
            star = bill_data.get('star')
            b_type = bill_data.get('mode', 'vazhipadu')
            draft_id = bill_data.get('draft_id')
            
            # Insert with Status
            status = 'printed' 
            scheduled_date = bill_data.get('scheduled_date')
            
            if draft_id:
                # REUSE existing Draft
                bill_id = draft_id
                
                # Update Draft to Printed
                db.execute(
                    '''UPDATE bills SET 
                       printer_id=?, total_amount=?, devotee_name=?, star=?, scheduled_date=?, status='printed', type=?, created_at=CURRENT_TIMESTAMP
                       WHERE id=?''', 
                    (c_session['printer_id'], bill_data['total'], name, star, scheduled_date, b_type, bill_id)
                )
                
                # Delete old items to overwrite with new cart state (in case edited)
                db.execute('DELETE FROM bill_items WHERE bill_id=?', (bill_id,))
                
            else:
                # Create NEW Bill
                cur = db.execute(
                    '''INSERT INTO bills (bill_no, bill_seq, cashier_id, printer_id, total_amount, devotee_name, star, scheduled_date, type, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (None, current_seq_counter, g.user['id'], c_session['printer_id'], bill_data['total'], name, star, scheduled_date, b_type, status)
                )
                bill_id = cur.lastrowid
            
            # GENERATE SEQUENTIAL BILL NUMBER
            current_seq_counter += 1
            new_seq = current_seq_counter
            
            # Format Bill No: B-{year}-{seq}
            import datetime
            year = datetime.datetime.now().year
            bill_no = f"B-{year}-{new_seq}"
            
            # Update Bill with Seq and No
            db.execute('UPDATE bills SET bill_seq = ?, bill_no = ? WHERE id = ?', (new_seq, bill_no, bill_id))
            
            bill_ids.append(bill_no) # Store formatted Bill No string for printing
            
            # Add Items
            for item in bill_data['items']:
                db.execute(
                    '''INSERT INTO bill_items (bill_id, puja_id, price_snapshot, count, total)
                       VALUES (?, ?, ?, ?, ?)''',
                    (bill_id, item['id'], item['amount'], item['count'], item['total'])
                )
        
        # GENERATE PRINT CONTENT
        # Logic: 
        # If "Group by Devotee" (Default):
        #   Iterate Bills -> Iterate Items -> Print One Slip per Puja (REQUIREMENT: One Puja = One Page)
        #   Wait, "One Puja = One Page" applies to MODE 1.
        #   So:
        #   Bill A (Devotee A):
        #       - Item 1 (Pushpanjali) -> Page 1
        #       - Item 2 (Archana) -> Page 2
        #   Bill B (Devotee B):
        #       - Item 1 -> Page 3
        
        # If "Group by Puja" (Option):
        #   Collates all "Pushpanjali" together?
        #   "Group by Puja (Item-wise)"
        #   This likely means:
        #   Page 1: Pushpanjali List (Devotee A, Devotee B...)
        #   Page 2: Archana List (Devotee A...)
        #   This is a summary mode. Useful for the Poojari.
        
        # Let's implement at least Default (Devotee-wise) which is straightforward.
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
        
        # Fetch Temple Header
        settings = db.execute('SELECT * FROM temple_settings WHERE id=1').fetchone()
        header = f"{settings['name_mal']}\n{settings['name_eng']}\n"
        footer = f"\n{settings['receipt_footer']}\n"
        
        print_slips = [] # Store individual slips
        
        # Helper to format slip text
        def format_slip(b_id, d_name, d_star, items, timestamp, header, footer, scheduled_date=None):
            slip = f"{header}\n"
            slip += f"Bill: {b_id} | {timestamp}\n"
            
            # Print Scheduled Date
            if scheduled_date:
                try:
                    from datetime import datetime as dt
                    s_dt = dt.strptime(scheduled_date, '%Y-%m-%d').strftime('%d-%m-%Y')
                    slip += f"Vazhipadu Date: {s_dt}\n"
                except:
                    slip += f"Vazhipadu Date: {scheduled_date}\n"

            # Malayalam Star Translation
            star_map = {s['eng']: s['mal'] for s in STARS}
            star_disp = star_map.get(d_star, d_star)
            if star_disp != d_star:
                slip += f"Name: {d_name}\nStar: {star_disp} ({d_star})\n"
            else:
                slip += f"Name: {d_name}  Star: {d_star}\n"
                
            slip += "--------------------------------\n"
            for item in items:
                slip += f"{item['name']}\n"
                slip += f"Qty: {item.get('count', item.get('qty', 1))}  Amt: {item.get('total', 0)}\n"
            slip += "--------------------------------\n"
            slip += f"{footer}"
            return slip

        if group_by == 'devotee':
            for i, bill_data in enumerate(items_to_process):
                b_id = bill_ids[i]
                dev_name = bill_data.get('devotee_name') or "Devotee"
                dev_star = bill_data.get('star') or ""
                scheduled_date = bill_data.get('scheduled_date')
                
                # Iterate each item for "One Puja = One Slip"
                for item in bill_data['items']:
                    single_item_slip = format_slip(b_id, dev_name, dev_star, [item], timestamp, header, footer, scheduled_date)
                    print_slips.append(single_item_slip)

        elif group_by == 'puja':
             # ... (Same logic, but grouping items differently)
             # Collect all items
            all_items = []
            for idx, bill_data in enumerate(items_to_process):
                b_num = bill_ids[idx]
                d_name = bill_data.get('devotee_name')
                d_star = bill_data.get('star')
                for item in bill_data['items']:
                    all_items.append({
                        'bill_no': b_num, # Capture real Bill No
                        'name': item['name'],
                        'devotee': d_name,
                        'star': d_star,
                        'qty': item['count'],
                        'total': item['total'],
                        'scheduled_date': bill_data.get('scheduled_date')
                    })
            all_items.sort(key=lambda x: x['name'])
            
            for item in all_items:
                # Use Standard Format Helper
                slip = format_slip(
                    item['bill_no'], 
                    item['devotee'], 
                    item['star'], 
                    [item], # Pass single item as list
                    timestamp, 
                    header, 
                    footer,
                    item.get('scheduled_date')
                )
                print_slips.append(slip)
        
        if is_batch:
            # Summary Slip
            total_bills = len(items_to_process)
            grand_total = sum(b['total'] for b in items_to_process)
            
            summary = f"{header}\n"
            summary += "****** TOTAL AMOUNT ******\n"
            summary += f"Time: {timestamp}\n"
            summary += f"Total Bills: {total_bills}\n"
            summary += f"Grand Total: {grand_total:.2f}\n"
            summary += "***************************\n"
            print_slips.append(summary)

        # GENERATE FINAL OUTPUT BASED ON PRINTER TYPE
        cut_cmd = "\n\n\n\x1dV\x00"
        
        if printer_name == 'WEB_BROWSER_PRINT':
            # Prepare data for template
            slips_data = [] # List of slip dictionaries
            
            # Helper to create slip data object
            def create_slip_data(b_no, d_name, d_star, items, scheduled_date=None):
                total = sum(i.get('total', 0) for i in items)
                
                # Format Scheduled Date
                s_date_str = None
                if scheduled_date:
                    try:
                        from datetime import datetime as dt
                        s_date_str = dt.strptime(scheduled_date, '%Y-%m-%d').strftime('%d-%m-%Y')
                    except:
                        s_date_str = str(scheduled_date)
                        
                # Star Translation
                star_map = {s['eng']: s['mal'] for s in STARS}
                star_disp = star_map.get(d_star, d_star)
                
                return {
                    'bill_no': b_no,
                    'devotee_name': d_name,
                    'star': star_disp,
                    'scheduled_date': s_date_str,
                    'line_items': items,
                    'total': total
                }

            if group_by == 'devotee':
                for i, bill_data in enumerate(items_to_process):
                    b_id = bill_ids[i]
                    dev_name = bill_data.get('devotee_name') or "Devotee"
                    dev_star = bill_data.get('star') or ""
                    scheduled_date = bill_data.get('scheduled_date')
                    
                    # Iterate each item for "One Puja = One Slip"
                    for item in bill_data['items']:
                        # Single item slip
                        slips_data.append(create_slip_data(b_id, dev_name, dev_star, [item], scheduled_date))

            elif group_by == 'puja':
                # Consolidate by Item Type Logic (Complex, sticking to simple list for now)
                # Re-using the same consolidation logic from before?
                # The previous logic was: One slip per item occurrence but sorted? 
                # "One Puja = One Page" implies independent slips.
                # So we just iterate all items across all bills.
                
                all_entries = []
                for idx, bill_data in enumerate(items_to_process):
                    b_num = bill_ids[idx]
                    d_name = bill_data.get('devotee_name')
                    d_star = bill_data.get('star')
                    s_date = bill_data.get('scheduled_date')
                    
                    for item in bill_data['items']:
                        all_entries.append({
                            'bill_no': b_num,
                            'devotee_name': d_name,
                            'star': d_star,
                            'scheduled_date': s_date,
                            'item': item # Single item
                        })
                
                # Sort by Item Name
                all_entries.sort(key=lambda x: x['item']['name'])
                
                for entry in all_entries:
                    slips_data.append(create_slip_data(
                        entry['bill_no'], 
                        entry['devotee_name'], 
                        entry['star'], 
                        [entry['item']], 
                        entry['scheduled_date']
                    ))
            
            # Render Template from DB
            from flask import render_template_string
            
            # Ensure template content exists, else fallback? (DB init ensures it, but safe to check)
            template_content = settings['print_template_content']
            if not template_content:
                # Fallback purely for safety if migration failed
                template_content = "<h1>Error: No Print Template Found. Contact Admin.</h1>"
                
            html_content = render_template_string(template_content, 
                                         slips=slips_data, 
                                         settings=settings, 
                                         timestamp=timestamp)
            
            db.commit()
            if is_batch: session.pop('batch', None)
            else: session.pop('cart', None)
                
            return {'status': 'print_web', 'content': html_content}

        # Physical Printer
        # Join with Cut Commands
        full_text_content = cut_cmd.join(print_slips) + cut_cmd
        
        printer_manager.print_text(printer_name, full_text_content)
        
        # Commit DB
        db.commit()
        
        # Clear Session
        if is_batch:
            session.pop('batch', None)
        else:
            session.pop('cart', None)
        
        return {'status': 'success'}
        
    except Exception as e:
        import traceback
        with open('debug_checkout.log', 'w') as f:
            f.write(str(e))
            f.write(traceback.format_exc())
        return {'status': 'error', 'message': str(e)}

@cashier_bp.route('/billing/cart/resume-draft', methods=['POST'])
@login_required
def resume_client_draft():
    data = request.json
    session['cart'] = data['cart']
    session.modified = True
    return {'status': 'success'}

@cashier_bp.route('/billing/reprint/<int:bill_id>', methods=['POST'])
@login_required
def reprint_bill(bill_id):
    db = get_db()
    
    # 1. Fetch Bill
    bill = db.execute('SELECT * FROM bills WHERE id = ?', (bill_id,)).fetchone()
    if not bill:
        return {'status': 'error', 'message': 'Bill not found'}
        
    # 2. Fetch Items
    items = db.execute('''
        SELECT bi.*, pm.name 
        FROM bill_items bi 
        JOIN puja_master pm ON bi.puja_id = pm.id 
        WHERE bi.bill_id = ?
    ''', (bill['id'],)).fetchall()
    
    # 3. Fetch Settings
    settings = db.execute('SELECT * FROM temple_settings WHERE id=1').fetchone()
    
    # 4. Prepare Data for Template
    import datetime
    from flask import render_template_string
    
    # Determine timestamp to show (Original print time or Now? "Reprint" usually implies copy)
    # Let's show "Reprinted: <Now>" or just original details?
    # Requirement: "Reprint" usually duplicates original.
    # But usually receipts show create time. Let's use original create time.
    timestamp = bill['created_at'] # String from DB
    try:
         from datetime import datetime as dt, timezone
         
         if timestamp:
             if isinstance(timestamp, str):
                 try:
                    ts_obj = dt.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                 except ValueError:
                    try:
                        ts_obj = dt.strptime(timestamp, '%Y-%m-%dT%H:%M:%S')
                    except ValueError:
                         try:
                             ts_obj = dt.strptime(timestamp.split('.')[0], '%Y-%m-%d %H:%M:%S')
                         except:
                             ts_obj = None
                 
                 if ts_obj:
                     # Convert UTC to Local
                     local_ts = ts_obj.replace(tzinfo=timezone.utc).astimezone()
                     timestamp = local_ts.strftime('%d-%m-%Y %H:%M')
             elif isinstance(timestamp, dt):
                  local_ts = timestamp.replace(tzinfo=timezone.utc).astimezone()
                  timestamp = local_ts.strftime('%d-%m-%Y %H:%M')

    except Exception as e:
         print(f"Reprint Date Error: {e}")
         pass # Keep original if parse fails
    
    # Convert DB Items to Dict list matching template expectation
    line_items = []
    for item in items:
        # DB columns: count, total, price_snapshot... template needs: name, count, total
        line_items.append({
            'name': item['name'],
            'count': item['count'],
            'total': item['total']
        })
        
    # Star Translation
    star_map = {s['eng']: s['mal'] for s in STARS}
    star_disp = star_map.get(bill['star'], bill['star'])
    
    # Format Scheduled Date
    scheduled_date = bill['scheduled_date']
    s_date_str = None
    if scheduled_date:
        try:
             from datetime import datetime as dt
             if isinstance(scheduled_date, str):
                 try:
                    s_date_str = dt.strptime(scheduled_date, '%Y-%m-%d').strftime('%d-%m-%Y')
                 except:
                    s_date_str = scheduled_date
             elif hasattr(scheduled_date, 'strftime'):
                 s_date_str = scheduled_date.strftime('%d-%m-%Y')
        except:
             s_date_str = str(scheduled_date)

    slip_data = {
        'bill_no': bill['bill_no'],
        'devotee_name': bill['devotee_name'],
        'star': star_disp,
        'scheduled_date': s_date_str,
        'line_items': line_items,
        'total': bill['total_amount']
    }
    
    # 5. Render
    template_content = settings['print_template_content']
    if not template_content:
        template_content = "<h1>Error: Print Template Missing</h1>"
        
    # Note: Template expects 'slips' as a LIST of slips
    html_content = render_template_string(template_content, 
                                 slips=[slip_data], 
                                 settings=settings, 
                                 timestamp=timestamp)
                                 
    return {'status': 'print_web', 'content': html_content}
