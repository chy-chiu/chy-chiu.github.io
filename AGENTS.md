# AGENTS.md — Static Site Generator Specification

## Overview

Build a Python-based static site generator that converts Obsidian-flavored markdown files into a minimalist, Distill.pub-inspired academic website. The generator should be a single-command build tool with clean, maintainable code.

**Design Philosophy:**
- Bear Blog minimalism (fast, no bloat, readable)
- Distill.pub richness (typography, wide figures, hover citations)
- Obsidian compatibility (wiki links, callouts, YAML frontmatter)
- Minimal JavaScript (only dark mode toggle + MathJax)

---

## Project Structure

Generate the following directory structure:

```
generator/
├── build.py                    # Main entry point, CLI
├── config.yaml                 # Site configuration
├── requirements.txt            # Python dependencies
├── README.md                   # Usage documentation
│
├── generator/                        # Python package
│   ├── __init__.py
│   ├── config.py               # Config loading and validation
│   ├── content.py              # Content loading and parsing
│   ├── markdown_ext.py         # Custom markdown transformations
│   ├── citations.py            # BibTeX parsing and citation rendering
│   ├── templates.py            # Jinja2 template management
│   ├── builder.py              # Main build orchestration
│   └── utils.py                # Slugify, file ops, logging
│
├── content/                    # User content (example/scaffold)
│   ├── about.md
│   ├── research.md
│   ├── publications.bib
│   ├── projects/
│   │   └── .gitkeep
│   ├── writing/
│   │   └── .gitkeep
│   └── notes/
│       └── .gitkeep
│
├── assets/                     # User assets
│   └── images/
│       └── .gitkeep
│
├── templates/
│   ├── base.html
│   ├── page.html               # Generic static page (about, research)
│   ├── research.html           # Research page with publications + projects
│   ├── post_index.html         # List view for writing/notes
│   ├── post.html               # Individual post view
│   ├── tag_index.html          # All tags listing
│   ├── tag_page.html           # Single tag's posts
│   └── partials/
│       ├── nav.html
│       ├── head.html
│       ├── footer.html
│       ├── toc.html
│       ├── post_card.html
│       ├── project_card.html
│       ├── publication.html
│       └── citation_tooltip.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── theme.js
│
└── output/                     # Generated site (gitignored)
    └── .gitkeep
```

---

## Configuration

### config.yaml Schema

```yaml
site:
  title: "Site Title"
  description: "Site description for meta tags"
  base_url: "https://username.github.io"  # No trailing slash
  author: "Author Name"

nav:
  - label: "About"
    url: "/"
  - label: "Research"
    url: "/research/"
  - label: "Writing"
    url: "/writing/"
  - label: "Notes"
    url: "/notes/"

style:
  # Fonts (loaded from Google Fonts)
  font_body: "IBM Plex Sans"
  font_mono: "IBM Plex Mono"
  font_heading: "IBM Plex Sans"

  # Light mode colors
  color_bg: "#ffffff"
  color_text: "#1a1a1a"
  color_text_muted: "#666666"
  color_accent: "#0066cc"
  color_border: "#e0e0e0"
  color_code_bg: "#f5f5f5"

  # Dark mode colors
  color_bg_dark: "#1a1a1a"
  color_text_dark: "#e0e0e0"
  color_text_muted_dark: "#999999"
  color_accent_dark: "#66b3ff"
  color_border_dark: "#333333"
  color_code_bg_dark: "#2d2d2d"

math: true  # Whether to load MathJax
```

### config.py Implementation

- Load YAML file with PyYAML
- Validate all required fields exist
- Provide sensible defaults for optional fields
- Expose as a dataclass or typed dict for IDE support
- Raise clear errors for missing/malformed config

---

## Content Types

### 1. Static Pages (about.md, research.md)

**Location:** `content/about.md`, `content/research.md`

**Frontmatter:**
```yaml
---
title: "About"
---
```

**Behavior:**
- `about.md` renders to `/index.html` (homepage)
- `research.md` renders to `/research/index.html`
- Research page additionally includes publications and project cards

### 2. Writing Posts

**Location:** `content/writing/*.md`

**Frontmatter (required fields marked with *):**
```yaml
---
title: "Post Title"*
subtitle: "Optional subtitle"
date: 2024-01-15*          # YYYY-MM-DD format
tags: [tag-one, tag-two]   # List of strings, optional
draft: false               # Default: false
toc: true                  # Default: false
---
```

