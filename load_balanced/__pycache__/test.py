import subprocess
import time
import requests
import os
import signal
import sys

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada\\")
ports = [5000, 5001, 5002]  # Define ports

from okada import LogService

logger = LogService("load").get_logger()

logger.info(f"Parent PID: {os.getpid()}")

# Dictionary to track processes
processes = {}

# Function to start a Flask instance on a given port
def start_flask_instance(port):
    # Windows: Use DETACHED_PROCESS flag
    p = subprocess.Popen(
        ["C:\\Users\\omg0043.cyk\\dashboard_environment.bat", f"{ROOT}\\reports\\load_balanced\\app.py", str(port)],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,  # Alternative to DETACHED_PROCESS
        # stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL  # Hide logs (optional)
    )
    
    processes[port] = p
    logger.info(f"Started Flask instance on port {port} with PID {p.pid}")
    time.sleep(120)

# Start all instances initially
for port in ports:
    start_flask_instance(port)



try:
    while True:
        time.sleep(5)  # Check every 5 seconds

        for port, process in list(processes.items()):
            try:
                response = requests.get(f"http://srm.okadamanila.com:{port}", timeout=3,verify=False)
                if response.status_code == 200:
                    pass
                    # logger.info(f"Port {port} (PID {process.pid}) is healthy")
                else:
                    logger.info(f"Port {port} (PID {process.pid}) is unreachable, restarting...")
                    os.kill(process.pid, signal.SIGTERM)  # Terminate process safely
                    # start_flask_instance(port)

            except requests.exceptions.RequestException:
                logger.info(f"Port {port} (PID {process.pid}) is down, restarting...")
                # start_flask_instance(port)

except KeyboardInterrupt:
    logger.info("\nTerminating all processes...")
    for p in processes.values():
        os.kill(p.pid, signal.SIGTERM)  # Kill all processes on exit