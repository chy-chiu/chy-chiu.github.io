#!/usr/bin/env python3
"""
Static Site Generator - Build Script

Usage:
    python build.py              # Build site
    python build.py --drafts     # Include draft posts
    python build.py --clean      # Clean output before build
    python build.py --no-strict  # Allow broken internal links
    python build.py --serve      # Serve output/ locally
"""

import argparse
import http.server
import os
import socketserver
import sys
from generator.builder import Builder


def main():
    parser = argparse.ArgumentParser(
        description='Build static site from markdown content'
    )
    parser.add_argument(
        '--drafts',
        action='store_true',
        help='Include draft posts in build'
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean output directory before build'
    )
    parser.add_argument(
        '--no-strict',
        action='store_true',
        help='Do not fail build on link-check problems'
    )
    parser.add_argument(
        '--serve',
        action='store_true',
        help='Serve output/ directory after building'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port for --serve (default: 8000)'
    )
    args = parser.parse_args()

    try:
        builder = Builder(
            include_drafts=args.drafts,
            clean=args.clean,
            strict=not args.no_strict,
        )
        builder.build()

        if args.serve:
            if not os.path.exists('output'):
                raise RuntimeError("output/ directory missing after build")
            os.chdir('output')
            handler = http.server.SimpleHTTPRequestHandler
            with socketserver.TCPServer(("", args.port), handler) as httpd:
                print(f"Serving at http://localhost:{args.port}/ (Ctrl+C to stop)")
                httpd.serve_forever()

        return 0
    except Exception as e:
        print(f"\nBuild failed: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