**Behavior:**
- Renders to `/writing/{slug}/index.html`
- Slug derived from title: "My Post Title" → "my-post-title"
- Slugify rules: lowercase, replace spaces with hyphens, remove special characters, collapse multiple hyphens
- Listed on `/writing/index.html` sorted by date descending
- Posts with `draft: true` excluded from build unless `--drafts` flag passed

### 3. Notes

**Location:** `content/notes/*.md`

**Frontmatter:** Same schema as Writing

**Behavior:**
- Renders to `/notes/{slug}/index.html`
- Listed on `/notes/index.html` sorted by date descending
- Identical processing to Writing, just different section

### 4. Projects

**Location:** `content/projects/*.md`

**Frontmatter:**
```yaml
---
title: "Project Name"*
description: "One-line description"*
image: "project-image.png"         # Relative to assets/images/
links:
  - label: "Paper"
    url: "https://arxiv.org/..."
  - label: "Code"
    url: "https://github.com/..."
order: 1                           # Manual sort order (ascending)
---

Optional longer markdown body for project description.
```

**Behavior:**
- Rendered as cards on the Research page
- Sorted by `order` field ascending
- No individual project pages (cards only)

### 5. Publications (BibTeX)

**Location:** `content/publications.bib`

**Supported BibTeX fields:**
- `author` (required)
- `title` (required)
- `year` (required)
- `booktitle` OR `journal` (venue)
- `url` (link to paper)
- `code` (custom field: link to code repository)
- `abstract` (for hover/tooltip if desired)

**Behavior:**
- Parsed into structured data
- Rendered on Research page grouped by year (descending)
- Each entry shows: Author list, "Title," Venue, Year, [Paper] [Code] links
- Citation keys (e.g., `smith2024`) used for in-text citations

---

## Markdown Processing

Use `markdown-it-py` as the base parser. Implement custom processing in this order:

### Processing Pipeline

1. **Extract frontmatter** — Parse YAML between `---` delimiters
2. **Wiki links** — Transform before markdown parsing
3. **Citations** — Transform `[@key]` syntax
4. **Parse markdown** — markdown-it-py with plugins
5. **Post-process HTML** — Callouts, figure captions, wide images

### Wiki Links

**Syntax:**
- `[[page-title]]` — Link using page title as display text
- `[[page-title|display text]]` — Link with custom display text

**Resolution:**
1. Build registry of all pages: `{slugified-title: {url, title, section}}`
2. When encountering `[[text]]`:
   - Slugify `text`
   - Look up in registry
   - If found: render as `<a href="{url}">{display}</a>`
   - If not found: render as `<span class="broken-link">{text}</span>` and emit warning to console

**Implementation:**
- Use regex to find wiki links before markdown parsing
- Pattern: `\[\[([^\]|]+)(?:\|([^\]]+))?\]\]`
- Replace with either resolved link or broken-link span

### In-Text Citations

**Syntax:** `[@citation-key]` or `[@key1; @key2]` for multiple

**Rendering:**
- Single: `<cite class="citation" data-keys="key1">[1]</cite>`
- Multiple: `<cite class="citation" data-keys="key1,key2">[1, 2]</cite>`
- Number assigned based on order of first appearance in document
- At end of document, render bibliography section with full citations
- Tooltip on hover shows full citation (CSS-only using `::after` and `attr()`, or minimal JS)

**Bibliography format:**
```html
<section class="bibliography">
  <h2>References</h2>
  <ol class="references">
    <li id="ref-1">Author. "Title." <em>Venue</em>, Year.</li>
  </ol>
</section>
```

### Callouts/Admonitions

**Obsidian Syntax:**
```markdown
> [!note] Optional Title
> Callout content here
> Can be multiple lines
```

**Supported types:** note, warning, tip, important, caution, info

**Output HTML:**
```html
<aside class="callout callout-note">
  <div class="callout-title">
    <span class="callout-icon"></span>
    <span class="callout-title-text">Optional Title</span>
  </div>
  <div class="callout-content">
    <p>Callout content here</p>
    <p>Can be multiple lines</p>
  </div>
</aside>
```

