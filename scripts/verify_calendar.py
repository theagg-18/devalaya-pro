import sys
import os
import requests
import datetime

# Add root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.panchang import get_malayalam_date, get_english_date

def verify_calendar():
    print("--- Verifying Calendar ---")
    
    # Test 1: Forward (Today)
    today = datetime.date.today()
    mal = get_malayalam_date(today)
    print(f"Today ({today}) -> {mal['mal_month']} {mal['day']}, {mal['mal_year']}")
    
    # Test 2: Known Date (Aug 17, 2024 roughly Chingam 1, 1200)
    # Note: 2024 is a leap year. 
    # Chingam 1 typically falls on Aug 17.
    test_date = datetime.date(2024, 8, 17)
    mal_known = get_malayalam_date(test_date)
    print(f"Test (2024-08-17) -> {mal_known['mal_month']} {mal_known['day']}, {mal_known['mal_year']}")
    
    # Test 3: Reverse
    # Let's try to reverse the result of Test 1
    rev_date = get_english_date(mal['mal_year'], mal['mal_month'], mal['day'])
    print(f"Reverse ({mal['mal_month']} {mal['day']}, {mal['mal_year']}) -> {rev_date}")
    
    if rev_date == today:
        print("[PASS] Reverse calculation exact match")
    else:
        print(f"[FAIL] Reverse mismatch (Expected {today})")

if __name__ == "__main__":
    verify_calendar()
