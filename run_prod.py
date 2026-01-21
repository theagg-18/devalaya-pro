import os
import platform
import subprocess
import sys
import socket

def get_local_ip():
    try:
        # Connect to an external server to get the interface IP (doesn't send data)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

def start_production():
    system = platform.system()
    ip = get_local_ip()
    
    print("="*50)
    print(f"Starting Devalaya Pro in Production Mode ({system})")
    print(f"Server is running at:")
    print(f" * Local:   http://localhost:5000")
    print(f" * Network: http://{ip}:5000")
    print("="*50)

    if system == "Windows":
        try:
            from waitress import serve
            from wsgi import app
            print("Running with Waitress...")
            serve(app, host='0.0.0.0', port=5000)
        except ImportError:
            print("Waitress not found. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "waitress"])
            from waitress import serve
            from wsgi import app
            serve(app, host='0.0.0.0', port=5000)
    else:
        print("Running with Gunicorn...")
        # For Linux/RPi, we use the config file we created
        subprocess.run(["gunicorn", "-c", "gunicorn_config.py", "wsgi:app"])

if __name__ == "__main__":
    try:
        start_production()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("\n[!] Server failed to start.")
        try:
            input("Press Enter to exit...")
        except EOFError:
            pass