**Implementation:**
- Post-process the HTML output
- Detect blockquotes starting with `[!type]`
- Parse title (if present) and type
- Replace blockquote with aside structure

### Images and Figures

**Input syntax:** `![Caption text](path/to/image.png)`

**Output HTML:**
```html
<figure class="image-figure">
  <img src="/assets/images/image.png" alt="Caption text" loading="lazy">
  <figcaption>Caption text</figcaption>
</figure>
```

**Width constraint CSS:**
- All figures are "wide" by default (break out of text column)
- Max width: `min(100vw - 2rem, 1.5 * min(natural-height, natural-width))`
- Since we can't know natural dimensions at build time, use CSS:
  - Set max-width to ~120% of text column (e.g., if text is 680px, figure max is 816px)
  - Use `max-width: min(calc(100vw - 2rem), 900px)` as practical approximation
  - Center with negative margins

**Path resolution:**
- If path starts with `/`, use as-is
- Otherwise, prepend `/assets/images/`

### Code Blocks

**Input:**
```markdown
```python
def hello():
    print("world")
```
```

**Processing:**
- Use Pygments for syntax highlighting
- Generate HTML with inline classes (not inline styles) for theming
- Use Pygments' `HtmlFormatter` with `cssclass="highlight"`

**Output:**
```html
<div class="code-block">
  <div class="code-header">
    <span class="code-language">python</span>
  </div>
  <pre class="highlight"><code>...</code></pre>
</div>
```

**CSS:**
- Generate Pygments CSS for both light and dark themes
- Include in style.css or as separate file

### Math (LaTeX)

**Delimiters:**
- Inline: `$...$`
- Display: `$$...$$`

**Processing:**
- Do NOT process math content — leave delimiters intact for MathJax
- Ensure markdown parser doesn't mangle content inside delimiters
- Configure markdown-it-py to treat `$` appropriately (may need escaping logic)

**MathJax Configuration:**
```html
<script>
  MathJax = {
    tex: {
      inlineMath: [['$', '$']],
      displayMath: [['$$', '$$']]
    }
  };
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>
```

### Table of Contents

**Trigger:** `toc: true` in frontmatter

**Generation:**
- Extract all headings (h2, h3, h4) from parsed HTML
- Generate nested list structure
- Add `id` attributes to headings if not present (slugified heading text)

**Output:**
```html
<nav class="toc">
  <h2 class="toc-title">Contents</h2>
  <ol class="toc-list">
    <li><a href="#heading-one">Heading One</a>
      <ol>
        <li><a href="#subheading">Subheading</a></li>
      </ol>
    </li>
  </ol>
</nav>
```

**Placement:** Rendered at top of article content, after title/subtitle/meta

---

## Templates

Use Jinja2. All templates extend `base.html`.

### base.html

```html
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  {% include "partials/head.html" %}
</head>
<body>
  {% include "partials/nav.html" %}

  <main class="main">
    {% block content %}{% endblock %}
  </main>

  {% include "partials/footer.html" %}

  {% if config.math %}
  <!-- MathJax config here -->
  {% endif %}

  <script src="/static/js/theme.js"></script>
</body>
</html>
```

### partials/head.html

Include:
- Meta charset, viewport
- Title: `{{ page.title }} | {{ config.site.title }}`
- Meta description
- Open Graph tags (og:title, og:description, og:type)
- Google Fonts link for configured fonts
- CSS link
- Favicon link (if exists)
- Canonical URL

### partials/nav.html

```html
<header class="header">
  <nav class="nav">
    <a href="/" class="nav-logo">{{ config.site.title }}</a>
    <ul class="nav-links">
      {% for item in config.nav %}
      <li><a href="{{ item.url }}" {% if current_url == item.url %}class="active"{% endif %}>{{ item.label }}</a></li>
      {% endfor %}
    </ul>
    <button class="theme-toggle" aria-label="Toggle dark mode">
      <span class="theme-icon"></span>
    </button>
  </nav>
</header>
```

### partials/footer.html

Simple footer with copyright year and author name.

### page.html (About)

```html
{% extends "base.html" %}
{% block content %}
<article class="page">
  <header class="page-header">
    <h1>{{ page.title }}</h1>
  </header>
  <div class="page-content prose">
    {{ page.content | safe }}
  </div>
</article>
{% endblock %}
```

### research.html

