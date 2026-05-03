import os
import sys
import time
import subprocess
import threading
from pyngrok import ngrok, conf
import qrcode

# ==========================================
# CONFIGURATION (EDIT THESE FOR PERMANENT LINK)
# ==========================================
# 1. Sign up at ngrok.com to get your Authtoken
NGROK_AUTHTOKEN = "3CkVp7m80mDPCqXdW8aVWOQ3WIK_4WwSgygZQ5EsS1GcWusqs" 

# 2. Claim your free Static Domain in ngrok dashboard (Cloud Edge -> Domains)
# Example: "your-app.ngrok-free.app"
STATIC_DOMAIN = "" 
# ==========================================

def print_qr(url):
    try:
        qr = qrcode.QRCode(version=1, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        
        # Print QR code in terminal using safe characters for Windows
        qr.print_ascii(invert=True)
    except Exception as e:
        print(f"[!] Could not display QR in terminal (Encoding issue): {e}")
        print("[*] You can still find the QR code image at 'static/qrcode.png'")


def run_flask_app(public_url):
    print(f"[*] Starting Flask App with Public URL: {public_url}")
    # Set the public URL as an environment variable for the Flask app
    env = os.environ.copy()
    env["PUBLIC_URL"] = public_url
    
    # Start the app.py using the current python interpreter
    subprocess.run([sys.executable, "app.py"], env=env)

def main():
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if NGROK_AUTHTOKEN:
        ngrok.set_auth_token(NGROK_AUTHTOKEN)
        print("[*] Ngrok Authtoken set.")

    try:
        print("[*] Starting Tunnel...")
        if STATIC_DOMAIN:
            print(f"[*] Using Static Domain: {STATIC_DOMAIN}")
            tunnel = ngrok.connect(5000, domain=STATIC_DOMAIN)
        else:
            print("[!] No Static Domain provided. Using temporary random URL.")
            tunnel = ngrok.connect(5000)

        public_url = tunnel.public_url
        
        print("\n" + "="*60)
        print("MOBILE ACCESS ENABLED")
        print(f"Link: {public_url}")
        print("="*60 + "\n")
        
        print("[*] Scan this QR code on your mobile phone:")

        print_qr(public_url)
        
        # Start Flask in a separate thread (optional, but here we just run it directly)
        # since we want to keep the tunnel alive while the app runs.
        run_flask_app(public_url)

    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
    except Exception as e:
        print(f"\n[!] Error: {e}")
    finally:
        ngrok.disconnect(tunnel.public_url)

if __name__ == "__main__":
    main()
