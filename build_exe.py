import os
import sys
import shutil
import subprocess

def install_dependencies():
    print("Installing build dependencies...")
    try:
        # Install PyInstaller
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        # Install project requirements to ensure they are available for bundling
        if os.path.exists("requirements.txt"):
             subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except subprocess.CalledProcessError as e:
        print(f"[-] Failed to install dependencies: {e}")
        sys.exit(1)

def build():
    try:
        import PyInstaller
    except ImportError:
        install_dependencies()
        
    # Double check requirements are actually installed (in case PyInstaller was already there but others weren't)
    if os.path.exists("requirements.txt"):
         print("[*] Verifying dependencies...")
         try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
         except:
             pass

    # Clean previous builds
    print("[*] Cleaning previous build artifacts...")
    if os.path.exists('build'): shutil.rmtree('build')
    if os.path.exists('dist'): shutil.rmtree('dist')
    if os.path.exists('DevalayaBilling.spec'): os.remove('DevalayaBilling.spec')
    
    # Path separator
    sep = ';' if os.name == 'nt' else ':'
    
    # Data files to include
    # Format: source_path + sep + dest_path
    datas = [
        f'static{sep}static',
        f'templates{sep}templates',
        f'data{sep}data',
        f'version.py{sep}.',
        # .env is deliberately NOT included so user can configure it externally.
        # If included, it would be frozen.
    ]
    
    # Hidden imports - modules that PyInstaller's analysis might miss
    hidden = [
        'waitress',
        'engineio.async_drivers.threading', 
        'engineio.async_drivers.eventlet', 
        'eventlet',
        'dns', 
        'socket',
        'logging',
        'uuid',
        'json',
        'sqlite3',
        'routes',
        'modules',
        'zeroconf',
        'ifaddr'
    ]
    
    cmd = [
        '--name=DevalayaBilling',
        '--onefile',       # Create a single executable file
        '--clean',         # Clean cache
        '--log-level=INFO',
    ]
    
    # Add icon if exists
    icon_path = os.path.join('static', 'favicon.ico')
    if os.path.exists(icon_path):
        cmd.append(f'--icon={icon_path}')
    else:
        print("[!] Warning: static/favicon.ico not found. Using default icon.")
    
    # Add datas
    for d in datas:
        cmd.extend(['--add-data', d])
        
    # Add hidden imports
    for h in hidden:
        cmd.extend(['--hidden-import', h])
        
    # Script to run
    cmd.append('launcher.py')
    
    print("[*] Starting Build Process (this may take a few minutes)...")
    
    # Run PyInstaller via python -m PyInstaller
    cmd_full = [sys.executable, '-m', 'PyInstaller'] + cmd
    
    try:
        subprocess.check_call(cmd_full)
        
        exe_path = os.path.abspath(os.path.join('dist', 'DevalayaBilling.exe' if os.name == 'nt' else 'DevalayaBilling'))
        
        print("\n" + "="*50)
        print("   BUILD SUCCESSFUL")
        print("="*50)
        print(f"[+] Executable created at:\n    {exe_path}")
        print("-" * 50)
        print("IMPORTANT DEPLOYMENT INSTRUCTIONS:")
        print("1. Copy the .exe to your desired folder.")
        print("2. IMPORTANT: The 'backups' folder and 'temple.db' will be created next to the .exe.")
        print("   If you have existing data, copy your 'temple.db' to the same folder as the .exe.")
        print("3. Optional: If you use a custom .env file, copy it next to the .exe.")
        print("="*50)
        
    except subprocess.CalledProcessError:
        print("\n[-] Build Failed.")

if __name__ == '__main__':
    build()
