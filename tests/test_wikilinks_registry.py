import tempfile
import unittest
from pathlib import Path

from generator.content import load_all_content, build_page_registry
from generator.markdown_ext import MarkdownProcessor


class TestWikiLinksRegistry(unittest.TestCase):
    def test_wikilink_resolves_by_filename_stem_not_title(self):
        with tempfile.TemporaryDirectory() as td:
            content_dir = Path(td) / "content"
            posts_dir = content_dir / "posts"
            posts_dir.mkdir(parents=True)

            (posts_dir / "My Obsidian Note.md").write_text(
                "---\n"
                "title: Different Title\n"
                "date: 2024-01-01\n"
                "post: true\n"
                "---\n"
                "Body\n",
                encoding="utf-8",
            )

            index = load_all_content(str(content_dir), include_drafts=True)
            registry = build_page_registry(index.pages)

            processor = MarkdownProcessor(page_registry=registry, citation_registry={})
            processed = processor.process("See [[My Obsidian Note]] and [[My Obsidian Note|Alias]].")

            self.assertIn('<a href="/writing/different-title/">My Obsidian Note</a>', processed.html)
            self.assertIn('<a href="/writing/different-title/">Alias</a>', processed.html)

    def test_wikilink_ignores_heading_and_block_refs(self):
        with tempfile.TemporaryDirectory() as td:
            content_dir = Path(td) / "content"
            posts_dir = content_dir / "posts"
            posts_dir.mkdir(parents=True)

            (posts_dir / "Deep Note.md").write_text(
                "---\n"
                "title: Deep Title\n"
                "date: 2024-01-01\n"
                "post: true\n"
                "---\n"
                "Body\n",
                encoding="utf-8",
            )

            index = load_all_content(str(content_dir), include_drafts=True)
            registry = build_page_registry(index.pages)

            processor = MarkdownProcessor(page_registry=registry, citation_registry={})
            processed = processor.process("A [[Deep Note#Section]] and [[Deep Note^block]].")

            self.assertIn('<a href="/writing/deep-title/">Deep Note#Section</a>', processed.html)
            self.assertIn('<a href="/writing/deep-title/">Deep Note^block</a>', processed.html)

