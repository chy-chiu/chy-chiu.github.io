"""
Content loading and parsing
"""

import os
import yaml
from dataclasses import dataclass, field
from datetime import datetime, date as date_type
from typing import List, Dict, Optional
from pathlib import Path
from .utils import to_url_slug, get_logger


logger = get_logger()

class ContentError(Exception):
    pass


@dataclass
class Page:
    title: str
    slug: str
    url: str
    section: str
    raw_content: str
    date: Optional[datetime] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    draft: bool = False
    toc: bool = False
    updated: Optional[datetime] = None
    word_count: int = 0
    reading_time_minutes: int = 0
    featured: bool = False
    featured_order: int = 0
    html_content: str = ""
    toc_html: str = ""
    bibliography_html: str = ""


@dataclass
class Project:
    title: str
    description: str
    order: int = 0
    image: Optional[str] = None
    links: List[Dict[str, str]] = field(default_factory=list)
    content: str = ""


@dataclass
class ContentIndex:
    pages: Dict[str, Page] = field(default_factory=dict)
    writing: List[Page] = field(default_factory=list)
    notes: List[Page] = field(default_factory=list)
    projects: List[Project] = field(default_factory=list)
    tags: Dict[str, List[Page]] = field(default_factory=dict)


def parse_frontmatter(content: str) -> tuple[Dict, str]:
    """
    Extract YAML frontmatter from markdown content.

    Returns:
        Tuple of (frontmatter_dict, body_content)
    """
    if not content.startswith('---'):
        return {}, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    try:
        frontmatter = yaml.safe_load(parts[1])
        if frontmatter is None:
            frontmatter = {}
        body = parts[2].strip()
        return frontmatter, body
    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse frontmatter: {e}")
        return {}, content


def load_page(path: str, section: str) -> Optional[Page]:
    """
    Load a markdown page from file.

    Args:
        path: Path to markdown file
        section: Section name (writing, notes, about, research)

    Returns:
        Page object or None if loading fails
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        raise ContentError(f"Failed to read {path}: {e}") from e

    frontmatter, body = parse_frontmatter(content)

    # Validate required fields for posts
    if section in ['writing', 'notes']:
        if 'title' not in frontmatter:
            raise ContentError(f"Missing required field 'title' in {path}")
        if 'date' not in frontmatter:
            raise ContentError(f"Missing required field 'date' in {path}")

    # Parse fields
    title = frontmatter.get('title', Path(path).stem)
    slug = to_url_slug(title)

    # Determine URL based on section
    if section == 'home':
        url = '/'
    elif section == 'about':
        url = '/about/'
    elif section == 'research':
        url = '/research/'
    elif section == 'now':
        url = '/now/'
    else:
        url = f'/{section}/{slug}/'

    # Parse date
    date = None
    if 'date' in frontmatter:
        date_value = frontmatter['date']
        if isinstance(date_value, datetime):
            date = date_value
        elif isinstance(date_value, date_type):
            # Convert date to datetime
            date = datetime.combine(date_value, datetime.min.time())
        else:
            try:
                date = datetime.strptime(str(date_value), '%Y-%m-%d')
            except ValueError:
                raise ContentError(f"Invalid date format in {path}, expected YYYY-MM-DD")

    # Parse updated date (static pages)
    updated = None
    if 'updated' in frontmatter:
        updated_value = frontmatter['updated']
        if isinstance(updated_value, datetime):
            updated = updated_value
        elif isinstance(updated_value, date_type):
            updated = datetime.combine(updated_value, datetime.min.time())
        else:
            try:
                updated = datetime.strptime(str(updated_value), '%Y-%m-%d')
            except ValueError:
                raise ContentError(f"Invalid updated date format in {path}, expected YYYY-MM-DD")

    # Simple word count (for reading time feature)
    words = [w for w in body.split() if w.strip()]
    word_count = len(words)
    reading_time_minutes = max(1, (word_count + 199) // 200) if word_count else 0

    page = Page(
        title=title,
        slug=slug,
        url=url,
        section=section,
        raw_content=body,
        date=date,
        subtitle=frontmatter.get('subtitle'),
        description=frontmatter.get('description'),
        tags=frontmatter.get('tags', []),
        draft=frontmatter.get('draft', False),
        toc=frontmatter.get('toc', False),
        updated=updated,
        word_count=word_count,
        reading_time_minutes=reading_time_minutes,
        featured=bool(frontmatter.get('featured', False)),
        featured_order=int(frontmatter.get('featured_order', 0) or 0),
    )

    return page


def load_project(path: str) -> Optional[Project]:
    """
    Load a project from markdown file.

    Args:
        path: Path to project markdown file

    Returns:
        Project object or None if loading fails
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        raise ContentError(f"Failed to read {path}: {e}") from e

    frontmatter, body = parse_frontmatter(content)

    # Validate required fields
    if 'title' not in frontmatter:
        raise ContentError(f"Missing required field 'title' in {path}")
    if 'description' not in frontmatter:
        raise ContentError(f"Missing required field 'description' in {path}")

    project = Project(
        title=frontmatter['title'],
        description=frontmatter['description'],
        order=frontmatter.get('order', 0),
        image=frontmatter.get('image'),
        links=frontmatter.get('links', []),
        content=body
    )

    return project


