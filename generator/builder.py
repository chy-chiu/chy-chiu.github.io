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
    def __init__(self, include_drafts: bool = False, clean: bool = False):
        """
        Initialize builder.

        Args:
            include_drafts: Whether to include draft posts
            clean: Whether to clean output directory before build
        """
        self.include_drafts = include_drafts
        self.clean = clean
        self.config: Config = None
        self.content: ContentIndex = None
        self.publications = {}
        self.processor: MarkdownProcessor = None
        self.templates: TemplateEngine = None

    def build(self):
        """Main build orchestration method."""
        logger.info("Starting build...")

        # Load configuration
        try:
            self.config = load_config()
            logger.info("Configuration loaded")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return

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

        # Copy static assets
        logger.info("Copying static files...")
        self._copy_static_assets()

        logger.info("Build complete!")

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
        """Render static pages (about, research, now)."""
        # Render homepage (about + recent writing + papers)
        about_slug = 'about'
        if about_slug in self.content.pages:
            page = self.content.pages[about_slug]

            def year_sort_key(pub):
                try:
                    return int(str(pub.year).strip())
                except Exception:
                    return -1

            recent_publications = sorted(
                list(self.publications.values()),
                key=lambda p: (year_sort_key(p), p.title.lower()),
                reverse=True,
            )[:3]

            html = self.templates.render(
                'home.html',
                page=page,
                recent_writing=self.content.writing[:3],
                recent_publications=recent_publications,
                current_url='/'
            )
            self._write_file('output/index.html', html)
            logger.info("Rendered homepage (index.html)")

        # Render research page
        research_slug = 'research'
        if research_slug in self.content.pages:
            page = self.content.pages[research_slug]

            # Group publications by year
            pubs_by_year = {}
            for pub in self.publications.values():
                year = pub.year
                if year not in pubs_by_year:
                    pubs_by_year[year] = []
                pubs_by_year[year].append(pub)

            html = self.templates.render(
                'research.html',
                page=page,
                projects=self.content.projects,
                publications=self.publications.values(),
                current_url='/research/'
            )
            self._write_file('output/research/index.html', html)
            logger.info("Rendered research page")

        # Render now page (optional)
        now_slug = 'now'
        if now_slug in self.content.pages:
            page = self.content.pages[now_slug]
            html = self.templates.render(
                'page.html',
                page=page,
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
                current_url=post.url
            )
            self._write_file(f'output{post.url}index.html', html)

        logger.info(f"Rendered {len(self.content.notes)} notes")

    def _render_tags(self):
        """Render tag pages."""
        if not self.content.tags:
            return

        # Render tag index
        html = self.templates.render(
            'tag_index.html',
            tags=self.content.tags,
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
