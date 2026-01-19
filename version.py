"""
Devalaya Pro - Temple Billing System
Version Configuration
"""

__version__ = "1.1.0"
__version_info__ = {
    "major": 1,
    "minor": 1,
    "patch": 0,
    "release": "stable"
}

# Version History
VERSION_HISTORY = [
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
