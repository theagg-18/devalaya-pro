from flask import Blueprint, jsonify, request
from modules.panchang import get_nakshatra_for_date, get_next_occurrences, get_malayalam_date
import datetime

utility_bp = Blueprint('utility', __name__, url_prefix='/utility')

@utility_bp.route('/get-star')
def get_star():
    date_str = request.args.get('date') # YYYY-MM-DD
    if not date_str:
        return jsonify({'status': 'error', 'message': 'Date is required'}), 400
        
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        star = get_nakshatra_for_date(date_obj)
        mal_date = get_malayalam_date(date_obj)
        return jsonify({
            'status': 'success',
            'date': date_str,
            'nakshatra_eng': star['eng'],
            'nakshatra_mal': star['mal'],
            'mal_date_str': f"{mal_date['day']} {mal_date['mal_month']} {mal_date['mal_year']}",
            'mal_date_details': mal_date
        })
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'An internal error has occurred.'}), 500

@utility_bp.route('/get-next-star-dates')
def get_next_star_dates():
    star_name = request.args.get('star_name')
    start_date = request.args.get('start_date')
    
    if not star_name:
        return jsonify({'status': 'error', 'message': 'star_name is required'}), 400
        
    try:
        s_date = None
        if start_date:
             s_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
             
        months = request.args.get('months')
        dates = get_next_occurrences(star_name, s_date, months=months)
        return jsonify({
            'status': 'success',
            'star_name': star_name,
            'dates': dates
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'An internal error has occurred.'}), 500
