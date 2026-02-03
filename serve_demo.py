#!/usr/bin/env python3
"""
Script to serve the demo HTML file
"""
import http.server
import socketserver
import os

class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Quiet HTTP request handler"""
    def log_message(self, format, *args):
        # Suppress log messages
        pass

def main():
    """Run the HTTP server"""
    port = 8081
    os.chdir(".")

    with socketserver.TCPServer(("", port), QuietHTTPRequestHandler) as httpd:
        print(f"🌐 Serving demo on http://localhost:{port}")
        print(f"📄 Open: http://localhost:{port}/frontend_demo.html")
        print("Press Ctrl+C to stop")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Demo server stopped")

if __name__ == "__main__":
    main()