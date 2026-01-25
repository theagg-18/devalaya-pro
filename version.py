"""
Devalaya Pro - Temple Billing System
Version Configuration
"""

__version__ = "1.6.2"
__version_info__ = {
    "major": 1,
    "minor": 6,
    "patch": 2,
    "release": "stable"
}

# Version History
VERSION_HISTORY = [
    {
        "version": "1.6.2",
        "date": "2026-01-25",
        "changes": [
            "Security Fix: Remediated 'Information exposure through an exception' vulnerability in utility routes",
            "Enhancement: Improved error handling sanitization for Panchangam API"
        ]
    },
    {
        "version": "1.6.1",
        "date": "2026-01-25",
        "changes": [
            "Feature: Built-in Malayalam Calendar & Star Calculation (Skyfield)",
            "Feature: Panchangam Utility Page & Calendar Converter",
            "Critical Fix: Syntax error in admin routes (admin.py)",
            "Chore: Removed unused documentation files"
        ]
    },
    {
        "version": "1.6.0",
        "date": "2026-01-22",
        "changes": [
            "Feature: Built-in Malayalam Calendar & Offline Star Calculation",
            "Feature: Star Finder & One-Click Yearly Replication",
            "Enhancement: Total Amount display in Print Overlay",
            "Enhancement: 'Clear All' button for batch billing",
            "Security: Fixed 'Pay Later' loophole ensuring immediate payment status confirmation",
            "Enhancement: Persistent billing overlay survives page refreshes"
        ]
    },
    {
        "version": "1.5.9",
        "date": "2026-01-21",
        "changes": [
            "Critical Fix: Resolved 'ModuleNotFoundError: No module named wsgi' in portable environments",
            "Fix: Explicitly configured static and template paths in app.py for reliable asset loading",
            "Build: Optimized portable distribution by excluding temporary and backup files"
        ]
    },
    {
        "version": "1.5.8",
        "date": "2026-01-21",
        "changes": [
            "Feature: Added 'Portable Distribution' builder (Zero-Install)",
            "Fix: build_portable.py correctly configures embedded python"
        ]
    },
    {
        "version": "1.5.7",
        "date": "2026-01-21",
        "changes": [
            "Feature: Added Offline Installation Support (Local packages/ folder)",
            "Enhancement: run_prod.py and manager.py now prefer local packages if present"
        ]
    },
    {
        "version": "1.5.6",
        "date": "2026-01-21",
        "changes": [
            "Hotfix: Fixed infinite install loop in Manager when shortcut dependencies fail to import"
        ]
    },
    {
        "version": "1.5.5",
        "date": "2026-01-21",
        "changes": [
            "Critical Fix: Resolved file corruption during Admin Update on Windows",
            "Critical Fix: Manager.py now auto-restarts server after update",
            "Enhancement: Server auto-installs all dependencies if missing (Flask, etc.)"
        ]
    },
    {
        "version": "1.5.4",
        "date": "2026-01-21",
        "changes": [
            "Hotfix: Resolved 'psutil' missing dependency crash in Manager",
            "Server: Added error trap to 'run_prod.py' to keep window open on startup failure",
            "System: Verified portability and fallback mechanisms for source distribution"
        ]
    },
    {
        "version": "1.5.3",
        "date": "2026-01-21",
        "changes": [
            "Hotfix: Resolved PermissionError on logs/error.log during update"
        ]
    },
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
