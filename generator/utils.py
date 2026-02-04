"""
Utility functions for the static site generator
"""

import os
import shutil
import logging
from datetime import datetime, date as date_type
from slugify import slugify

def to_url_slug(text: str) -> str:
    """
    Convert text to URL-safe slug.

    Rules:
    - Lowercase
    - Replace spaces with hyphens
    - Remove special characters
    - Collapse multiple hyphens
    """
    return slugify(text, lowercase=True, separator='-')


def ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def copy_tree(src: str, dst: str) -> None:
    """Recursively copy directory tree."""
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def get_logger() -> logging.Logger:
    """Get configured logger."""
    logger = logging.getLogger('ssg')
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def format_date(date: datetime, fmt: str = '%B %d, %Y') -> str:
    if isinstance(date, datetime):
        date = date
    elif isinstance(date, date_type):
        # Convert date to datetime
        date = datetime.combine(date, datetime.min.time())
    else:
        try:
            date = datetime.strptime(str(date), '%Y-%m-%d')
        except ValueError:
            return None

    return date.strftime(fmt)
