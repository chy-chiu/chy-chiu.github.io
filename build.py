#!/usr/bin/env python3
"""
Static Site Generator - Build Script

Usage:
    python build.py              # Build site
    python build.py --drafts     # Include draft posts
    python build.py --clean      # Clean output before build
"""

import argparse
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
    args = parser.parse_args()

    # try:
    builder = Builder(
        include_drafts=args.drafts,
        clean=args.clean
    )
    builder.build()
    # print("\n✅ Build successful! Site generated in output/")
    # return 0
    # except Exception as e:
    #     print(f"\n❌ Build failed: {e}", file=sys.stderr)
    #     return 1


if __name__ == '__main__':
    sys.exit(main())
