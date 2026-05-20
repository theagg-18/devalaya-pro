import logging
import datetime

from flask import Blueprint, jsonify, request, render_template

from modules.panchang import (
    get_next_star_dates, get_malayalam_date, get_english_date,
    MAL_MONTHS_ENG, get_nakshatra
)
from database import get_cached_settings

utility_bp = Blueprint('utility', __name__, url_prefix='/utility')


def _get_location():
    settings, _ = get_cached_settings()
    lat = settings.get('latitude', 10.85) if settings else 10.85
    lon = settings.get('longitude', 76.27) if settings else 76.27
    return lat, lon


@utility_bp.route('/calendar')
def calendar_view():
    return render_template('utility/calendar.html', mal_months=MAL_MONTHS_ENG)


@utility_bp.route('/get-star')
def get_star():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'status': 'error', 'message': 'Date is required'}), 400

    try:
        lat, lon = _get_location()
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
        logging.error(f"get_star error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal Error'}), 500


@utility_bp.route('/get-next-star-dates')
def get_next_star_dates_route():
    from modules.panchang import get_next_star_dates as gnsd
    star_name = request.args.get('star_name')
    start_date = request.args.get('start_date')

    if not star_name:
        return jsonify({'status': 'error', 'message': 'star_name is required'}), 400

    try:
        lat, lon = _get_location()
        s_date = datetime.date.today()
        if start_date:
            s_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()

        months = request.args.get('months')
        count = 100 if months else 5

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
        logging.error(f"get_next_star_dates error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal Error'}), 500


@utility_bp.route('/eng-to-mal')
def eng_to_mal():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'status': 'error', 'message': 'Date required'}), 400
    try:
        lat, lon = _get_location()
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        mal_date = get_malayalam_date(date_obj, lat, lon)
        return jsonify({'status': 'success', 'data': mal_date})
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid date format'}), 400
    except Exception as e:
        logging.error(f"eng_to_mal error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal Error'}), 500


@utility_bp.route('/mal-to-eng')
def mal_to_eng():
    try:
        lat, lon = _get_location()
        year = int(request.args.get('year'))
        month = request.args.get('month')
        day = int(request.args.get('day'))

        eng_date = get_english_date(year, month, day)

        if not eng_date:
            return jsonify({'status': 'error', 'message': 'Date not found'}), 404

        mal_details = get_malayalam_date(eng_date, lat, lon)
        star = get_nakshatra(eng_date, lat, lon)

        if star.get('status') == 'error':
            return jsonify({'status': 'error', 'message': 'Star calculation failed'}), 500

        return jsonify({
            'status': 'success',
            'date': eng_date.strftime("%Y-%m-%d"),
            'mal_details': mal_details,
            'star': {
                'nakshatra_eng': star.get('nakshatra_eng'),
                'nakshatra_mal': star.get('nakshatra_mal'),
            }
        })
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Invalid input'}), 400
    except Exception as e:
        logging.error(f"mal_to_eng error: {e}", exc_info=True)
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
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Invalid date'}), 400

    try:
        lat, lon = _get_location()
        from modules.panchang import get_nakshatra_timings
        data = get_nakshatra_timings(today, lat, lon)
        if data.get('status') == 'error':
            return jsonify({'status': 'error', 'message': 'Internal Error'}), 500
        return jsonify(data)
    except Exception as e:
        logging.error(f"get_panchangam_data error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal Error'}), 500
