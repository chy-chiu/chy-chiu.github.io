"""
Configuration loading and validation
"""

import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


@dataclass
class NavItem:
    label: str
    url: str


@dataclass
class SiteConfig:
    title: str
    description: str
    base_url: str
    author: str
    links: List[Dict[str, str]] = field(default_factory=list)
    author_highlight: Optional[str] = None


@dataclass
class HomeConfig:
    recent_writing_count: int = 3
    featured_writing: List[str] = field(default_factory=list)  # slugs
    papers_count: int = 3
    featured_publications: List[str] = field(default_factory=list)  # BibTeX keys


@dataclass
class FeatureConfig:
    reading_time: bool = False


@dataclass
class StyleConfig:
    font_body: str = "Libre Baskerville"
    font_mono: str = "IBM Plex Mono"
    font_heading: str = "Friz Quadrata"
    font_link: Optional[str] = None
    font_weight_heading: int = 400

    font_size_root: str = "16px"
    font_size_prose: str = "1.125rem"
    font_size_h1: str = "2.25rem"
    font_size_h2: str = "1.75rem"
    font_size_h3: str = "1.375rem"
    font_size_h4: str = "1.125rem"
    font_size_page_title: str = "2.5rem"
    font_size_post_title: str = "1.5rem"
    font_size_home_h2: str = "1.5rem"
    font_size_section_h2: str = "1.75rem"
    font_size_bibliography_h2: str = "1.5rem"

    color_bg: str = "#ffffff"
    color_text: str = "#1a1a1a"
    color_text_muted: str = "#666666"
    color_accent: str = "#0066cc"
    color_link: Optional[str] = None
    color_link_hover: Optional[str] = None
    color_border: str = "#e0e0e0"
    color_code_bg: str = "#f5f5f5"

    color_bg_dark: str = "#1a1a1a"
    color_text_dark: str = "#e0e0e0"
    color_text_muted_dark: str = "#999999"
    color_accent_dark: str = "#66b3ff"
    color_link_dark: Optional[str] = None
    color_link_hover_dark: Optional[str] = None
    color_border_dark: str = "#333333"
    color_code_bg_dark: str = "#2d2d2d"


@dataclass
class Config:
    site: SiteConfig
    nav: List[NavItem]
    style: StyleConfig
    math: bool = True
    home: HomeConfig = field(default_factory=HomeConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)


def _coalesce(*values):
    for v in values:
        if v is not None:
            return v
    return None