def load_all_content(content_dir: str = 'content', include_drafts: bool = False) -> ContentIndex:
    """
    Load all content from content directory.

    Args:
        content_dir: Path to content directory
        include_drafts: Whether to include draft posts

    Returns:
        ContentIndex with all loaded content
    """
    index = ContentIndex()

    # Load static pages
    home_path = os.path.join(content_dir, 'home.md')
    about_path = os.path.join(content_dir, 'about.md')
    if os.path.exists(home_path):
        home_page = load_page(home_path, 'home')
        if home_page:
            index.pages[home_page.slug] = home_page

        if os.path.exists(about_path):
            about_page = load_page(about_path, 'about')
            if about_page:
                index.pages[about_page.slug] = about_page
    else:
        if os.path.exists(about_path):
            # Backwards-compatible behavior: about.md is the homepage
            about_page = load_page(about_path, 'home')
            if about_page:
                index.pages[about_page.slug] = about_page

    research_path = os.path.join(content_dir, 'research.md')
    if os.path.exists(research_path):
        research_page = load_page(research_path, 'research')
        if research_page:
            index.pages[research_page.slug] = research_page

    now_path = os.path.join(content_dir, 'now.md')
    if os.path.exists(now_path):
        now_page = load_page(now_path, 'now')
        if now_page:
            index.pages[now_page.slug] = now_page

    # Load writing posts
    writing_dir = os.path.join(content_dir, 'writing')
    if os.path.exists(writing_dir):
        for filename in sorted(os.listdir(writing_dir)):
            if filename.endswith('.md'):
                path = os.path.join(writing_dir, filename)
                page = load_page(path, 'writing')
                if page and (include_drafts or not page.draft):
                    index.pages[page.slug] = page
                    index.writing.append(page)
                    # Index tags
                    for tag in page.tags:
                        if tag not in index.tags:
                            index.tags[tag] = []
                        index.tags[tag].append(page)

    # Sort writing by date descending
    index.writing.sort(key=lambda p: p.date if p.date else datetime.min, reverse=True)

    # Load notes
    notes_dir = os.path.join(content_dir, 'notes')
    if os.path.exists(notes_dir):
        for filename in sorted(os.listdir(notes_dir)):
            if filename.endswith('.md'):
                path = os.path.join(notes_dir, filename)
                page = load_page(path, 'notes')
                if page and (include_drafts or not page.draft):
                    index.pages[page.slug] = page
                    index.notes.append(page)
                    # Index tags
                    for tag in page.tags:
                        if tag not in index.tags:
                            index.tags[tag] = []
                        index.tags[tag].append(page)

    # Sort notes by date descending
    index.notes.sort(key=lambda p: p.date if p.date else datetime.min, reverse=True)

    # Load projects
    projects_dir = os.path.join(content_dir, 'projects')
    if os.path.exists(projects_dir):
        for filename in sorted(os.listdir(projects_dir)):
            if filename.endswith('.md'):
                path = os.path.join(projects_dir, filename)
                project = load_project(path)
                if project:
                    index.projects.append(project)

    # Sort projects by order ascending
    index.projects.sort(key=lambda p: p.order)

    return index
