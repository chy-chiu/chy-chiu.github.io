import tempfile
import unittest
from pathlib import Path

from generator.content import load_all_content


class TestPostsFolder(unittest.TestCase):
    def test_posts_folder_splits_writing_and_notes(self):
        with tempfile.TemporaryDirectory() as td:
            content_dir = Path(td) / "content"
            posts_dir = content_dir / "posts"
            posts_dir.mkdir(parents=True)

            (posts_dir / "a.md").write_text(
                "---\n"
                "title: Writing Post\n"
                "date: 2024-01-01\n"
                "post: true\n"
                "tags: [t]\n"
                "---\n"
                "Hello\n",
                encoding="utf-8",
            )
            (posts_dir / "b.md").write_text(
                "---\n"
                "title: Note\n"
                "date: 2024-01-02\n"
                "post: false\n"
                "tags: [t]\n"
                "---\n"
                "Hi\n",
                encoding="utf-8",
            )

            index = load_all_content(str(content_dir), include_drafts=True)
            self.assertEqual(len(index.writing), 1)
            self.assertEqual(len(index.notes), 1)
            self.assertIn("t", index.tags)
            self.assertEqual(len(index.tags["t"]), 2)