```html
{% extends "base.html" %}
{% block content %}
<article class="page research">
  <header class="page-header">
    <h1>{{ page.title }}</h1>
  </header>

  <div class="page-content prose">
    {{ page.content | safe }}
  </div>

  {% if projects %}
  <section class="projects-section">
    <h2>Projects</h2>
    <div class="projects-grid">
      {% for project in projects %}
      {% include "partials/project_card.html" %}
      {% endfor %}
    </div>
  </section>
  {% endif %}

  {% if publications %}
  <section class="publications-section">
    <h2>Publications</h2>
    {% for year, pubs in publications | groupby('year') | sort(reverse=true) %}
    <div class="pub-year-group">
      <h3 class="pub-year">{{ year }}</h3>
      <ul class="pub-list">
        {% for pub in pubs %}
        {% include "partials/publication.html" %}
        {% endfor %}
      </ul>
    </div>
    {% endfor %}
  </section>
  {% endif %}
</article>
{% endblock %}
```

### post_index.html (Writing/Notes listing)

```html
{% extends "base.html" %}
{% block content %}
<div class="post-index">
  <header class="section-header">
    <h1>{{ section_title }}</h1>
  </header>

  <ul class="post-list">
    {% for post in posts %}
    <li class="post-item">
      <article>
        <a href="{{ post.url }}" class="post-link">
          <h2 class="post-title">{{ post.title }}</h2>
          {% if post.subtitle %}
          <p class="post-subtitle">{{ post.subtitle }}</p>
          {% endif %}
        </a>
        <div class="post-meta">
          <time datetime="{{ post.date.isoformat() }}">{{ post.date.strftime('%B %d, %Y') }}</time>
          {% if post.tags %}
          <span class="post-tags">
            {% for tag in post.tags %}
            <a href="/tags/{{ tag | slugify }}/" class="tag">{{ tag }}</a>
            {% endfor %}
          </span>
          {% endif %}
        </div>
      </article>
    </li>
    {% endfor %}
  </ul>
</div>
{% endblock %}
```

### post.html (Individual writing/note)

```html
{% extends "base.html" %}
{% block content %}
<article class="post">
  <header class="post-header">
    <h1 class="post-title">{{ post.title }}</h1>
    {% if post.subtitle %}
    <p class="post-subtitle">{{ post.subtitle }}</p>
    {% endif %}
    <div class="post-meta">
      <time datetime="{{ post.date.isoformat() }}">{{ post.date.strftime('%B %d, %Y') }}</time>
      {% if post.tags %}
      <span class="post-tags">
        {% for tag in post.tags %}
        <a href="/tags/{{ tag | slugify }}/" class="tag">{{ tag }}</a>
        {% endfor %}
      </span>
      {% endif %}
    </div>
  </header>

  {% if post.toc and toc_html %}
  {{ toc_html | safe }}
  {% endif %}

  <div class="post-content prose">
    {{ post.content | safe }}
  </div>

  {% if post.bibliography %}
  {{ post.bibliography | safe }}
  {% endif %}
</article>
{% endblock %}
```

### tag_index.html

```html
{% extends "base.html" %}
{% block content %}
<div class="tag-index">
  <header class="section-header">
    <h1>Tags</h1>
  </header>

  <ul class="tag-cloud">
    {% for tag, posts in tags.items() | sort %}
    <li>
      <a href="/tags/{{ tag | slugify }}/" class="tag">
        {{ tag }} <span class="tag-count">({{ posts | length }})</span>
      </a>
    </li>
    {% endfor %}
  </ul>
</div>
{% endblock %}
```

### tag_page.html

```html
{% extends "base.html" %}
{% block content %}
<div class="tag-page">
  <header class="section-header">
    <h1>Tagged: {{ tag }}</h1>
    <p class="tag-count">{{ posts | length }} post{% if posts | length != 1 %}s{% endif %}</p>
  </header>

  <ul class="post-list">
    {% for post in posts %}
    <!-- Same structure as post_index.html post items -->
    {% endfor %}
  </ul>
</div>
{% endblock %}
```

### partials/project_card.html

