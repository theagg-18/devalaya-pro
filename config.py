import os
import sys
import secrets
import warnings
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

base_path = get_base_path()

_env_secret = os.environ.get('SECRET_KEY')
if not _env_secret:
    warnings.warn(
        "SECRET_KEY not set in environment. Using a random key — sessions will be "
        "invalidated on every restart. Set SECRET_KEY in your .env file for production.",
        RuntimeWarning, stacklevel=2
    )
    _env_secret = secrets.token_hex(32)

class Config:
    SECRET_KEY = _env_secret
    DB_PATH = os.environ.get('DB_PATH') or os.path.join(base_path, 'temple.db')
    BACKUP_PATH = os.environ.get('BACKUP_PATH') or os.path.join(base_path, 'backups')
    WTF_CSRF_HEADERS = ['X-CSRFToken']
    WTF_CSRF_TIME_LIMIT = 3600
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
