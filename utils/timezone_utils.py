"""
Timezone utilities for Indian Standard Time (IST)

This module provides centralized IST timezone handling for the entire application.
All datetime operations should use these utilities to ensure consistency.
"""

from datetime import datetime, timezone, timedelta
import logging

# IST is UTC+5:30
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    """
    Get current datetime in IST timezone.
    
    Returns:
        datetime: Current datetime with IST timezone
    """
    return datetime.now(IST)

def get_ist_timestamp():
    """
    Get current IST timestamp as string for database storage.
    
    Returns:
        str: Timestamp in 'YYYY-MM-DD HH:MM:SS' format
    """
    return now_ist().strftime('%Y-%m-%d %H:%M:%S')

def parse_db_timestamp(timestamp_str):
    """
    Parse a database timestamp string and return it as IST datetime.
    
    Args:
        timestamp_str (str): Timestamp string from database
        
    Returns:
        datetime: Parsed datetime with IST timezone
    """
    if not timestamp_str:
        return None
    
    try:
        # Handle various timestamp formats
        if 'T' in timestamp_str:
            # ISO format with T separator
            clean_ts = timestamp_str.split('.')[0]  # Remove microseconds
            dt_obj = datetime.strptime(clean_ts, '%Y-%m-%dT%H:%M:%S')
        else:
            # Standard format with space separator
            clean_ts = timestamp_str.split('.')[0]  # Remove microseconds
            dt_obj = datetime.strptime(clean_ts, '%Y-%m-%d %H:%M:%S')
        
        # Assume database timestamps are in IST and add timezone info
        return dt_obj.replace(tzinfo=IST)
    except Exception as e:
        logging.error(f"Error parsing timestamp '{timestamp_str}': {e}")
        return None

def format_ist_datetime(dt, format_str='%d-%m-%Y %H:%M'):
    """
    Format a datetime object to string in IST timezone.
    
    Args:
        dt (datetime): Datetime object to format
        format_str (str): strftime format string
        
    Returns:
        str: Formatted datetime string
    """
    if not dt:
        return ""
    
    # If datetime is naive, assume it's IST
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=IST)
    # If it has a different timezone, convert to IST
    elif dt.tzinfo != IST:
        dt = dt.astimezone(IST)
    
    return dt.strftime(format_str)
