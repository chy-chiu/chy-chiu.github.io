import tempfile
import unittest
from pathlib import Path

from generator.content import load_page, parse_frontmatter


class TestFrontmatter(unittest.TestCase):
    def test_parse_frontmatter_none(self):
        fm, body = parse_frontmatter("hello")
        self.assertEqual(fm, {})
        self.assertEqual(body, "hello")

    def test_load_page_home_and_about_routes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "page.md"
            path.write_text("---\ntitle: \"About\"\n---\nHello", encoding="utf-8")

            home = load_page(str(path), "home")
            self.assertEqual(home.url, "/")

            about = load_page(str(path), "about")
            self.assertEqual(about.url, "/about/")

