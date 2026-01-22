import math
from datetime import datetime, timedelta

# --- CONSTANTS ---

STARS = [
    {"id": 0, "mal": "അശ്വതി", "eng": "Aswathi"},
    {"id": 1, "mal": "ഭരണി", "eng": "Bharani"},
    {"id": 2, "mal": "കാർത്തിക", "eng": "Karthika"},
    {"id": 3, "mal": "രോഹിണി", "eng": "Rohini"},
    {"id": 4, "mal": "മകയിരം", "eng": "Makayiram"},
    {"id": 5, "mal": "തിരുവാതിര", "eng": "Thiruvathira"},
    {"id": 6, "mal": "പുണർതം", "eng": "Punartham"},
    {"id": 7, "mal": "പൂയം", "eng": "Pooyam"},
    {"id": 8, "mal": "ആയില്യം", "eng": "Ayilyam"},
    {"id": 9, "mal": "മകം", "eng": "Makam"},
    {"id": 10, "mal": "പൂരം", "eng": "Pooram"},
    {"id": 11, "mal": "ഉത്രം", "eng": "Uthram"},
    {"id": 12, "mal": "അത്തം", "eng": "Atham"},
    {"id": 13, "mal": "ചിത്തിര", "eng": "Chithira"},
    {"id": 14, "mal": "ചോതി", "eng": "Chothi"},
    {"id": 15, "mal": "വിശാഖം", "eng": "Vishakham"},
    {"id": 16, "mal": "അനിഴം", "eng": "Anizham"},
    {"id": 17, "mal": "തൃക്കേട്ട", "eng": "Thrikketta"},
    {"id": 18, "mal": "മൂലം", "eng": "Moolam"},
    {"id": 19, "mal": "പൂരാടം", "eng": "Pooradam"},
    {"id": 20, "mal": "ഉത്രാടം", "eng": "Uthradam"},
    {"id": 21, "mal": "തിരുവോണം", "eng": "Thiruvonam"},
    {"id": 22, "mal": "അവിട്ടം", "eng": "Avittam"},
    {"id": 23, "mal": "ചതയം", "eng": "Chathayam"},
    {"id": 24, "mal": "പൂരുരുട്ടാതി", "eng": "Pooruruttathi"},
    {"id": 25, "mal": "ഉത്രട്ടാതി", "eng": "Uthrattathi"},
    {"id": 26, "mal": "രേവതി", "eng": "Revathi"}
]

MAL_MONTHS = [
    {"id": 1, "mal": "ചിത്തിര", "eng": "Chingam"}, # Wait, id 1 is Medam traditionally in Zodiac, but Kollam starts Chingam
    # Let's use Zodiac Index 0 = Medam
    {"id": 0, "mal": "മേടം", "eng": "Medam"},
    {"id": 1, "mal": "ഇടവം", "eng": "Edavam"},
    {"id": 2, "mal": "മിഥുനം", "eng": "Midhunam"},
    {"id": 3, "mal": "കർക്കിടകം", "eng": "Karkidakam"},
    {"id": 4, "mal": "ചിങ്ങം", "eng": "Chingam"},
    {"id": 5, "mal": "കന്നി", "eng": "Kanni"},
    {"id": 6, "mal": "തുലാം", "eng": "Thulam"},
    {"id": 7, "mal": "വൃശ്ചികം", "eng": "Vrischikam"},
    {"id": 8, "mal": "ധനു", "eng": "Dhanu"},
    {"id": 9, "mal": "മകരം", "eng": "Makaram"},
    {"id": 10, "mal": "കുംഭം", "eng": "Kumbham"},
    {"id": 11, "mal": "മീനം", "eng": "Meenam"}
]

# --- ASTRONOMICAL CALCULATIONS (Pure Python) ---

