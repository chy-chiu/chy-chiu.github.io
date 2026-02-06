import unittest

from generator.utils import to_url_slug


class TestSlugify(unittest.TestCase):
    def test_to_url_slug_basic(self):
        self.assertEqual(to_url_slug("My Post Title"), "my-post-title")

    def test_to_url_slug_collapses(self):
        self.assertEqual(to_url_slug("Hello   World!!!"), "hello-world")

