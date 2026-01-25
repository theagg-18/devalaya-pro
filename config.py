import os
import sys
from dotenv import load_dotenv

load_dotenv()

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

base_path = get_base_path()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-secret-key'
    # Default to local file if not specified
    DB_PATH = os.environ.get('DB_PATH') or os.path.join(base_path, 'temple.db')
    BACKUP_PATH = os.environ.get('BACKUP_PATH') or os.path.join(base_path, 'backups')
