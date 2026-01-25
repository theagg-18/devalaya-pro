import os
import sys
import webbrowser
import threading
import socket
import logging
from time import sleep
from waitress import serve

# Configure logging before importing app
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

try:
    from app import app
except ImportError as e:
    # If running from source but issues with path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from app import app

def get_best_ip():
    """
    Attempt to find the most likely LAN IP address.
    """
    ip = None
    try:
        # Method 1: Connect to a public DNS (doesn't send packets)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    if not ip or ip.startswith('127.'):
        # Method 2: Hostname resolution (Fallback)
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except:
            pass

    return ip or '127.0.0.1'

def open_browser(url):
    """Open the browser after a short delay."""
    try:
        print(f"[*] Opening browser: {url}")
        webbrowser.open(url)
    except Exception as e:
        print(f"[-] Failed to open browser: {e}")

def main():
    # Set console title
    if os.name == 'nt':
        os.system('title Devalaya Billing System Server')

    local_ip = get_best_ip()
    hostname = socket.gethostname()
    port = 5000
    host = '0.0.0.0'
    
    local_url = f"http://localhost:{port}"
    network_url_ip = f"http://{local_ip}:{port}"
    
    print("\n" + "="*60)
    print("   DEVALAYA BILLING SYSTEM - SERVER RUNNING")
    print("="*60)
    print(f" Status:  ONLINE")
    print(f" Port:    {port}")
    print(f" Network: Connected ({local_ip})")
    print("-" * 60)
    
    # Register mDNS
    zeroconf = None
    service_info = None
    
    try:
        from zeroconf import ServiceInfo, Zeroconf
        
        # Ensure we have a valid IP for mDNS
        if local_ip != '127.0.0.1':
            desc = {'version': '1.0.0'}
            
            # Service Name needs to be unique-ish if possible, but fixed for now
            # Format: _service._proto.local.
            service_type = "_http._tcp.local."
            service_name = "Devalaya Pro._http._tcp.local." 
            
            service_info = ServiceInfo(
                service_type,
                service_name,
                addresses=[socket.inet_aton(local_ip)],
                port=port,
                properties=desc,
                server="devalaya-pro.local.", 
            )

            zeroconf = Zeroconf()
            zeroconf.register_service(service_info)
            mdns_status = "ACTIVE"
            mdns_url = f"http://devalaya-pro.local:{port}"
        else:
            mdns_status = "SKIPPED (No LAN IP)"
            mdns_url = "N/A"
            
    except ImportError:
        mdns_status = "FAILED (Missing Dependency)"
    except Exception as e:
        mdns_status = f"ERROR: {e}"

    print(" ACCESS INSTRUCTIONS:")
    print(f" 1. On this PC:      {local_url}")
    print(f" 2. Other Devices:   {network_url_ip}")
    
    if "ACTIVE" in mdns_status:
        print(f"    OR Domain:       http://devalaya-pro.local:{port}")
    else:
        print(f"    (Domain feature unavailable: {mdns_status})")
    print("-" * 60)
    print(" [!] KEEP THIS WINDOW OPEN to keep the system running.")
    print(" [!] Close this window to SHUT DOWN the system.")
    print("="*60 + "\n")
    
    # Schedule browser launch
    threading.Timer(2.0, open_browser, args=[local_url]).start()
    
    # Start Server (Blocking)
    try:
        serve(app, host=host, port=port, threads=6)
    except OSError as e:
        print(f"\n[-] PORT ERROR: {e}")
        print(f"    Port {port} might be in use. Is the server already running?")
    except Exception as e:
        print(f"\n[-] CRITICAL SERVER ERROR: {e}")
    finally:
        if zeroconf and service_info:
            try:
                zeroconf.unregister_service(service_info)
                zeroconf.close()
            except:
                pass
        
        # Only pause on exit if we want to debug
        print("\n[!] Server stopped.")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
