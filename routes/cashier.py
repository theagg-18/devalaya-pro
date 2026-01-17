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
    {"eng": "Swathi (Choti)", "mal": "ചോതി (സ്വാതി)"},
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
    
    sql = 'SELECT * FROM bills WHERE cashier_id = ?'
    params = [g.user['id']]
    
    if query:
        # Search by Bill No or Devotee Name
        sql += ' AND (bill_no LIKE ? OR devotee_name LIKE ?)'
        wildcard = f'%{query}%'
        params.extend([wildcard, wildcard])
        
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
        bill_list.append(b_dict)
    
    return render_template('cashier/history.html', bills=bill_list, query=query)

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

    batch = session.get('batch', [])
    # Append current cart as a bill entry
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
            # Format content for HTML display
            # Wrap each slip in a div with page-break-after
            html_body = ""
            for slip in print_slips:
                html_body += f'<div class="slip"><pre>{slip}</pre></div>'
            
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: monospace; font-size: 14px; width: 300px; margin: 0 auto; }}
                    .slip {{ margin-bottom: 20px; page-break-after: always; padding-bottom: 20px; border-bottom: 1px dashed #ccc; }}
                    pre {{ white-space: pre-wrap; margin: 0; }}
                </style>
            </head>
            <body style="margin: 0; padding: 20px;">
                {html_body}
            </body>
            </html>
            """
            
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

@cashier_bp.route('/billing/draft/save', methods=['POST'])
@login_required
def save_draft():
    db = get_db()
    cart = session.get('cart')
    
    if not cart or not cart['items']:
        return {'status': 'error', 'message': 'Cart is empty'}

    try:
        name = cart.get('devotee_name')
        star = cart.get('star')
        b_type = cart.get('mode', 'vazhipadu')
        
        # 1. Create Bill with status 'draft'
        cursor = db.execute(
            '''INSERT INTO bills (cashier_id, printer_id, total_amount, devotee_name, star, status, type)
               VALUES (?, ?, ?, ?, ?, 'draft', ?)''', 
            (g.user['id'], None, cart['total'], name, star, b_type)
        )
        bill_id = cursor.lastrowid
        
        # 2. Generate Draft Bill No
        import datetime
        year = datetime.datetime.now().year
        bill_no = f"DRAFT-{year}-{bill_id}" # Distinct format
        
        db.execute('UPDATE bills SET bill_no = ? WHERE id = ?', (bill_no, bill_id))
        
        # 3. Add Items
        for item in cart['items']:
            db.execute(
                '''INSERT INTO bill_items (bill_id, puja_id, price_snapshot, count, total)
                   VALUES (?, ?, ?, ?, ?)''',
                (bill_id, item['id'], item['amount'], item['count'], item['total'])
            )
            
        db.commit()
        
        # Clear Cart
        session.pop('cart', None)
        
        return {'status': 'success', 'bill_no': bill_no}
        
    except Exception as e:
        import traceback
        with open('debug_error.log', 'w') as f:
            f.write(str(e))
            f.write(traceback.format_exc())
            
        print(f"SAVE DRAFT ERROR: {e}")
        return {'status': 'error', 'message': f"Server Error: {str(e)}"}

@cashier_bp.route('/billing/draft/resume/<int:bill_id>')
@login_required
def resume_draft(bill_id):
    db = get_db()
    
    # Fetch Bill
    bill = db.execute('SELECT * FROM bills WHERE id = ? AND cashier_id = ?', (bill_id, g.user['id'])).fetchone()
    if not bill:
        flash("Draft not found", "error")
        return redirect(url_for('cashier.history'))
        
    # Fetch Items
    items = db.execute('SELECT * FROM bill_items WHERE bill_id = ?', (bill_id,)).fetchall()
    
    # Reconstruct Cart
    cart_items = []
    for item in items:
        # Fetch name from master
        name = db.execute('SELECT name FROM puja_master WHERE id = ?', (item['puja_id'],)).fetchone()[0]
        
        cart_items.append({
            'id': item['puja_id'],
            'name': name,
            'amount': item['price_snapshot'],
            'count': item['count'],
            'total': item['total']
        })
        
    session['cart'] = {
        'draft_id': bill['id'], # Store ID to reuse
        'mode': bill['type'], # 'vazhipadu' or 'donation'
        'devotee_name': bill['devotee_name'],
        'star': bill['star'],
        'items': cart_items,
        'total': bill['total_amount']
    }
    session.modified = True
    
    flash("Draft Resumed!", "success")
    return redirect(url_for('cashier.start_billing', mode=bill['type']))