def to_julian(date_obj):
    """Convert datetime to Julian Day."""
    # Algorithm from Meeus
    Y = date_obj.year
    M = date_obj.month
    D = date_obj.day
    
    # Adjust for Time (assume Noon 12:00 UTC for "Day's Star" checking, 
    # or use actual time if provided. For now standardizing to Noon IST -> 06:30 UTC)
    # Actually, Star of the Day is usually defined by Sunrise star. 
    # Sunrise ~ 6 AM IST -> 00:30 UTC.
    H = 6 # 6 AM IST specific for "Star of the Day"
    M_time = 0
    
    # Convert time to day fraction
    day_frac = (H + (M_time / 60.0)) / 24.0
    D = D + day_frac

    if M <= 2:
        Y -= 1
        M += 12

    A = math.floor(Y / 100)
    B = 2 - A + math.floor(A / 4)
    
    JD = math.floor(365.25 * (Y + 4716)) + math.floor(30.6001 * (M + 1)) + D + B - 1524.5
    return JD

def normalize_deg(deg):
    """Normalize angle to 0-360 degrees."""
    deg = deg % 360
    if deg < 0: deg += 360
    return deg

def get_moon_longitude(jd):
    """Calculate Moon's Geocentric Ecliptic Longitude (Tropical)."""
    # Meeus simplified model
    T = (jd - 2451545.0) / 36525.0

    # Mean elements
    L_prime = 218.3164191 + 481267.88134236 * T
    D = 297.8501921 + 445267.1114034 * T
    M = 134.9633964 + 477198.8675055 * T
    M_prime = 357.5291092 + 35999.0502909 * T
    F = 93.2720950 + 483202.0175233 * T

    # Convert to radians
    def rad(d): return math.radians(normalize_deg(d))
    
    L_r = rad(L_prime)
    D_r = rad(D)
    M_r = rad(M)
    Mp_r = rad(M_prime)
    F_r = rad(F)

    # Major Periodic Terms (The sum of these corrections gives the true longitude)
    # Coeffs from Meeus (Chapter 47) - Truncated to major terms for ~0.1 deg accuracy
    
    # Sigma l
    c_l = 0
    c_l += 6.288774 * math.sin(M_r)
    c_l += 1.274027 * math.sin(2*D_r - M_r)
    c_l += 0.658314 * math.sin(2*D_r)
    c_l += 0.213618 * math.sin(2*M_r)
    c_l -= 0.185116 * math.sin(Mp_r)
    c_l -= 0.114332 * math.sin(2*F_r)
    c_l += 0.058793 * math.sin(2*D_r - 2*M_r)
    c_l += 0.057066 * math.sin(2*D_r - M_r - Mp_r)
    c_l += 0.053322 * math.sin(2*D_r + M_r)
    c_l += 0.045758 * math.sin(2*D_r - Mp_r)
    
    curr_long = L_prime + c_l
    return normalize_deg(curr_long)

def get_sun_longitude(jd):
    """Calculate Sun's Geocentric Ecliptic Longitude (Tropical)."""
    # Meeus simplified
    T = (jd - 2451545.0) / 36525.0
    
    # Geometric Mean Longitude
    L0 = 280.46646 + 36000.76983 * T
    # Mean Anomaly
    M = 357.52911 + 35999.05029 * T
    
    M_rad = math.radians(normalize_deg(M))
    
    # Equation of Center
    C = (1.914602 - 0.004817 * T - 0.000014 * T**2) * math.sin(M_rad)
    C += (0.019993 - 0.000101 * T) * math.sin(2 * M_rad)
    C += 0.000289 * math.sin(3 * M_rad)
    
    true_long = L0 + C
    return normalize_deg(true_long)

