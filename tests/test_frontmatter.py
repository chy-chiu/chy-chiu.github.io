import tempfile
import unittest
from pathlib import Path

from generator.content import ContentError, load_page, parse_frontmatter


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

    def test_load_page_uses_frontmatter_url_for_posts(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "post.md"
            path.write_text(
                "---\n"
                "title: \"Custom Route\"\n"
                "date: 2024-01-15\n"
                "url: essays/custom-route\n"
                "---\n"
                "Hello\n",
                encoding="utf-8",
            )

            post = load_page(str(path), "writing")
            self.assertEqual(post.url, "/blog/essays/custom-route/")

    def test_load_page_strips_section_prefix_from_frontmatter_url(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "post.md"
            path.write_text(
                "---\n"
                "title: \"Custom Route\"\n"
                "date: 2024-01-15\n"
                "url: /blog/essays/custom-route/\n"
                "---\n"
                "Hello\n",
                encoding="utf-8",
            )

            post = load_page(str(path), "writing")
            self.assertEqual(post.url, "/blog/essays/custom-route/")

    def test_load_page_rejects_external_url_override(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "post.md"
            path.write_text(
                "---\n"
                "title: \"Bad Route\"\n"
                "date: 2024-01-15\n"
                "url: https://example.com/post\n"
                "---\n"
                "Hello\n",
                encoding="utf-8",
            )

            with self.assertRaises(ContentError):
                load_page(str(path), "writing")

    def test_load_page_defaults_when_url_is_null(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "post.md"
            path.write_text(
                "---\n"
                "title: \"Null Route\"\n"
                "date: 2024-01-15\n"
                "url:\n"
                "---\n"
                "Hello\n",
                encoding="utf-8",
            )

            post = load_page(str(path), "writing")
            self.assertEqual(post.url, "/blog/null-route/")

    def test_load_page_defaults_when_url_is_blank(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "post.md"
            path.write_text(
                "---\n"
                "title: \"Blank Route\"\n"
                "date: 2024-01-15\n"
                "url: \"   \"\n"
                "---\n"
                "Hello\n",
                encoding="utf-8",
            )

            post = load_page(str(path), "writing")
            self.assertEqual(post.url, "/blog/blank-route/")
