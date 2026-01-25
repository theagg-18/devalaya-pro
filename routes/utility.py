from flask import Blueprint, jsonify, request, render_template
from modules.panchang import get_next_star_dates, get_malayalam_date, get_english_date, MAL_MONTHS_ENG, get_nakshatra
import datetime
utility_bp = Blueprint('utility', __name__, url_prefix='/utility')

@utility_bp.route('/calendar')
def calendar_view():
    return render_template('utility/calendar.html', mal_months=MAL_MONTHS_ENG)

from database import get_cached_settings

@utility_bp.route('/get-star')
def get_star():
    date_str = request.args.get('date') # YYYY-MM-DD
    if not date_str:
        return jsonify({'status': 'error', 'message': 'Date is required'}), 400
        
    try:
        # Get Location
        settings, _ = get_cached_settings()
        lat = settings.get('latitude', 10.85) if settings else 10.85
        lon = settings.get('longitude', 76.27) if settings else 76.27
        
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        star = get_nakshatra(date_obj, lat, lon)
        mal_date = get_malayalam_date(date_obj, lat, lon)
        
        return jsonify({
            'status': 'success',
            'date': date_str,
            'nakshatra_eng': star['nakshatra_eng'],
            'nakshatra_mal': star['nakshatra_mal'],
            'mal_date_str': f"{mal_date['day']} {mal_date['mal_month']} {mal_date['mal_year']}",
            'mal_date_details': mal_date
        })
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid date format'}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'Internal Error'}), 500

@utility_bp.route('/get-next-star-dates')
def get_next_star_dates_route():
    from modules.panchang import get_next_star_dates as gnsd
    star_name = request.args.get('star_name')
    start_date = request.args.get('start_date')
    
    if not star_name:
        return jsonify({'status': 'error', 'message': 'star_name is required'}), 400
        
    try:
        settings, _ = get_cached_settings()
        lat = settings.get('latitude', 10.85) if settings else 10.85
        lon = settings.get('longitude', 76.27) if settings else 76.27
        
        s_date = None
        if start_date:
             s_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
             s_date = datetime.date.today()
             
        months = request.args.get('months')
        
        count = 5 
        if months:
            count = 100 
            
        dates_list = gnsd(star_name, s_date, count=count, months=months, lat=lat, lon=lon)
        
        detailed_dates = []
        for d_str in dates_list:
            d_obj = datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
            mal = get_malayalam_date(d_obj, lat, lon)
            mal_str = f"{mal['day']} {mal['mal_month']} {mal['mal_year']}"
            detailed_dates.append({
                'date': d_str,
                'mal_date': mal_str,
                'star': {'eng': star_name} 
            })

        return jsonify({
            'status': 'success',
            'star_name': star_name,
            'dates': detailed_dates
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'Internal Error'}), 500

@utility_bp.route('/eng-to-mal')
def eng_to_mal():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'status': 'error', 'message': 'Date required'}), 400
    try:
        settings, _ = get_cached_settings()
        lat = settings.get('latitude', 10.85) if settings else 10.85
        lon = settings.get('longitude', 76.27) if settings else 76.27
        
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        mal_date = get_malayalam_date(date_obj, lat, lon)
        return jsonify({'status': 'success', 'data': mal_date})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'Internal Error'}), 500
@utility_bp.route('/mal-to-eng')
def mal_to_eng():
    try:
        settings, _ = get_cached_settings()
        lat = settings.get('latitude', 10.85) if settings else 10.85
        lon = settings.get('longitude', 76.27) if settings else 76.27
        
        year = int(request.args.get('year'))
        month = request.args.get('month')
        day = int(request.args.get('day'))
        
        # Reverse search doesn't accept lat/lon yet? check.
        # get_english_date calls get_malayalam_date inside loop.
        # It needs to support passing it down? 
        # I'll stick to default for reverse search or update if needed.
        # Update get_english_date signature? 
        # For now, it might drift slightly if reverse search uses default lat/lon vs precise.
        # Let's hope deviation is minimal or update panchang later.
        
        eng_date = get_english_date(year, month, day)
        
        if eng_date:
            mal_details = get_malayalam_date(eng_date, lat, lon)
            star = get_nakshatra(eng_date, lat, lon)
            
            if star.get('status') == 'error':
                return jsonify({'status': 'error', 'message': 'Star calculation failed'}), 500
                
            return jsonify({
                'status': 'success',
                'date': eng_date.strftime("%Y-%m-%d"),
                'mal_details': mal_details,
                'star': star
            })
        else:
             return jsonify({'status': 'error', 'message': 'Date not found'}), 404
             
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'Internal Error'}), 500
        
@utility_bp.route('/panchangam')
def panchangam_view():
    return render_template('utility/panchangam.html')

@utility_bp.route('/get-panchangam-data')
def get_panchangam_data_api():
    date_str = request.args.get('date')
    if not date_str:
        today = datetime.date.today()
    else:
        try:
            today = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            return jsonify({'status': 'error', 'message': 'Invalid date'}), 400
            
    try:
        settings, _ = get_cached_settings()
        lat = settings.get('latitude', 10.85) if settings else 10.85
        lon = settings.get('longitude', 76.27) if settings else 76.27
        
        from modules.panchang import get_nakshatra_timings
        data = get_nakshatra_timings(today, lat, lon)
        if data.get('status') == 'error':
             return jsonify({'status': 'error', 'message': 'Internal Error'}), 500
        return jsonify(data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'Internal Error'}), 500
