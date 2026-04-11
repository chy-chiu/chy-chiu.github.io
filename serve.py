#!/usr/bin/env python3
"""
Simple development server for the static site.

Usage:
    python3 serve.py
    python3 serve.py 8080  # Custom port
"""

import http.server
import socketserver
import os
import sys


class _NotFoundTo404Handler(http.server.SimpleHTTPRequestHandler):
    """
    Serve the site's generated 404.html for missing routes.

    This makes local development behave like GitHub Pages/static hosting.
    """

    def send_error(self, code, message=None, explain=None):
        if code != 404:
            return super().send_error(code, message, explain)

        try:
            with open("404.html", "rb") as f:
                body = f.read()
        except OSError:
            return super().send_error(code, message, explain)

        self.send_response(404, message)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    # Change to output directory
    output_dir = 'output'

    if not os.path.exists(output_dir):
        print("Error: output/ directory doesn't exist. Run 'python3 build.py' first.")
        return 1

    os.chdir(output_dir)

    # Get port from args or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

    Handler = _NotFoundTo404Handler

    with socketserver.TCPServer(("", port), Handler) as httpd:
        print(f"✅ Server running at http://localhost:{port}/")
        print(f"📁 Serving from: {os.getcwd()}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped")
            return 0

if __name__ == "__main__":
    sys.exit(main())
