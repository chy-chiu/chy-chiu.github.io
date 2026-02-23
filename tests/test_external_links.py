import unittest

from generator.markdown_ext import MarkdownProcessor


class TestExternalLinks(unittest.TestCase):
    def test_bare_domain_links_get_https(self):
        mp = MarkdownProcessor(page_registry={}, citation_registry={})
        out = mp.process("[google](google.com)")
        self.assertIn('href="https://google.com"', out.html)

    def test_relative_links_are_unchanged(self):
        mp = MarkdownProcessor(page_registry={}, citation_registry={})
        out = mp.process("[Writing](/writing/)")
        self.assertIn('href="/writing/"', out.html)

        out2 = mp.process("[Post](writing/my-post/)")
        self.assertIn('href="writing/my-post/"', out2.html)

    def test_schemed_links_are_unchanged(self):
        mp = MarkdownProcessor(page_registry={}, citation_registry={})
        out = mp.process("[x](http://example.com)")
        self.assertIn('href="http://example.com"', out.html)