def get_ayanamsa(jd):
    """Calculate Lahiri Ayanamsa."""
    # Approx t = (JD - 2451545) / 36525
    # Ayanamsa ~ 23.85 + 0.0139 * t (Linear approx valid for 1900-2100)
    # A simplified formulae often used:
    t = (jd - 2451545.0) / 36525.0
    ayanamsa = 23.8561 + 0.0139 * t # Approx for year 2000 base
    # Refined Lahiri: 23deg 51' 25.532" at J2000 (23.857) + precession
    
    # Let's use a slightly better fit for 2000-2050
    # Lahiri value at 2000 is ~23.86 deg
    # Rate is roughly 50.27 arcsec per year = 0.01396 deg/year
    
    return 23.857 + 1.396 * t # Wait, 50 arcsec/yr * 100 yr = 5000 arcsec = 1.39 deg/century
    # So the formula 23.85 + 1.396 * T seems correct.
    

def get_nakshatra_for_date(date_obj):
    """
    Returns the Nakshatra for a given date object (YYYY-MM-DD).
    Calculated at 6 AM IST (approx Sunrise) to determine 'Star of the Day'.
    """
    jd = to_julian(date_obj)
    
    moon_trop = get_moon_longitude(jd)
    ayanamsa = get_ayanamsa(jd)
    
    moon_sid = normalize_deg(moon_trop - ayanamsa)
    
    # 27 Nakshatras -> 360 / 27 = 13.3333 degrees each
    nak_index = math.floor(moon_sid / 13.3333333333)
    
    # Safety Check
    if nak_index < 0: nak_index = 0
    if nak_index > 26: nak_index = 26
    
    return STARS[int(nak_index)]