```html
<article class="project-card">
  {% if project.image %}
  <div class="project-image">
    <img src="/assets/images/{{ project.image }}" alt="{{ project.title }}" loading="lazy">
  </div>
  {% endif %}
  <div class="project-info">
    <h3 class="project-title">{{ project.title }}</h3>
    <p class="project-description">{{ project.description }}</p>
    {% if project.links %}
    <div class="project-links">
      {% for link in project.links %}
      <a href="{{ link.url }}" class="project-link">{{ link.label }}</a>
      {% endfor %}
    </div>
    {% endif %}
  </div>
</article>
```

### partials/publication.html

```html
<li class="publication">
  <span class="pub-authors">{{ pub.authors | join(', ') }}</span>.
  "<span class="pub-title">{{ pub.title }}</span>."
  <em class="pub-venue">{{ pub.venue }}</em>, {{ pub.year }}.
  {% if pub.url or pub.code %}
  <span class="pub-links">
    {% if pub.url %}<a href="{{ pub.url }}">[Paper]</a>{% endif %}
    {% if pub.code %}<a href="{{ pub.code }}">[Code]</a>{% endif %}
  </span>
  {% endif %}
</li>
```

---

## CSS Specification

### Design Tokens (CSS Custom Properties)

```css
:root {
  /* Typography */
  --font-body: 'IBM Plex Sans', -apple-system, sans-serif;
  --font-mono: 'IBM Plex Mono', monospace;
  --font-heading: 'IBM Plex Sans', sans-serif;

  /* Sizing */
  --content-width: 680px;
  --wide-width: 900px;
  --full-width: 100%;

  /* Spacing scale */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 2rem;
  --space-xl: 4rem;

  /* Colors - Light (default) */
  --color-bg: #ffffff;
  --color-text: #1a1a1a;
  --color-text-muted: #666666;
  --color-accent: #0066cc;
  --color-border: #e0e0e0;
  --color-code-bg: #f5f5f5;
}

[data-theme="dark"] {
  --color-bg: #1a1a1a;
  --color-text: #e0e0e0;
  --color-text-muted: #999999;
  --color-accent: #66b3ff;
  --color-border: #333333;
  --color-code-bg: #2d2d2d;
}
```

### Layout

- Body: centered, max-width content
- Main content column: 680px max-width, centered with auto margins
- Wide elements (figures): 900px max-width, centered, break out of text column using negative margins
- Nav: full width, content constrained to same max-width as body
- Responsive: single column, reduce margins on mobile

### Typography

```css
.prose {
  font-size: 1.125rem;      /* 18px */
  line-height: 1.7;

  h1 { font-size: 2.25rem; margin-top: 3rem; margin-bottom: 1rem; }
  h2 { font-size: 1.75rem; margin-top: 2.5rem; margin-bottom: 0.75rem; }
  h3 { font-size: 1.375rem; margin-top: 2rem; margin-bottom: 0.5rem; }

  p { margin-bottom: 1.5rem; }

  a { color: var(--color-accent); text-decoration: underline; }
  a:hover { text-decoration: none; }

  code {
    font-family: var(--font-mono);
    font-size: 0.9em;
    background: var(--color-code-bg);
    padding: 0.1em 0.3em;
    border-radius: 3px;
  }

  blockquote {
    border-left: 3px solid var(--color-border);
    padding-left: 1rem;
    margin-left: 0;
    color: var(--color-text-muted);
  }
}
```

### Navigation

- Horizontal layout: logo left, links center/right, theme toggle far right
- Mobile: hamburger menu or simple stacked layout
- Active link styling (underline or bold)
- Sticky/fixed optional (can be static for simplicity)

### Post List

- Each post: title (linked), subtitle below (muted), date and tags on separate line
- Clear visual separation between posts (spacing, not heavy borders)
- Tags: small, pill-shaped, muted color, hover state

### Figures

```css
.image-figure {
  margin: var(--space-lg) 0;

  /* Break out of text column */
  width: var(--wide-width);
  max-width: calc(100vw - 2rem);
  margin-left: calc((var(--content-width) - var(--wide-width)) / 2);

  img {
    width: 100%;
    height: auto;
    display: block;
  }

  figcaption {
    margin-top: var(--space-sm);
    font-size: 0.9rem;
    color: var(--color-text-muted);
    text-align: center;
  }
}

/* On narrow screens, just full width */
@media (max-width: 900px) {
  .image-figure {
    width: 100%;
    margin-left: 0;
  }
}
```

### Callouts

