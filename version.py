"""
Devalaya Pro - Temple Billing System
Version Configuration
"""

__version__ = "1.5.2"
__version_info__ = {
    "major": 1,
    "minor": 5,
    "patch": 2,
    "release": "stable"
}

# Version History
VERSION_HISTORY = [
    {
        "version": "1.5.2",
        "date": "2026-01-21",
        "changes": [
            "Manager Script: Added fallback to GitHub Tags API (Fixes 404 errors)",
            "Manager Script: Configured User-Agent headers for reliable API access",
            "Admin Panel: Integrated robust non-Git update logic matching Manager script",
            "Release Automation: Added publish_release.py script"
        ]
    },
    {
        "version": "1.5.1",
        "date": "2026-01-21",
        "changes": [
            "Critical Fix: Resolved PermissionError during update on Windows (.venv locking)",
            "Fixed update loop due to version mismatch"
        ]
    },
    {
        "version": "1.5.0",
        "date": "2026-01-20",
        "changes": [
            "Bill Cancellation and Editing features",
            "Enhanced History and Billing UI",
            "Added Cancelled Bill alerts and styling"
        ]
    },
    {
        "version": "1.4.2",
        "date": "2026-01-20",
        "changes": [
            "Theme CSS Fix: Resolved syntax error in theme_css.html",
            "Server Improvements: Enhanced auto-reload configuration and startup scripts"
        ]
    },
    {
        "version": "1.4.1",
        "date": "2026-01-20",
        "changes": [
            "Security Fix: Remediated information exposure in exception handling (admin/cashier/updater)",
            "Detailed server-side logging for errors",
            "Sanitized API error responses"
        ]
    },
    {
        "version": "1.4.0",
        "date": "2026-01-20",
        "changes": [
            "Concurrent Billing Safety: Added retry mechanism to prevent bill number collisions",
            "Bulk Upload: Admin can now upload Item/Vazhipadu CSV with UPSERT support",
            "Pagination: Implemented 10-item limit for Cashier History and Admin Reports",
            "Reports Enhancement: Added Date Range filtering and accurate global totals",
            "Backup Manager: Made the usage note permanent (no auto-dismiss)",
            "CSV Export: Fixed export to respect date ranges and added date timestamps to filename"
        ]
    },
    {
        "version": "1.3.1",
        "date": "2026-01-19",
        "changes": [
            "Test Update: Verified auto-update functionality",
            "Minor stability improvements"
        ]
    },
    {
        "version": "1.3.0",
        "date": "2026-01-19",
        "changes": [
            "Implemented Safe Update System with Auto-Rollback",
            "Added Maintenance Mode locking mechanism",
            "Added /health endpoint for system status checks",
            "New Admin Update Dashboard (Online & Offline support)",
            "Integrated GitHub API for update checking"
        ]
    },
    {
        "version": "1.2.0",
        "date": "2026-01-19",
        "changes": [
            "Custom Logo upload feature with privacy protection",
            "CSV export now includes item details for each bill",
            "Fixed CSV encoding issue for Malayalam characters (UTF-8 BOM)",
            "Added uploads directory to .gitignore for user privacy",
            "Fixed missing route decorator in admin backups"
        ]
    },
    {
        "version": "1.1.0",
        "date": "2026-01-19",
        "changes": [
            "New Theme Engine with Custom Theme Builder",
            "Added 3 new preset themes: Forest, Ocean, and Sunset",
            "Dynamic hover and shadow colors based on active theme",
            "Added 'from_json' template filter for settings JSON parsing",
            "Database migration for custom theme storage",
            "Improved visual consistency across admin interactions"
        ]
    },
    {
        "version": "1.0.0",
        "date": "2026-01-19",
        "changes": [
            "Initial stable release",
            "Kerala temple theme with Kumkum and Chandan colors",
            "IST timezone support (UTC+5:30)",
            "Unified billing system for Vazhipadu and Donations",
            "Dual reprint options (thermal printer and web browser)",
            "Cart date initialization fix",
            "Temple deity logo integration",
            "Malayalam language support",
            "Batch printing with grouping options",
            "Draft save and resume functionality",
            "Bill replication for multiple dates",
            "Comprehensive admin dashboard with analytics"
        ]
    }
]

def get_version():
    """Get the current version string"""
    return __version__

def get_version_info():
    """Get detailed version information"""
    return __version_info__

def get_version_display():
    """Get formatted version for display"""
    return f"Devalaya Pro v{__version__}"
