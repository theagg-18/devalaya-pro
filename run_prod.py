import os
import platform
import subprocess
import sys
import socket

# Ensure the script's directory is in sys.path.
# This is required for embedded Python distributions which might not add the CWD/Script dir by default.
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

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
            print("Missing dependencies detected (Waitress/Flask etc). Installing...")
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                packages_dir = os.path.join(base_dir, "packages")
                
                cmd = [sys.executable, "-m", "pip", "install"]
                if os.path.exists(packages_dir) and os.listdir(packages_dir):
                    print(f"[*] Local packages found. Installing offline...")
                    cmd.extend(["--no-index", "--find-links", packages_dir])
                
                cmd.extend(["-r", "requirements.txt"])
                
                subprocess.run(cmd, check=True)
                print("[+] Dependencies installed. Retrying...")
                from waitress import serve
                from wsgi import app
                serve(app, host='0.0.0.0', port=5000)
            except subprocess.CalledProcessError:
                print("[-] Failed to install dependencies.")
                raise
            except ImportError:
                print("[-] Dependencies installed but import failed. Please restart the application.")
                raise
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