```css
.callout {
  margin: var(--space-lg) 0;
  padding: var(--space-md);
  border-radius: 4px;
  border-left: 4px solid;
}

.callout-note {
  background: rgba(0, 102, 204, 0.1);
  border-color: #0066cc;
}

.callout-warning {
  background: rgba(255, 153, 0, 0.1);
  border-color: #ff9900;
}

.callout-tip {
  background: rgba(0, 153, 51, 0.1);
  border-color: #009933;
}

/* Add more callout types... */

.callout-title {
  font-weight: 600;
  margin-bottom: var(--space-sm);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.callout-content p:last-child {
  margin-bottom: 0;
}
```

### Code Blocks

```css
.code-block {
  margin: var(--space-lg) 0;
  border-radius: 6px;
  overflow: hidden;
  background: var(--color-code-bg);
}

.code-header {
  padding: var(--space-sm) var(--space-md);
  background: rgba(0, 0, 0, 0.1);
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.code-block pre {
  margin: 0;
  padding: var(--space-md);
  overflow-x: auto;
}

.code-block code {
  background: none;
  padding: 0;
}

/* Include Pygments theme CSS here */
```

### Citations

```css
.citation {
  color: var(--color-accent);
  cursor: help;
  position: relative;
}

.citation:hover::after {
  content: attr(data-citation);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: var(--color-text);
  color: var(--color-bg);
  padding: var(--space-sm) var(--space-md);
  border-radius: 4px;
  font-size: 0.85rem;
  white-space: nowrap;
  max-width: 400px;
  white-space: normal;
  z-index: 100;
}

.bibliography {
  margin-top: var(--space-xl);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border);
}

.references {
  font-size: 0.95rem;
  padding-left: 1.5rem;
}

.references li {
  margin-bottom: var(--space-sm);
}
```

### Table of Contents

```css
.toc {
  background: var(--color-code-bg);
  padding: var(--space-md);
  border-radius: 6px;
  margin-bottom: var(--space-xl);
}

.toc-title {
  font-size: 1rem;
  margin-bottom: var(--space-sm);
}

.toc-list {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.95rem;
}

.toc-list ol {
  margin-top: var(--space-xs);
  padding-left: 1rem;
}

.toc-list a {
  color: var(--color-text);
  text-decoration: none;
}

.toc-list a:hover {
  color: var(--color-accent);
}
```

### Theme Toggle

```css
.theme-toggle {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 50%;
  width: 2.5rem;
  height: 2.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.theme-icon::before {
  content: "☀️";  /* Or use SVG icons */
}

[data-theme="dark"] .theme-icon::before {
  content: "🌙";
}
```

### Broken Links

```css
.broken-link {
  color: var(--color-text-muted);
  background: rgba(255, 0, 0, 0.1);
  padding: 0.1em 0.2em;
  border-radius: 2px;
}
```

### Project Cards

```css
.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--space-lg);
  margin-top: var(--space-lg);
}

.project-card {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
}

.project-image img {
  width: 100%;
  height: 180px;
  object-fit: cover;
}

.project-info {
  padding: var(--space-md);
}

.project-title {
  margin: 0 0 var(--space-sm);
  font-size: 1.125rem;
}

.project-description {
  color: var(--color-text-muted);
  font-size: 0.95rem;
  margin-bottom: var(--space-md);
}

.project-links {
  display: flex;
  gap: var(--space-sm);
}

.project-link {
  font-size: 0.9rem;
}
```

### Publications

```css
.publications-section {
  margin-top: var(--space-xl);
}

.pub-year-group {
  margin-bottom: var(--space-lg);
}

.pub-year {
  font-size: 1.25rem;
  color: var(--color-text-muted);
  margin-bottom: var(--space-md);
}

.pub-list {
  list-style: none;
  padding: 0;
}

.publication {
  margin-bottom: var(--space-md);
  line-height: 1.5;
}

.pub-title {
  font-weight: 500;
}

.pub-links a {
  font-size: 0.9rem;
  margin-right: var(--space-sm);
}
```

---

## JavaScript

### theme.js (~15 lines)

```javascript
(function() {
  const toggle = document.querySelector('.theme-toggle');
  const html = document.documentElement;

  // Check saved preference or system preference
  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const initial = saved || (prefersDark ? 'dark' : 'light');
  html.setAttribute('data-theme', initial);

  toggle.addEventListener('click', () => {
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
  });
})();
```

