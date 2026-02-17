"""
Jinja2 template management
"""

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape
from .config import Config
from .utils import to_url_slug, format_date


class TemplateEngine:
    def __init__(self, templates_dir: str, config: Config):
        """
        Initialize template engine.

        Args:
            templates_dir: Path to templates directory
            config: Site configuration
        """
        self.config = config
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

        def format_authors(authors, mode: str = "full"):
            highlight = (
                getattr(self.config.site, "author_highlight", None)
                or getattr(self.config.site, "author", "")
                or ""
            ).strip()
            highlight_lower = highlight.lower()

            authors_list = list(authors or [])
            if mode == "etal" and len(authors_list) > 1:
                display = f"{authors_list[0]} et al."
                authors_list = [display]

            out = []
            for a in authors_list:
                a_str = str(a)
                if highlight_lower and highlight_lower in a_str.lower():
                    out.append(Markup(f'<span class="author-highlight">{escape(a_str)}</span>'))
                else:
                    out.append(escape(a_str))
            return Markup(", ").join(out)

        # Add custom filters
        self.env.filters['slugify'] = to_url_slug
        self.env.filters['date_format'] = format_date
        self.env.filters['format_authors'] = format_authors
        self.env.filters['font_stack'] = self._font_stack

    @staticmethod
    def _font_stack(primary: str, kind: str) -> Markup:
        """
        Build a safe CSS font-family stack from a primary font.

        If `primary` already looks like a stack (contains a comma), it is returned as-is.
        """
        primary = (primary or "").strip()
        if not primary:
            primary = "serif" if kind in {"body", "heading"} else "monospace"

        if "," in primary:
            return Markup(primary)

        def q(name: str) -> str:
            name = (name or "").strip().strip('"').strip("'")
            return f"'{name}'" if name else ""

        if kind == "mono":
            return Markup(
                ", ".join(
                    [
                        q(primary),
                        "ui-monospace",
                        "SFMono-Regular",
                        "Menlo",
                        "Monaco",
                        "Consolas",
                        "'Liberation Mono'",
                        "monospace",
                    ]
                )
            )

        if kind == "heading":
            return Markup(
                ", ".join(
                    [
                        q(primary),
                        "'Marcellus'",
                        "'Noto Sans TC'",
                        "'Libre Baskerville'",
                        "serif",
                    ]
                )
            )

        # body
        return Markup(", ".join([q(primary), "'Noto Sans TC'", "ui-serif", "Georgia", "serif"]))

    def render(self, template_name: str, **context) -> str:
        """
        Render a template with context.

        Args:
            template_name: Name of template file
            **context: Template context variables

        Returns:
            Rendered HTML string
        """
        # Auto-include config in all contexts
        context['config'] = self.config

        template = self.env.get_template(template_name)
        return template.render(**context)
