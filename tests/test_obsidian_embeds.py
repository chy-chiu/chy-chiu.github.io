import unittest

from generator.markdown_ext import MarkdownProcessor


class TestObsidianEmbeds(unittest.TestCase):
    def test_obsidian_image_embed_becomes_image(self):
        mp = MarkdownProcessor(page_registry={}, citation_registry={}, attachments_url_prefix="/assets/posts/assets/")
        out = mp.process("![[Pasted Image.png]]")
        self.assertIn('src="/assets/posts/assets/Pasted%20Image.png"', out.html)

    def test_obsidian_image_embed_alias_becomes_caption(self):
        mp = MarkdownProcessor(page_registry={}, citation_registry={}, attachments_url_prefix="/assets/posts/assets/")
        out = mp.process("![[img.png|Caption]]")
        self.assertIn("<figcaption>Caption</figcaption>", out.html)

    def test_obsidian_image_embed_size_alias_is_ignored(self):
        mp = MarkdownProcessor(page_registry={}, citation_registry={}, attachments_url_prefix="/assets/posts/assets/")
        out = mp.process("![[img.png|300]]")
        self.assertIn('src="/assets/posts/assets/img.png"', out.html)

    def test_obsidian_image_embed_trailing_caption(self):
        mp = MarkdownProcessor(page_registry={}, citation_registry={}, attachments_url_prefix="/assets/posts/assets/")
        out = mp.process("![[img.png]](Hello world)")
        self.assertIn("<figcaption>Hello world</figcaption>", out.html)

    def test_markdown_image_in_posts_section_uses_posts_assets(self):
        mp = MarkdownProcessor(page_registry={}, citation_registry={}, attachments_url_prefix="/assets/posts/assets/")
        out = mp.process("![Alt](img.png)", section="writing")
        self.assertIn('src="/assets/posts/assets/img.png"', out.html)

        out2 = mp.process("![Alt](assets/img.png)", section="writing")
        self.assertIn('src="/assets/posts/assets/img.png"', out2.html)
