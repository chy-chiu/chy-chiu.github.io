"""
Configuration loading and validation
"""

import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Any
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


@dataclass
class StyleConfig:
    font_body: str = "IBM Plex Sans"
    font_mono: str = "IBM Plex Mono"
    font_heading: str = "IBM Plex Sans"

    color_bg: str = "#ffffff"
    color_text: str = "#1a1a1a"
    color_text_muted: str = "#666666"
    color_accent: str = "#0066cc"
    color_border: str = "#e0e0e0"
    color_code_bg: str = "#f5f5f5"

    color_bg_dark: str = "#1a1a1a"
    color_text_dark: str = "#e0e0e0"
    color_text_muted_dark: str = "#999999"
    color_accent_dark: str = "#66b3ff"
    color_border_dark: str = "#333333"
    color_code_bg_dark: str = "#2d2d2d"


@dataclass
class Config:
    site: SiteConfig
    nav: List[NavItem]
    style: StyleConfig
    math: bool = True


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
        author=site_data['author']
    )

    # Parse navigation
    nav_data = data.get('nav', [])
    nav = [NavItem(label=item['label'], url=item['url']) for item in nav_data]

    # Parse style config with defaults
    style_data = data.get('style', {})
    style = StyleConfig(**style_data)

    # Parse math flag
    math = data.get('math', True)

    return Config(site=site, nav=nav, style=style, math=math)