def _get_dict(value) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _parse_font_weight(value, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v.isdigit():
            return int(v)
        if v == "normal":
            return 400
        if v == "bold":
            return 700
    return default


def _parse_style(style_data: Dict[str, Any]) -> StyleConfig:
    """
    Parse `style:` allowing both the legacy flat schema and a nested schema:

    style:
      fonts: {body, mono, heading, link?, heading_weight?}
      sizes: {root, prose, headings: {h1..h4}, titles: {...}}
      colors: {light: {...}, dark: {...}}
    """
    style_data = _get_dict(style_data)
    fonts = _get_dict(style_data.get("fonts"))
    sizes = _get_dict(style_data.get("sizes"))
    headings = _get_dict(sizes.get("headings"))
    titles = _get_dict(sizes.get("titles"))
    colors = _get_dict(style_data.get("colors"))
    light = _get_dict(colors.get("light"))
    dark = _get_dict(colors.get("dark"))

    # Fonts
    font_body = _coalesce(fonts.get("body"), style_data.get("font_body"), StyleConfig.font_body)
    font_mono = _coalesce(fonts.get("mono"), style_data.get("font_mono"), StyleConfig.font_mono)
    font_heading = _coalesce(fonts.get("heading"), style_data.get("font_heading"), StyleConfig.font_heading)
    font_link = _coalesce(fonts.get("link"), style_data.get("font_link"))
    font_weight_heading = _coalesce(fonts.get("heading_weight"), style_data.get("font_weight_heading"), StyleConfig.font_weight_heading)

    # Sizes
    font_size_root = _coalesce(sizes.get("root"), style_data.get("font_size_root"), StyleConfig.font_size_root)
    font_size_prose = _coalesce(sizes.get("prose"), style_data.get("font_size_prose"), StyleConfig.font_size_prose)
    font_size_h1 = _coalesce(headings.get("h1"), style_data.get("font_size_h1"), StyleConfig.font_size_h1)
    font_size_h2 = _coalesce(headings.get("h2"), style_data.get("font_size_h2"), StyleConfig.font_size_h2)
    font_size_h3 = _coalesce(headings.get("h3"), style_data.get("font_size_h3"), StyleConfig.font_size_h3)
    font_size_h4 = _coalesce(headings.get("h4"), style_data.get("font_size_h4"), StyleConfig.font_size_h4)

    font_size_page_title = _coalesce(titles.get("page"), style_data.get("font_size_page_title"), StyleConfig.font_size_page_title)
    font_size_post_title = _coalesce(titles.get("post"), style_data.get("font_size_post_title"), StyleConfig.font_size_post_title)
    font_size_home_h2 = _coalesce(titles.get("home_h2"), style_data.get("font_size_home_h2"), StyleConfig.font_size_home_h2)
    font_size_section_h2 = _coalesce(titles.get("section_h2"), style_data.get("font_size_section_h2"), StyleConfig.font_size_section_h2)
    font_size_bibliography_h2 = _coalesce(
        titles.get("bibliography_h2"),
        style_data.get("font_size_bibliography_h2"),
        StyleConfig.font_size_bibliography_h2,
    )

    # Colors
    color_bg = _coalesce(light.get("bg"), style_data.get("color_bg"), StyleConfig.color_bg)
    color_text = _coalesce(light.get("text"), style_data.get("color_text"), StyleConfig.color_text)
    color_text_muted = _coalesce(light.get("text_muted"), style_data.get("color_text_muted"), StyleConfig.color_text_muted)
    color_accent = _coalesce(light.get("accent"), style_data.get("color_accent"), StyleConfig.color_accent)
    color_link = _coalesce(light.get("link"), style_data.get("color_link"))
    color_link_hover = _coalesce(light.get("link_hover"), style_data.get("color_link_hover"))
    color_border = _coalesce(light.get("border"), style_data.get("color_border"), StyleConfig.color_border)
    color_code_bg = _coalesce(light.get("code_bg"), style_data.get("color_code_bg"), StyleConfig.color_code_bg)

    color_bg_dark = _coalesce(dark.get("bg"), style_data.get("color_bg_dark"), StyleConfig.color_bg_dark)
    color_text_dark = _coalesce(dark.get("text"), style_data.get("color_text_dark"), StyleConfig.color_text_dark)
    color_text_muted_dark = _coalesce(dark.get("text_muted"), style_data.get("color_text_muted_dark"), StyleConfig.color_text_muted_dark)
    color_accent_dark = _coalesce(dark.get("accent"), style_data.get("color_accent_dark"), StyleConfig.color_accent_dark)
    color_link_dark = _coalesce(dark.get("link"), style_data.get("color_link_dark"))
    color_link_hover_dark = _coalesce(dark.get("link_hover"), style_data.get("color_link_hover_dark"))
    color_border_dark = _coalesce(dark.get("border"), style_data.get("color_border_dark"), StyleConfig.color_border_dark)
    color_code_bg_dark = _coalesce(dark.get("code_bg"), style_data.get("color_code_bg_dark"), StyleConfig.color_code_bg_dark)

    return StyleConfig(
        font_body=font_body,
        font_mono=font_mono,
        font_heading=font_heading,
        font_link=font_link,
        font_weight_heading=_parse_font_weight(font_weight_heading, StyleConfig.font_weight_heading),
        font_size_root=str(font_size_root),
        font_size_prose=str(font_size_prose),
        font_size_h1=str(font_size_h1),
        font_size_h2=str(font_size_h2),
        font_size_h3=str(font_size_h3),
        font_size_h4=str(font_size_h4),
        font_size_page_title=str(font_size_page_title),
        font_size_post_title=str(font_size_post_title),
        font_size_home_h2=str(font_size_home_h2),
        font_size_section_h2=str(font_size_section_h2),
        font_size_bibliography_h2=str(font_size_bibliography_h2),
        color_bg=str(color_bg),
        color_text=str(color_text),
        color_text_muted=str(color_text_muted),
        color_accent=str(color_accent),
        color_link=color_link,
        color_link_hover=color_link_hover,
        color_border=str(color_border),
        color_code_bg=str(color_code_bg),
        color_bg_dark=str(color_bg_dark),
        color_text_dark=str(color_text_dark),
        color_text_muted_dark=str(color_text_muted_dark),
        color_accent_dark=str(color_accent_dark),
        color_link_dark=color_link_dark,
        color_link_hover_dark=color_link_hover_dark,
        color_border_dark=str(color_border_dark),
        color_code_bg_dark=str(color_code_bg_dark),
    )


def load_config(path: str = "config.yaml") -> Config:
    """
    Load and validate configuration from YAML file.

    Args:
        path: Path to config.yaml file

    Returns:
        Config object with validated configuration

    Raises:
        ConfigError: If config is missing or invalid
    """
    if not Path(path).exists():
        raise ConfigError(
            f"Configuration file not found: {path}\n"
            f"Expected location: {Path(path).absolute()}"
        )

    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in config file: {e}")

    if not data:
        raise ConfigError("Configuration file is empty")

    # Validate required sections
    if 'site' not in data:
        raise ConfigError("Missing required section: 'site'")

    # Validate required site fields
    site_data = data['site']
    required_site_fields = ['title', 'description', 'base_url', 'author']
    for field_name in required_site_fields:
        if field_name not in site_data:
            raise ConfigError(f"Missing required field in 'site': '{field_name}'")

    # Parse site config
    site = SiteConfig(
        title=site_data['title'],
        description=site_data['description'],
        base_url=site_data['base_url'].rstrip('/'),  # Remove trailing slash
        author=site_data['author'],
        links=site_data.get('links', []) or [],
        author_highlight=site_data.get('author_highlight'),
    )

    # Parse navigation
    nav_data = data.get('nav', [])
    nav = [NavItem(label=item['label'], url=item['url']) for item in nav_data]

    # Parse style config with defaults
    style_data = data.get('style', {})
    style = _parse_style(style_data)

    # Parse math flag
    math = data.get('math', True)

    # Parse home config
    home = HomeConfig(**(data.get('home', {}) or {}))

    # Parse feature flags
    features = FeatureConfig(**(data.get('features', {}) or {}))

    return Config(site=site, nav=nav, style=style, math=math, home=home, features=features)
