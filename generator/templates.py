"""
Jinja2 template management
"""

from jinja2 import Environment, FileSystemLoader, select_autoescape
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

        # Add custom filters
        self.env.filters['slugify'] = to_url_slug
        self.env.filters['date_format'] = format_date

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
