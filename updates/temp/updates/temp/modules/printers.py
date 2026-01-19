import platform
import subprocess
import os

class PrinterManager:
    def __init__(self):
        self.system = platform.system()
        self.is_linux = self.system == 'Linux'

    def get_system_printers(self):
        """
        Returns list of system printer names using lpstat on Linux,
        or mock list on Windows.
        """
        if self.is_linux:
            try:
                # Run lpstat -a to get list of printers
                result = subprocess.run(['lpstat', '-a'], capture_output=True, text=True)
                printers = []
                for line in result.stdout.splitlines():
                    # Output format: "PrinterName accepting requests since..."
                    if line:
                        printers.append(line.split()[0])
                return printers
            except Exception as e:
                print(f"Error getting printers: {e}")
                return []
        else:
            # Mock for Windows Dev
            return ["Thermal_Receipt_1", "Main_Office_Printer", "Counter_2_Printer"]

    def print_text(self, printer_name, text):
        """
        Sends raw text content to the printer.
        """
        if self.is_linux:
            try:
                # Use lp command to print
                # Create a temporary file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w+', delete=False) as fp:
                    fp.write(text)
                    fp.close()
                    # Print using lp
                    subprocess.run(['lp', '-d', printer_name, fp.name], check=True)
                    os.unlink(fp.name)
                return True, "Printed successfully"
            except subprocess.CalledProcessError as e:
                return False, f"Printing failed: {e}"
        else:
            print(f"--- MOCK PRINTING TO {printer_name} ---\n{text}\n----------------------------------")
            return True, "Mock print success"

    def get_printer_status(self, printer_name):
        """
        Checks if printer is reachable/idle.
        """
        if self.is_linux:
            # Simple check using lpstat -p
            try:
                result = subprocess.run(['lpstat', '-p', printer_name], capture_output=True, text=True)
                if "enabled" in result.stdout and "idle" in result.stdout:
                    return "online"
                elif "disabled" in result.stdout:
                    return "offline"
                else:
                    return "busy" # potentially
            except:
                return "error"
        else:
            return "online"

printer_manager = PrinterManager()
