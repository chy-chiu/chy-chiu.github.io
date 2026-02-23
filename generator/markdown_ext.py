"""
Custom markdown transformations and processing
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse
from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.footnote import footnote_plugin
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from bs4 import BeautifulSoup
from .content import Page
from .citations import Publication, format_citation, format_inline_citation
from .utils import to_url_slug, get_logger


logger = get_logger()

_BARE_DOMAIN_RE = re.compile(
    r"^(?P<host>(?:[a-z0-9-]+\.)+[a-z]{2,})(?P<rest>(?::\d+)?(?:[/?#].*)?)?$",
    re.IGNORECASE,
)


def _normalize_link_href(href: str) -> str:
    """
    Convert bare domains like 'google.com' to 'https://google.com'.

    Markdown treats 'google.com' as a relative URL; this makes it external by default.
    """
    if not href:
        return href

    href = href.strip()
    if not href:
        return href

    if href.startswith(("/", "#", "./", "../")):
        return href

    parsed = urlparse(href)
    if parsed.scheme:
        return href

    # Avoid rewriting likely relative paths (e.g., 'writing/my-post/').
    if "/" in href and not _BARE_DOMAIN_RE.match(href):
        return href

    if _BARE_DOMAIN_RE.match(href):
        return f"https://{href}"

    return href


def external_links_plugin(md: MarkdownIt) -> None:
    """
    Markdown-it-py core plugin: normalize hrefs for markdown links.
    """

    def normalize(state) -> bool:
        for token in state.tokens:
            if token.type != "inline":
                continue
            if not token.children:
                continue
            for child in token.children:
                if child.type != "link_open":
                    continue
                href = child.attrGet("href") or ""
                normalized = _normalize_link_href(href)
                if normalized != href:
                    child.attrSet("href", normalized)
        return False

    md.core.ruler.after("inline", "external_links", normalize)


@dataclass
class ProcessedContent:
    html: str
    toc_html: str = ""
    bibliography_html: str = ""
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class MarkdownProcessor:
    def __init__(self, page_registry: Dict[str, Page], citation_registry: Dict[str, Publication]):
        """
        Initialize markdown processor.

        Args:
            page_registry: Dictionary mapping Obsidian-style link keys (usually filename stem slugs) to Page objects
            citation_registry: Dictionary mapping citation keys to Publication objects
        """
        self.page_registry = page_registry
        self.citation_registry = citation_registry
        self.md = MarkdownIt()
        self.md.enable(['table', 'strikethrough'])
        self.md.use(external_links_plugin)
        self.citations_used = []  # Track citations in order of appearance

    def process(self, content: str, extract_toc: bool = False) -> ProcessedContent:
        """
        Process markdown content through full pipeline.

        Args:
            content: Raw markdown content
            extract_toc: Whether to extract table of contents

        Returns:
            ProcessedContent with HTML and optional TOC/bibliography
        """
        warnings = []

        # Reset citations for this document
        self.citations_used = []

        # Transform wiki links
        content, wiki_warnings = self._transform_wiki_links(content)
        warnings.extend(wiki_warnings)

        # Transform citations
        content = self._transform_citations(content)

        # Parse markdown to HTML
        html = self._parse_markdown(content)

        # Post-process HTML
        html = self._post_process_callouts(html)
        html = self._post_process_figures(html)
        html = self._post_process_code_blocks(html)

        # Extract TOC if requested
        toc_html = ""
        if extract_toc:
            html, toc_html = self._extract_toc(html)

        # Generate bibliography if citations were used
        bibliography_html = ""
        if self.citations_used:
            bibliography_html = self._generate_bibliography()

        return ProcessedContent(
            html=html,
            toc_html=toc_html,
            bibliography_html=bibliography_html,
            warnings=warnings
        )

    def _transform_wiki_links(self, content: str) -> Tuple[str, List[str]]:
        """
        Transform wiki links [[page]] or [[page|alias]] to HTML links.

        Returns:
            Tuple of (transformed_content, warnings)
        """
        warnings = []
        pattern = r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'

        def replace_link(match):
            page_title = match.group(1).strip()
            display_text = match.group(2).strip() if match.group(2) else page_title
            # Obsidian link targets may include heading or block refs, e.g. [[Note#Heading]] or [[Note^block]].
            link_target = re.split(r'[#^]', page_title, maxsplit=1)[0].strip()
            slug = to_url_slug(link_target)

            if slug in self.page_registry:
                page = self.page_registry[slug]
                return f'<a href="{page.url}">{display_text}</a>'
            else:
                warnings.append(f"Broken wiki link: [[{page_title}]]")
                return f'<span class="broken-link">{display_text}</span>'

        content = re.sub(pattern, replace_link, content)
        return content, warnings

    def _transform_citations(self, content: str) -> str:
        """
        Transform citation markers [@key] to numbered citations.

        Returns:
            Transformed content with citation markers
        """
        pattern = r'\[@([^\]]+)\]'

        def replace_citation(match):
            keys_str = match.group(1)
            keys = [k.strip().lstrip('@') for k in keys_str.split(';')]

            # Track citations and assign numbers
            citation_numbers = []
            for key in keys:
                if key in self.citation_registry:
                    if key not in self.citations_used:
                        self.citations_used.append(key)
                    num = self.citations_used.index(key) + 1
                    citation_numbers.append(str(num))
                else:
                    logger.warning(f"Unknown citation key: {key}")

            if not citation_numbers:
                return match.group(0)  # Return original if no valid keys

            # Get full citations for tooltip
            citations_text = "; ".join([
                format_inline_citation(self.citation_registry[key])
                for key in keys if key in self.citation_registry
            ])

            nums_str = ", ".join(citation_numbers)
            keys_str = ",".join(keys)

            return f'<cite class="citation" data-keys="{keys_str}" data-citation="{citations_text}">[{nums_str}]</cite>'

        return re.sub(pattern, replace_citation, content)

    def _parse_markdown(self, content: str) -> str:
        """
        Parse markdown to HTML using markdown-it-py.

        Returns:
            HTML string
        """
        return self.md.render(content)

    def _post_process_callouts(self, html: str) -> str:
        """
        Transform Obsidian-style callouts to HTML aside elements.

        Detects blockquotes starting with [!type] and converts them.
        """
        soup = BeautifulSoup(html, 'html.parser')

        for blockquote in soup.find_all('blockquote'):
            # Check if first element contains callout marker
            first_p = blockquote.find('p')
            if not first_p:
                continue

            text = first_p.get_text()
            callout_match = re.match(r'\[!(note|warning|tip|important|caution|info)\]\s*(.*)', text, re.IGNORECASE)

            if callout_match:
                callout_type = callout_match.group(1).lower()
                callout_title = callout_match.group(2) or callout_type.capitalize()

                # Create aside element
                aside = soup.new_tag('aside', attrs={'class': f'callout callout-{callout_type}'})

                # Create title div
                title_div = soup.new_tag('div', attrs={'class': 'callout-title'})
                icon_span = soup.new_tag('span', attrs={'class': 'callout-icon'})
                title_text_span = soup.new_tag('span', attrs={'class': 'callout-title-text'})
                title_text_span.string = callout_title
                title_div.append(icon_span)
                title_div.append(title_text_span)
                aside.append(title_div)

                # Create content div
                content_div = soup.new_tag('div', attrs={'class': 'callout-content'})

                # Remove the callout marker from first paragraph
                first_p.string = first_p.get_text().replace(callout_match.group(0), '').strip()
                if first_p.get_text().strip():
                    content_div.append(first_p.extract())

                # Move remaining content
                for elem in list(blockquote.children):
                    content_div.append(elem.extract())

                aside.append(content_div)

                # Replace blockquote with aside
                blockquote.replace_with(aside)

        return str(soup)

    def _post_process_figures(self, html: str) -> str:
        """
        Wrap images in figure elements with figcaption.
        """
        soup = BeautifulSoup(html, 'html.parser')

        for img in soup.find_all('img'):
            # Skip if already in a figure
            if img.parent.name == 'figure':
                continue

            alt_text = img.get('alt', '')
            figure_variant = None
            alt_match = re.match(r'^\s*(full|narrow|wide)\s*:\s*(.*)$', alt_text, re.IGNORECASE)
            if alt_match:
                figure_variant = alt_match.group(1).lower()
                alt_text = alt_match.group(2).strip()
                img['alt'] = alt_text

            # Resolve image path
            src = img.get('src', '')
            if not src.startswith('/') and not src.startswith('http'):
                src = f'/assets/images/{src}'
            img['src'] = src
            img['loading'] = 'lazy'

            # Create figure
            figure_class = 'image-figure'
            if figure_variant == 'full':
                figure_class += ' image-figure-full'
            elif figure_variant == 'narrow':
                figure_class += ' image-figure-narrow'
            figure = soup.new_tag('figure', attrs={'class': figure_class})
            figcaption = soup.new_tag('figcaption')
            figcaption.string = alt_text

            # Move img into figure
            img_copy = img.extract()
            figure.append(img_copy)
            if alt_text:
                figure.append(figcaption)

            # Replace original img location with figure
            # Find parent paragraph and replace it
            parent = img.parent if hasattr(img, 'parent') else None
            if parent and parent.name == 'p':
                parent.replace_with(figure)
            else:
                # If not in a paragraph, just insert figure
                figure.append(img)

        return str(soup)

    def _post_process_code_blocks(self, html: str) -> str:
        """
        Add syntax highlighting to code blocks using Pygments.
        """
        soup = BeautifulSoup(html, 'html.parser')

        for pre in soup.find_all('pre'):
            code = pre.find('code')
            if not code:
                continue

            # Try to detect language from class
            language = None
            if code.get('class'):
                for cls in code.get('class'):
                    if cls.startswith('language-'):
                        language = cls.replace('language-', '')
                        break

            code_text = code.get_text()

            # Apply syntax highlighting
            if language:
                try:
                    lexer = get_lexer_by_name(language, stripall=True)
                    formatter = HtmlFormatter(cssclass='highlight', nowrap=False)
                    highlighted = highlight(code_text, lexer, formatter)

                    # Create code block wrapper
                    wrapper = soup.new_tag('div', attrs={'class': 'code-block'})
                    header = soup.new_tag('div', attrs={'class': 'code-header'})
                    lang_span = soup.new_tag('span', attrs={'class': 'code-language'})
                    lang_span.string = language
                    header.append(lang_span)
                    wrapper.append(header)

                    # Parse highlighted HTML and add it
                    highlighted_soup = BeautifulSoup(highlighted, 'html.parser')
                    wrapper.append(highlighted_soup)

                    pre.replace_with(wrapper)
                except Exception as e:
                    logger.warning(f"Failed to highlight code block: {e}")

        return str(soup)

    def _extract_toc(self, html: str) -> Tuple[str, str]:
        """
        Extract table of contents from headings.

        Returns:
            Tuple of (html_with_ids, toc_html)
        """
        soup = BeautifulSoup(html, 'html.parser')
        headings = soup.find_all(['h2', 'h3', 'h4'])

        if not headings:
            return str(soup), ""

        # Add IDs to headings
        for heading in headings:
            if not heading.get('id'):
                heading['id'] = to_url_slug(heading.get_text())

        # Build TOC
        toc_soup = BeautifulSoup('<nav class="toc"></nav>', 'html.parser')
        toc = toc_soup.find('nav')

        title = toc_soup.new_tag('h2', attrs={'class': 'toc-title'})
        title.string = 'Contents'
        toc.append(title)

        toc_list = toc_soup.new_tag('ol', attrs={'class': 'toc-list'})

        stack = [(toc_list, 1)]  # (current_list, current_level)

        for heading in headings:
            level = int(heading.name[1])  # h2 -> 2, h3 -> 3, etc.
            text = heading.get_text()
            heading_id = heading.get('id')

            # Navigate to appropriate level
            while stack and stack[-1][1] >= level:
                stack.pop()

            # Create list item
            li = toc_soup.new_tag('li')
            a = toc_soup.new_tag('a', href=f'#{heading_id}')
            a.string = text
            li.append(a)

            # Add to current list
            current_list = stack[-1][0]
            current_list.append(li)

            # If we might have children, create nested list
            if level < 4:  # Max depth
                nested_list = toc_soup.new_tag('ol')
                li.append(nested_list)
                stack.append((nested_list, level + 1))

        toc.append(toc_list)

        return str(soup), str(toc)

    def _generate_bibliography(self) -> str:
        """
        Generate bibliography HTML from used citations.

        Returns:
            HTML string with bibliography section
        """
        if not self.citations_used:
            return ""

        html_parts = ['<section class="bibliography">']
        html_parts.append('<h2>References</h2>')
        html_parts.append('<ol class="references">')

        for i, key in enumerate(self.citations_used, 1):
            if key in self.citation_registry:
                pub = self.citation_registry[key]
                citation_html = format_citation(pub)
                html_parts.append(f'<li id="ref-{i}">{citation_html}</li>')

        html_parts.append('</ol>')
        html_parts.append('</section>')

        return '\n'.join(html_parts)
