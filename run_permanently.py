import subprocess
import time
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    filename='server_watchdog.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def start_server():
    logging.info("Attempting to start MedAI Server...")
    # Use sys.executable to ensure we use the same python environment
    # Use creationflags=subprocess.CREATE_NO_WINDOW on Windows for silent running
    creationflags = 0
    if os.name == 'nt':
        creationflags = subprocess.CREATE_NO_WINDOW
        
    return subprocess.Popen(
        [sys.executable, "app.py"],
        creationflags=creationflags,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

def monitor_server():
    while True:
        process = start_server()
        logging.info(f"MedAI Server started with PID: {process.pid}")
        
        # Monitor the process
        while process.poll() is None:
            time.sleep(10) # Check every 10 seconds
            
        # If we reach here, the process has exited
        error_msg = process.stderr.read() if process.stderr else "Unknown error"
        logging.error(f"MedAI Server stopped. Error output: {error_msg}")
        logging.info("Restarting in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    logging.info("MedAI Watchdog started.")
    try:
        monitor_server()
    except KeyboardInterrupt:
        logging.info("MedAI Watchdog stopped by user.")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"Watchdog crashed: {e}")
