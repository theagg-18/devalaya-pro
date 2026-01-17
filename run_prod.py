import os
import platform
import subprocess
import sys

def start_production():
    system = platform.system()
    print(f"Detected System: {system}")
    print("Starting Devalaya Pro in Production Mode...")

    if system == "Windows":
        try:
            from waitress import serve
            from wsgi import app
            print("Running with Waitress (Windows Production Server)...")
            print("Access at http://localhost:5000")
            serve(app, host='0.0.0.0', port=5000)
        except ImportError:
            print("Waitress not found. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "waitress"])
            from waitress import serve
            from wsgi import app
            serve(app, host='0.0.0.0', port=5000)
    else:
        print("Running with Gunicorn (Linux Production Server)...")
        # For Linux/RPi, we use the config file we created
        subprocess.run(["gunicorn", "-c", "gunicorn_config.py", "wsgi:app"])

if __name__ == "__main__":
    start_production()
