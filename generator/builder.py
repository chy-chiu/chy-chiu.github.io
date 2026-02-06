"""
Main build orchestration
"""

import os
import shutil
from pathlib import Path
from .config import load_config, Config
from .content import load_all_content, ContentIndex
from .citations import load_bibtex
from .markdown_ext import MarkdownProcessor
from .templates import TemplateEngine
from .utils import ensure_dir, get_logger


logger = get_logger()


class Builder:
    def __init__(self, include_drafts: bool = False, clean: bool = False, strict: bool = True):
        """
        Initialize builder.

        Args:
            include_drafts: Whether to include draft posts
            clean: Whether to clean output directory before build
        """
        self.include_drafts = include_drafts
        self.clean = clean
        self.strict = strict
        self.config: Config = None
        self.content: ContentIndex = None
        self.publications = {}
        self.processor: MarkdownProcessor = None
        self.templates: TemplateEngine = None

    def build(self):
        """Main build orchestration method."""
        logger.info("Starting build...")

        # Load configuration
        self.config = load_config()
        logger.info("Configuration loaded")

        # Clean output if requested
        if self.clean and os.path.exists('output'):
            logger.info("Cleaning output directory")
            shutil.rmtree('output')

        # Ensure output directory exists
        ensure_dir('output')

        # Load all content
        logger.info("Loading content...")
        self.content = load_all_content(include_drafts=self.include_drafts)
        logger.info(f"Loaded {len(self.content.pages)} pages, "
                   f"{len(self.content.writing)} writing posts, "
                   f"{len(self.content.notes)} notes, "
                   f"{len(self.content.projects)} projects")

        # Load publications
        bib_path = 'content/publications.bib'
        if os.path.exists(bib_path):
            self.publications = load_bibtex(bib_path)
            logger.info(f"Loaded {len(self.publications)} publications")

        # Initialize markdown processor
        self.processor = MarkdownProcessor(
            page_registry=self.content.pages,
            citation_registry=self.publications
        )

        # Initialize template engine
        self.templates = TemplateEngine('templates', self.config)

        # Process all markdown content
        logger.info("Processing markdown content...")
        self._process_all_markdown()

        # Render pages
        logger.info("Rendering pages...")
        self._render_static_pages()
        self._render_writing()
        self._render_notes()
        self._render_tags()
        self._render_archives()

        # Copy static assets
        logger.info("Copying static files...")
        self._copy_static_assets()

        # Extra production files
        self._render_404()
        self._write_sitemap()
        self._write_robots()
        self._write_rss()
        self._write_og_images()
        self._check_output_links()

        logger.info("Build complete!")

    def _og_url_for(self, section: str, slug: str | None = None) -> str:
        if section in {"writing", "notes"} and slug:
            return f"/og/{section}/{slug}.svg"
        return f"/og/{section}.svg"

    def _process_all_markdown(self):
        """Process markdown content for all pages."""
        for page in self.content.pages.values():
            processed = self.processor.process(
                page.raw_content,
                extract_toc=page.toc
            )
            page.html_content = processed.html
            page.toc_html = processed.toc_html
            page.bibliography_html = processed.bibliography_html

            # Log warnings
            for warning in processed.warnings:
                logger.warning(f"{page.slug}: {warning}")

    def _render_static_pages(self):
        """Render static pages (home, about, research, now)."""

        def get_page_by_section(section: str):
            for p in self.content.pages.values():
                if p.section == section:
                    return p
            return None

        # Render homepage (home + highlights)
        page = get_page_by_section('home')
        if page:

            def year_sort_key(pub):
                try:
                    return int(str(pub.year).strip())
                except Exception:
                    return -1

            def month_sort_key(pub):
                try:
                    return int(getattr(pub, "month", 0) or 0)
                except Exception:
                    return 0

            publications_sorted = sorted(
                list(self.publications.values()),
                key=lambda p: (year_sort_key(p), month_sort_key(p), (p.title or "").lower()),
                reverse=True,
            )

            featured_keys = self.config.home.featured_publications or []
            featured_from_keys = [self.publications[k] for k in featured_keys if k in self.publications]
            featured_from_bibtex = [p for p in publications_sorted if getattr(p, "selected", False)]
            featured_publications = []
            seen_keys = set()
            for p in featured_from_keys + featured_from_bibtex:
                if p.key in seen_keys:
                    continue
                seen_keys.add(p.key)
                featured_publications.append(p)

            recent_publications = publications_sorted[: (self.config.home.papers_count or 3)]

            featured_writing_slugs = set(self.config.home.featured_writing or [])
            featured_writing = [p for p in self.content.writing if p.featured or p.slug in featured_writing_slugs]

            def sort_ts(dt):
                return int(dt.timestamp()) if dt else 0

            featured_writing.sort(key=lambda p: (p.featured_order, -sort_ts(p.date)))
            recent_writing = self.content.writing[: (self.config.home.recent_writing_count or 3)]

            html = self.templates.render(
                'home.html',
                page=page,
                featured_writing=featured_writing,
                recent_writing=recent_writing,
                publications=featured_publications if featured_publications else recent_publications,
                publications_title="Selected Papers" if featured_publications else "Recent Papers",
                pub_authors_mode="etal",
                og_image_url=self._og_url_for("home"),
                current_url='/'
            )
            self._write_file('output/index.html', html)
            logger.info("Rendered homepage (index.html)")

        # Render about page (optional; only when content/about.md is treated as about page)
        about_page = get_page_by_section('about')
        if about_page:
            html = self.templates.render(
                'page.html',
                page=about_page,
                og_image_url=self._og_url_for("about"),
                current_url='/about/'
            )
            self._write_file('output/about/index.html', html)
            logger.info("Rendered about page")

        # Render research page
        page = get_page_by_section('research')
        if page:

            html = self.templates.render(
                'research.html',
                page=page,
                projects=self.content.projects,
                publications=self.publications.values(),
                pub_authors_mode="full",
                og_image_url=self._og_url_for("research"),
                current_url='/research/'
            )
            self._write_file('output/research/index.html', html)
            logger.info("Rendered research page")

        # Render now page (optional)
        page = get_page_by_section('now')
        if page:
            html = self.templates.render(
                'page.html',
                page=page,
                og_image_url=self._og_url_for("now"),
                current_url='/now/'
            )
            self._write_file('output/now/index.html', html)
            logger.info("Rendered now page")

    def _render_writing(self):
        """Render writing section pages."""
        # Render writing index
        html = self.templates.render(
            'post_index.html',
            section_title='Writing',
            posts=self.content.writing,
            og_image_url=self._og_url_for("writing"),
            current_url='/writing/'
        )
        self._write_file('output/writing/index.html', html)
        logger.info(f"Rendered writing index")

        # Render individual writing posts
        for post in self.content.writing:
            html = self.templates.render(
                'post.html',
                post=post,
                toc_html=post.toc_html,
                og_image_url=self._og_url_for("writing", post.slug),
                current_url=post.url
            )
            self._write_file(f'output{post.url}index.html', html)

        logger.info(f"Rendered {len(self.content.writing)} writing posts")

    def _render_notes(self):
        """Render notes section pages."""
        # Render notes index
        html = self.templates.render(
            'post_index.html',
            section_title='Notes',
            posts=self.content.notes,
            og_image_url=self._og_url_for("notes"),
            current_url='/notes/'
        )
        self._write_file('output/notes/index.html', html)
        logger.info(f"Rendered notes index")

        # Render individual notes
        for post in self.content.notes:
            html = self.templates.render(
                'post.html',
                post=post,
                toc_html=post.toc_html,
                og_image_url=self._og_url_for("notes", post.slug),
                current_url=post.url
            )
            self._write_file(f'output{post.url}index.html', html)

        logger.info(f"Rendered {len(self.content.notes)} notes")

    def _render_archives(self):
        def group_by_year(posts):
            out = {}
            for p in posts:
                if not p.date:
                    continue
                out.setdefault(p.date.year, []).append(p)
            for year in out:
                out[year].sort(key=lambda p: p.date, reverse=True)
            return out

        writing_by_year = group_by_year(self.content.writing)
        for year, posts in writing_by_year.items():
            html = self.templates.render(
                'post_index.html',
                section_title=f'Writing: {year}',
                posts=posts,
                og_image_url=self._og_url_for("writing"),
                current_url=f'/writing/{year}/'
            )
            self._write_file(f'output/writing/{year}/index.html', html)

        notes_by_year = group_by_year(self.content.notes)
        for year, posts in notes_by_year.items():
            html = self.templates.render(
                'post_index.html',
                section_title=f'Notes: {year}',
                posts=posts,
                og_image_url=self._og_url_for("notes"),
                current_url=f'/notes/{year}/'
            )
            self._write_file(f'output/notes/{year}/index.html', html)

    def _render_tags(self):
        """Render tag pages."""
        if not self.content.tags:
            return

        # Render tag index
        html = self.templates.render(
            'tag_index.html',
            tags=self.content.tags,
            og_image_url=self._og_url_for("tags"),
            current_url='/tags/'
        )
        self._write_file('output/tags/index.html', html)
        logger.info("Rendered tag index")

        # Render individual tag pages
        from .utils import to_url_slug
        for tag, posts in self.content.tags.items():
            tag_slug = to_url_slug(tag)
            html = self.templates.render(
                'tag_page.html',
                tag=tag,
                posts=posts,
                og_image_url=self._og_url_for("tags"),
                current_url=f'/tags/{tag_slug}/'
            )
            self._write_file(f'output/tags/{tag_slug}/index.html', html)

        logger.info(f"Rendered {len(self.content.tags)} tag pages")

    def _copy_static_assets(self):
        """Copy static assets and content assets to output."""
        # Copy static directory
        if os.path.exists('static'):
            for item in os.listdir('static'):
                src = os.path.join('static', item)
                dst = os.path.join('output/static', item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    ensure_dir('output/static')
                    shutil.copy2(src, dst)

        # Copy assets directory
        if os.path.exists('assets'):
            dst = 'output/assets'
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree('assets', dst)

    def _write_file(self, path: str, content: str):
        """
        Write content to file, creating directories as needed.

        Args:
            path: Output file path
            content: Content to write
        """
        ensure_dir(os.path.dirname(path))
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _render_404(self):
        html = self.templates.render('404.html', current_url='/404/')
        self._write_file('output/404.html', html)

    def _iter_site_urls(self):
        yield '/'
        if any(p.section == 'about' for p in self.content.pages.values()):
            yield '/about/'
        if any(p.section == 'now' for p in self.content.pages.values()):
            yield '/now/'
        if any(p.section == 'research' for p in self.content.pages.values()):
            yield '/research/'
        yield '/writing/'
        for year in sorted({p.date.year for p in self.content.writing if p.date}, reverse=True):
            yield f'/writing/{year}/'
        for post in self.content.writing:
            yield post.url
        yield '/notes/'
        for year in sorted({p.date.year for p in self.content.notes if p.date}, reverse=True):
            yield f'/notes/{year}/'
        for note in self.content.notes:
            yield note.url
        if self.content.tags:
            yield '/tags/'
            from .utils import to_url_slug
            for tag in self.content.tags.keys():
                yield f"/tags/{to_url_slug(tag)}/"

    def _write_sitemap(self):
        import xml.etree.ElementTree as ET

        urlset = ET.Element('urlset', attrib={'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9'})
        for url_path in sorted(set(self._iter_site_urls())):
            url = ET.SubElement(urlset, 'url')
            loc = ET.SubElement(url, 'loc')
            loc.text = f"{self.config.site.base_url}{url_path}"

        xml = ET.tostring(urlset, encoding='utf-8', xml_declaration=True).decode('utf-8')
        self._write_file('output/sitemap.xml', xml)

    def _write_robots(self):
        lines = [
            "User-agent: *",
            "Allow: /",
            "",
            f"Sitemap: {self.config.site.base_url}/sitemap.xml",
            "",
        ]
        self._write_file('output/robots.txt', "\n".join(lines))

    def _write_rss(self):
        import xml.etree.ElementTree as ET
        from datetime import timezone
        from email.utils import format_datetime

        rss = ET.Element('rss', attrib={'version': '2.0'})
        channel = ET.SubElement(rss, 'channel')
        ET.SubElement(channel, 'title').text = self.config.site.title
        ET.SubElement(channel, 'link').text = f"{self.config.site.base_url}/"
        ET.SubElement(channel, 'description').text = self.config.site.description

        for post in self.content.writing[:50]:
            item = ET.SubElement(channel, 'item')
            ET.SubElement(item, 'title').text = post.title
            ET.SubElement(item, 'link').text = f"{self.config.site.base_url}{post.url}"
            ET.SubElement(item, 'guid').text = f"{self.config.site.base_url}{post.url}"
            if post.subtitle:
                ET.SubElement(item, 'description').text = post.subtitle
            if post.date:
                dt = post.date
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                ET.SubElement(item, 'pubDate').text = format_datetime(dt)

        xml = ET.tostring(rss, encoding='utf-8', xml_declaration=True).decode('utf-8')
        self._write_file('output/rss.xml', xml)

    def _write_og_images(self):
        from xml.sax.saxutils import escape as xml_escape

        def svg(title: str, subtitle: str):
            title_esc = xml_escape(title or "")
            subtitle_esc = xml_escape(subtitle or "")
            return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630">
  <rect width="1200" height="630" fill="#ffffff"/>
  <rect x="0" y="0" width="1200" height="630" fill="#ffffff"/>
  <text x="96" y="220" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif" font-size="64" font-weight="700" fill="#1a1a1a">{title_esc}</text>
  <text x="96" y="300" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif" font-size="32" fill="#666666">{subtitle_esc}</text>
  <text x="96" y="560" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif" font-size="28" fill="#666666">{xml_escape(self.config.site.base_url)}</text>
</svg>"""

        pages_by_section = {p.section: p for p in self.content.pages.values()}
        for section in ("home", "about", "now", "research", "writing", "notes", "tags"):
            if section in {"writing", "notes"}:
                continue
            title = self.config.site.title if section == "home" else section.capitalize()
            subtitle = self.config.site.description
            if section in pages_by_section:
                title = pages_by_section[section].title
                subtitle = pages_by_section[section].description or pages_by_section[section].subtitle or self.config.site.description
            self._write_file(f"output/og/{section}.svg", svg(title, subtitle))

        for post in self.content.writing:
            self._write_file(f"output/og/writing/{post.slug}.svg", svg(post.title, post.subtitle or self.config.site.description))

        for note in self.content.notes:
            self._write_file(f"output/og/notes/{note.slug}.svg", svg(note.title, note.subtitle or self.config.site.description))

    def _check_output_links(self):
        import re

        if not os.path.exists('output'):
            return

        def normalize(path: str) -> str:
            path = path.split('#', 1)[0].split('?', 1)[0]
            return path

        def output_path_for_url(url_path: str) -> str:
            if url_path == '/':
                return 'output/index.html'
            if url_path.startswith('/'):
                url_path = url_path[1:]
            if not url_path:
                return 'output/index.html'
            if url_path.endswith('/'):
                return os.path.join('output', url_path, 'index.html')
            return os.path.join('output', url_path)

        html_files = []
        for root, _dirs, files in os.walk('output'):
            for f in files:
                if f.endswith('.html'):
                    html_files.append(os.path.join(root, f))

        problems = []
        for path in sorted(html_files):
            try:
                with open(path, 'r', encoding='utf-8') as fh:
                    html = fh.read()
            except Exception:
                continue

            for attr in ('href', 'src'):
                for m in re.finditer(rf'{attr}="([^"]+)"', html):
                    raw = m.group(1)
                    if not raw or raw.startswith('#'):
                        continue
                    if raw.startswith(('http://', 'https://', 'mailto:')):
                        continue
                    url_path = normalize(raw)
                    if url_path.startswith('/'):
                        candidate = output_path_for_url(url_path)
                        if not os.path.exists(candidate):
                            problems.append(f"{path}: missing {url_path} -> {candidate}")

        for p in problems:
            logger.warning(p)

        if self.strict and problems:
            raise RuntimeError(f"Link check failed with {len(problems)} broken internal links/assets")
