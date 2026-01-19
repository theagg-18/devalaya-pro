import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-secret-key'
    # Default to local file if not specified
    DB_PATH = os.environ.get('DB_PATH') or 'temple.db'
    BACKUP_PATH = os.environ.get('BACKUP_PATH') or 'backups'
