from pyngrok import ngrok
import time
import sys

try:
    # Open a HTTP tunnel on the default port 5000
    public_url = ngrok.connect(5000).public_url
    print(f"NGROK_URL:{public_url}")
    
    # Keep the tunnel open
    while True:
        time.sleep(10)
except Exception as e:
    print(f"ERROR:{str(e)}")
    sys.exit(1)