---

## Build CLI

### Usage

```bash
# Build site
python build.py

# Build including drafts
python build.py --drafts

# Clean output directory before build
python build.py --clean

# Development server with live reload (v1.1)
python build.py --serve
```

### build.py Implementation

```python
#!/usr/bin/env python3
import argparse
from ssg.builder import Builder

def main():
    parser = argparse.ArgumentParser(description='Build static site')
    parser.add_argument('--drafts', action='store_true', help='Include draft posts')
    parser.add_argument('--clean', action='store_true', help='Clean output before build')
    parser.add_argument('--serve', action='store_true', help='Start dev server')  # v1.1
    args = parser.parse_args()

    builder = Builder(
        include_drafts=args.drafts,
        clean=args.clean
    )
    builder.build()

    if args.serve:
        builder.serve()  # v1.1

if __name__ == '__main__':
    main()
```

---

## Python Module Specifications

### ssg/config.py

- `load_config(path: str) -> Config` — Load and validate config.yaml
- `Config` dataclass with typed fields
- Raise `ConfigError` with helpful message for missing/invalid fields

### ssg/content.py

- `Page` dataclass: title, subtitle, date, tags, draft, toc, slug, url, raw_content, html_content, section
- `Project` dataclass: title, description, image, links, order, content
- `Publication` dataclass: key, authors, title, venue, year, url, code
- `load_page(path: str, section: str) -> Page`
- `load_project(path: str) -> Project`
- `load_all_content(content_dir: str) -> ContentIndex`
- `ContentIndex` class with:
  - `pages: dict[str, Page]` — slug to page mapping
  - `writing: list[Page]` — sorted by date
  - `notes: list[Page]` — sorted by date
  - `projects: list[Project]` — sorted by order
  - `tags: dict[str, list[Page]]` — tag to pages mapping

### ssg/markdown_ext.py

- `MarkdownProcessor` class:
  - `__init__(page_registry: dict[str, Page], citation_registry: dict[str, Publication])`
  - `process(content: str, extract_toc: bool = False) -> ProcessedContent`
- `ProcessedContent` dataclass: html, toc_html, bibliography_html, warnings
- Internal methods:
  - `_transform_wiki_links(content: str) -> str`
  - `_transform_citations(content: str) -> str`
  - `_parse_markdown(content: str) -> str`
  - `_post_process_callouts(html: str) -> str`
  - `_post_process_figures(html: str) -> str`
  - `_extract_toc(html: str) -> tuple[str, str]` — returns (html_with_ids, toc_html)

### ssg/citations.py

- `load_bibtex(path: str) -> dict[str, Publication]`
- `format_citation(pub: Publication) -> str` — formatted string for bibliography
- `format_inline_citation(pub: Publication) -> str` — short form for tooltips

### ssg/templates.py

- `TemplateEngine` class:
  - `__init__(templates_dir: str, config: Config)`
  - `render(template_name: str, **context) -> str`
  - Auto-includes config in all contexts
  - Custom Jinja2 filters: `slugify`, `date_format`

### ssg/builder.py

- `Builder` class:
  - `__init__(include_drafts: bool = False, clean: bool = False)`
  - `build()` — main orchestration method
  - `_load_all_content()`
  - `_process_all_markdown()`
  - `_render_static_pages()`
  - `_render_writing()`
  - `_render_notes()`
  - `_render_tags()`
  - `_copy_static_assets()`
  - `_write_file(path: str, content: str)`

### ssg/utils.py

- `slugify(text: str) -> str` — title to URL-safe slug
- `ensure_dir(path: str)` — create directory if not exists
- `copy_tree(src: str, dst: str)` — recursive copy
- `get_logger() -> Logger` — configured logging
- `format_date(date: datetime, fmt: str) -> str`

---

## Output Structure

```
output/
├── index.html                    # About page
├── research/
│   └── index.html
├── writing/
│   ├── index.html                # Writing listing
│   └── {slug}/
│       └── index.html            # Individual posts
├── notes/
│   ├── index.html
│   └── {slug}/
│       └── index.html
├── tags/
│   ├── index.html                # All tags
│   └── {tag-slug}/
│       └── index.html            # Tag page
├── assets/
│   └── images/
│       └── ...
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── theme.js
```

