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
from urllib.parse import urlparse
from generator.builder import Builder


class _NotFoundTo404Handler(http.server.SimpleHTTPRequestHandler):
    """
    Dev-server handler that serves the site's generated 404.html for missing routes.

    This matches GitHub Pages behavior more closely than the default handler.
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


def _cname_value(base_url: str) -> str:
    """
    Convert config.site.base_url into a valid CNAME value.

    GitHub Pages expects a bare host in CNAME (no scheme/path).
    """
    raw = (base_url or "").strip()
    if not raw:
        return ""

    parsed = urlparse(raw)
    if parsed.scheme:
        # Handles values like https://example.com
        host = parsed.netloc
    else:
        # Handles values like example.com or example.com/path
        host = raw.split("/", 1)[0]

    return host.strip().rstrip("/")


def _write_cname(output_dir: str, base_url: str) -> None:
    cname = _cname_value(base_url)
    if not cname:
        return

    os.makedirs(output_dir, exist_ok=True)
    cname_path = os.path.join(output_dir, "CNAME")
    with open(cname_path, "w", encoding="utf-8") as f:
        f.write(f"{cname}\n")


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


    builder = Builder(
        include_drafts=args.drafts,
        clean=args.clean,
        strict=not args.no_strict,
    )
    builder.build()
    _write_cname("output", builder.config.site.base_url)

    if args.serve:
        if not os.path.exists('output'):
            raise RuntimeError("output/ directory missing after build")
        os.chdir('output')
        with socketserver.TCPServer(("", args.port), _NotFoundTo404Handler) as httpd:
            print(f"Serving at http://localhost:{args.port}/ (Ctrl+C to stop)")
            httpd.serve_forever()


if __name__ == '__main__':
    sys.exit(main())
