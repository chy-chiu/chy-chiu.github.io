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

def main():
    # Change to output directory
    output_dir = 'output'

    if not os.path.exists(output_dir):
        print("Error: output/ directory doesn't exist. Run 'python3 build.py' first.")
        return 1

    os.chdir(output_dir)

    # Get port from args or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

    Handler = http.server.SimpleHTTPRequestHandler

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