def get_malayalam_date(date_obj):
    """
    Returns Malayalam Date dictionary {year, month_name, day}.
    Approximation based on Sun Longitude.
    """
    # Calculate for Noon to check Solar Rashi
    jd = to_julian(date_obj.replace(hour=12))
    
    sun_trop = get_sun_longitude(jd)
    ayanamsa = get_ayanamsa(jd)
    sun_sid = normalize_deg(sun_trop - ayanamsa)
    
    # Rashi Index (0 = Medam, 1 = Edavam...)
    rashi_index = int(math.floor(sun_sid / 30.0))
    if rashi_index < 0: rashi_index = 0
    if rashi_index > 11: rashi_index = 11
    
    month_data = MAL_MONTHS[rashi_index]
    
    # Calculate Day of Month
    # We iterate backwards to find when Rashi changed
    # Max days in month is ~32. 
    curr_jd = jd
    day_count = 1
    
    # Safety break
    for _ in range(35):
        curr_jd -= 1.0 
        # Check sun long at this past date
        s_long = normalize_deg(get_sun_longitude(curr_jd) - get_ayanamsa(curr_jd))
        prev_rashi = int(math.floor(s_long / 30.0))
        
        if prev_rashi != rashi_index:
            # Transit happened between curr_jd and curr_jd + 1
            # Usually day_count is current gap.
            # Example: If today is 1st, yesterday was prev rashi. count = 1.
            break
        day_count += 1
        
    # Calculate Year (Kollam Era)
    # Starts in Chingam (Index 4, Leo).
    # New Year usually Aug 17.
    # Current Gregorian Year - 825.
    # If before Chingam 1 (i.e. Month Index < 4): Year - 826?
    # Wait.
    # Aug 2024 = 1200 ME.
    # Jan 2025 = 1200 ME. (Month Index 9 Makaram)
    # Apr 2025 = 1200 ME. (Month Index 0 Medam)
    # Aug 2025 = 1201 ME. (Month Index 4 Chingam starts)
    # So if Rashi >= 4 (Leo/Chingam) and <= 11: Year = Greg - 824?
    # Let's test:
    # Aug 2024 (Chingam): 2024 - 824 = 1200. Correct.
    # Jan 2025 (Makaram): 2025 - 825 = 1200. Correct.
    # Apr 2025 (Medam, Index 0): 2025 - 825 = 1200. Correct.
    # So logic:
    # If rashi_index >= 4 (Chingam to Meenam? No, Chingam is start).
    # Sequence: Chingam(4), Kanni(5)... Meenam(11), Medam(0)... Karkidakam(3).
    # So if index is 4,5,6,7,8,9,10,11: It is early part of ME year.
    # If index is 0,1,2,3: It is late part of ME year.
    
    me_year = 0
    if 4 <= rashi_index <= 11:
        # Aug - Dec usually
        me_year = date_obj.year - 824
    else:
        # Jan - Aug (Medam to Karkidakam or Makaram etc)
        # Wait, Makaram is index 9 (Jan). 
        # Jan is Makaram (9).
        # Apr is Medam (0).
        # So Jan (9) is part of previous year cycle started in Aug.
        # So 2025 Jan (Makaram) is 1200. 2025 - 825 = 1200.
        # But Aug 2024 (Chingam 4) is 1200. 2024 - 824 = 1200.
        # So:
        # If we are in Jan-Dec Gregorian:
        # Month indices map to months.
        # But the split happens at Chingam 1.
        
        # Actually simpler:
        # If Current Date is AFTER Chingam 1 (Aug 16/17): Year - 824.
        # If Current Date is BEFORE Chingam 1: Year - 825.
        
        # But we need to know the *exact* Chingam 1 date.
        # Using Rashi index is safer. 
        # If rashi_index == 4 (Chingam): We are in new year.
        # If rashi_index == 3 (Karkidakam): We are in old year.
        
        # Example: 15 Aug 2024. Sun in Karkidakam (3). Year = 2024 - 825 = 1199.
        # 20 Aug 2024. Sun in Chingam (4). Year = 2024 - 824 = 1200.
        # Jan 2025. Sun in Makaram (9). Year = 2025 - 825 = 1200.
        # May 2025. Sun in Medam (0). Year = 2025 - 825 = 1200.
        
        # So:
        # If month index >= 4 (Chingam to Meenam?? No Meenam is 11).
        # WAIT. Month indices:
        # 0 Medam (Apr)
        # 1 Edavam (May)
        # 2 Midhunam (Jun)
        # 3 Karkidakam (Jul/Aug) -> Ends year
        # 4 Chingam (Aug/Sep) -> Starts year
        # ...
        # 9 Makaram (Jan/Feb)
        # 11 Meenam (Mar/Apr)
        
        pass
    
    
    # If 0 <= rashi_index <= 3 (Apr - Aug): ME Year = GregYear - 825.
    # If 4 <= rashi_index <= 8 (Aug - Dec): ME Year = GregYear - 824.
    # If 9 <= rashi_index <= 11 (Jan - Apr): ME Year = GregYear - 825.
    
    if 4 <= rashi_index <= 8:
        me_year = date_obj.year - 824
    else:
        me_year = date_obj.year - 825
        
    return {
        "mal_year": me_year,
        "mal_month": month_data['mal'],
        "month_eng": month_data['eng'],
        "day": day_count
    }

def get_next_occurrences(star_eng, start_date=None, limit=5, months=None):
    """
    Finds the next dates where the given star occurs.
    If 'months' is specified, searches for that many months (approx 30*months days).
    Otherwise returns up to 'limit' occurrences.
    """
    if not start_date:
        start_date = datetime.now()
        
    found_dates = []
    
    # Determine search duration
    search_days = 150 # Default limit fallback
    if months:
        search_days = int(months) * 32 # Cover enough days
        limit = 999 # effectively no limit on count, just time
        
    current_date = start_date
    count = 0
    
    for _ in range(search_days):
        star = get_nakshatra_for_date(current_date)
        
        # Check matching (Case insensitive)
        if star['eng'].lower() == star_eng.lower():
            mal_date = get_malayalam_date(current_date)
            found_dates.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'star': star,
                'mal_date': f"{mal_date['day']} {mal_date['mal_month']} {mal_date['mal_year']}"
            })
            count += 1
            if count >= limit:
                break
                
        current_date += timedelta(days=1)
        
    return found_dates
