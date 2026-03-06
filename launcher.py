"""
New Metro Big Bazaar — Desktop Launcher
Starts the Flask server and opens the app in a browser window.
Works fully offline. No internet required.
"""

import sys
import os
import time
import threading
import webbrowser
import subprocess
import socket

# ── Make sure we run from the script's directory ──────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

PORT = 5000

def is_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) != 0

def find_free_port(start=5000):
    for p in range(start, start + 20):
        if is_port_free(p):
            return p
    return start

def wait_for_server(port, timeout=15):
    """Wait until Flask is ready to accept connections."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False

def open_browser(port):
    """Wait for server then open browser."""
    if wait_for_server(port):
        webbrowser.open(f'http://127.0.0.1:{port}')
    else:
        print("❌ Server did not start in time.")

def run_flask(port):
    """Import and run the Flask app directly."""
    # Add project dir to path
    sys.path.insert(0, BASE_DIR)
    from app import app, init_db
    init_db()
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)

def main():
    port = find_free_port(5000)

    print("=" * 50)
    print("  🏪 New Metro Big Bazaar")
    print("  Billing & Inventory System")
    print("=" * 50)
    print(f"\n  Starting server on port {port}...")
    print(f"  URL: http://127.0.0.1:{port}")
    print(f"\n  Login: admin / admin123")
    print("\n  Close this window to stop the application.")
    print("-" * 50)

    # Start browser opener in background thread
    browser_thread = threading.Thread(target=open_browser, args=(port,), daemon=True)
    browser_thread.start()

    # Run Flask (blocking)
    try:
        run_flask(port)
    except KeyboardInterrupt:
        print("\n\n  App stopped. Goodbye!")

if __name__ == '__main__':
    main()
