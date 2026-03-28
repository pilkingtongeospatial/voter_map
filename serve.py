"""
Local HTTP server for the Voter Map.
Run this script, then open http://localhost:8000 in your browser.
"""
import http.server
import socketserver
import os
import webbrowser
import threading

PORT = 8000
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silence per-request logs

def open_browser():
    import time; time.sleep(1)
    webbrowser.open(f"http://localhost:{PORT}")

print(f"Serving Voter Map at http://localhost:{PORT}")
print("Press Ctrl+C to stop.\n")
threading.Thread(target=open_browser, daemon=True).start()

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