---

## Error Handling

1. **Missing frontmatter fields**: Error with filename and missing field name
2. **Invalid date format**: Error with expected format (YYYY-MM-DD)
3. **Broken wiki links**: Warning to console, continue build
4. **Missing BibTeX file**: Warning, skip publications section
5. **Invalid BibTeX entry**: Warning with entry key, skip entry
6. **Missing config file**: Clear error message with expected location
7. **Invalid config YAML**: Parse error with line number

---

## Feature Roadmap

### MVP (v1.0)
- ✓ All core markdown processing
- ✓ Wiki links, tags, callouts
- ✓ Code highlighting, MathJax
- ✓ Figure captions, wide figures
- ✓ Dark mode toggle
- ✓ BibTeX publications list
- ✓ Project cards
- ✓ Table of contents

### v1.1 (Future)
- In-text citations `[@key]`
- Live reload dev server
- RSS feed generation

### v1.2 (Future)
- Client-side search
- Backlinks support
- Margin notes (Distill-style)

# Decisions (captured)

- Homepage is a real landing page: `content/home.md` (title “Hello”) + recent writing + selected papers.
- Homepage markdown content appears above the “Featured/Recent” blocks.
- Separate `/about/` page: `content/about.md` (longer bio, includes CV/contact section).
- Writing and Notes stay separate, but tags aggregate both.
- Homepage recent writing: Writing-only, up to 3, show title/subtitle/date (no excerpt).
- Featured writing can be pinned via post frontmatter (`featured: true`) and/or `home.featured_writing` slugs.
- Homepage papers prefer selected entries; BibTeX can mark selections via `selected = "true"`.
- Homepage papers fallback sorting uses `year` + `month` when present.
- Authors: Research page shows full author list; homepage uses “et al.”; highlight uses `site.author_highlight`.
- Now page: dated entries, past items can be struck through; show “Last updated”.
- Obsidian workflow; drafts previewable locally; slugs from title.
- RSS: Writing-only.
- Sticky nav; mobile hamburger; theme toggle should not have an ugly border.
- Figures: support default wide, plus full-bleed and narrow variants (`![full: ...]`, `![narrow: ...]`); default remains wide.
- Canonical URLs: trailing slash everywhere.
- Per-page `description` frontmatter for meta tags.
- OpenGraph images: auto-generated per post/page.
- Deploy: GitHub Pages, built in CI from artifacts; GitHub Actions pipeline.
- Footer includes `site.links` (CV, email, scholar, github, twitter).

# Open Questions (next)

- [ ] Do you want client-side search in v1.1 (lunr/minisearch) or a build-time search index?
Use minisearch
- [ ] Should tag pages show a split view (Writing vs Notes headings) or a single merged list (current)?
single merged list
- [ ] Do you want a dedicated `/cv/` page eventually (PDF or HTML), or keep it as a section inside About?
no just a pdf is good and keep it inside About
- [ ] Do you want syntax highlighting themes to match light/dark more closely (Pygments CSS generation)?
yes, but make the font smaller for syntax
- [ ] Any posts that should be featured by default once you add real content?
that's for me to fix
- [ ] Do you want a redirect for legacy `/about.md`-style links (if you have old URLs)?
no need for stuff like redirect

## TODOs (Production Readiness)

### For you (site owner)

- [ ] Replace placeholder site metadata in `config.yaml`
- [ ] Fill out `content/home.md` with your real landing copy
- [ ] Fill out `content/about.md` with your full bio (and CV/contact details)
- [ ] Maintain `content/now.md` with a clear “last updated” cadence (weekly/monthly)
- [ ] Add at least 3 real posts in `content/writing/` so homepage highlights are meaningful
- [ ] Add your real `content/publications.bib` (or decide to hide the papers block)
- [ ] Add a favicon (recommended)

### For the agent (next engineering tasks)

- [ ] For the distill style blogposts, the contents table is now on side but the main is a bit too squished. Can you make it (1) on the left side, or (2) if too narrow, make it on top of post?
- [ ] Also Back to top is not to "top" but somewhere in the middle
- [ ] The nav menu - should be (name) (all the spacer) (nav menu items) (dark / light mode). Then hamburger menu should be left of the dark / light mode
- [ ] Given my answers to your questions above make more tasks for yourself
