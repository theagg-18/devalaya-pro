# Devalaya Pro v1.6.1 Release Notes

**Release Date:** January 25, 2026
**Version:** 1.6.1

## New Features
- **Malayalam Star (Nakshatra) Calculation**: Added backend support to automatically calculate the Malayalam Star for any given date.
    - Utilizes **Skyfield** for high-precision astronomical calculations.
    - Implements **Sunrise Rule** (Star present at 6:00 AM IST) and **Lahiri Ayanamsa** for accurate Vedic astrology compliance.
    - Operates fully offline with local ephemeris data (`de421.bsp`).
- **Panchangam Utility Page**: Added a dedicated standalone page (`/utility/panchangam`) for detailed daily star calculations and future date lookups.
- **Calendar Converter Utility**: Added a tool (`/utility/calendar`) to convert dates between **English (Gregorian)** and **Malayalam (Kolla Varsham)** calendars, including Star calculation for both.

## Critical Fixes
- **Admin Panel Crash:** Fixed a critical SyntaxError in `routes/admin.py` (duplicate `try` block) that could cause the admin dashboard to fail.

## Installation
1. Download `DevalayaBillingSetup_v1.6.1.exe`.
2. Run the installer. It will automatically update your existing installation while preserving your data (`temple.db`).
