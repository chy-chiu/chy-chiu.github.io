# Static Site Generator

A Python-based static site generator designed for academic websites, with support for Obsidian-flavored markdown, BibTeX citations, and minimalist design inspired by Bear Blog and Distill.pub.

## Features

- **Obsidian Compatibility**: Wiki links `[[page]]`, callouts, YAML frontmatter
- **Academic Features**: BibTeX publications, project cards, in-text citations
- **Beautiful Typography**: Distill.pub-inspired design with wide figures
- **Dark Mode**: Automatic theme switching with user preference
- **Minimal JavaScript**: Only for theme toggle and MathJax
- **Fast & Simple**: Single command to build entire site

## Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Project Structure

```
.
├── build.py              # Build script
├── config.yaml           # Site configuration
├── content/              # Your markdown content
│   ├── home.md           # Homepage content (landing copy)
│   ├── about.md          # About page (/about/)
│   ├── now.md            # "Now" page
│   ├── research.md       # Research page
│   ├── publications.bib  # BibTeX file
│   ├── projects/         # Project markdown files
│   └── posts/            # Writing + notes (use frontmatter to split)
├── assets/               # Images and media
│   └── images/
├── templates/            # Jinja2 templates
├── static/               # CSS and JavaScript
└── output/               # Generated site (gitignored)
```

## Usage

### Build Site

```bash
python build.py
```

### Serve Locally

```bash
python build.py --serve
```

### Build with Drafts

```bash
python build.py --drafts
```

### Clean Build

```bash
python build.py --clean
```

### Strictness

By default the build fails if the generated site contains broken internal links or missing assets.

```bash
python build.py --no-strict
```

### Deploy

The generated site will be in the `output/` directory. Deploy to:

- **GitHub Pages (recommended)**: Use `.github/workflows/pages.yml` to build and deploy from the `output/` artifact
- **Netlify**: Point to `output/` directory
- **Any static host**: Upload `output/` contents

Generated extras:

- `output/rss.xml` (Writing-only RSS feed; items come from posts with `post: true`)
- `output/sitemap.xml` and `output/robots.txt`
- `output/404.html` (GitHub Pages-friendly)
- `output/og/...` (auto-generated OpenGraph SVG images)
- Year archives: `/writing/YYYY/` and `/notes/YYYY/`

## Content Guide

### Static Pages

**Homepage** (`content/home.md`):
```markdown
---
title: "Hello"
description: "Landing page with recent writing and selected papers."
---

Landing copy here...
```

**About Page** (`content/about.md`):
```markdown
---
title: "About"
description: "Background, interests, and contact."
---

Longer bio + CV/contact here...
```

**Now Page** (`content/now.md`):
```markdown
---
title: "Now"
updated: 2026-02-04
---

What you’re focused on right now...
```

### Featured Writing (Homepage)

Mark a Writing post as featured:

```yaml
featured: true
featured_order: 10
```

Or pin by slug in `config.yaml` under `home.featured_writing`.

### Selected Publications (Homepage)

Mark a BibTeX entry as selected:

```bibtex
selected = "true",
month = "10",
```

If no selected entries exist, the homepage falls back to showing the most recent by `year` + `month`.

**Research Page** (`content/research.md`):
```markdown
---
title: "Research"
---

Research overview...
```

### Writing & Notes (Unified `content/posts/`)

Create markdown files in `content/posts/` and use `post: true` for Writing and `post: false` for Notes:

```markdown
---
title: "My Post Title"
subtitle: "Optional subtitle"
date: 2024-01-15
post: true
tags: [machine-learning, research]
draft: false
toc: true
---

Your content here...
```

### Projects

Create markdown files in `content/projects/`:

```markdown
---
title: "Project Name"
description: "One-line description"
image: "project-image.png"
links:
  - label: "Paper"
    url: "https://arxiv.org/..."
  - label: "Code"
    url: "https://github.com/..."
order: 1
---

Optional longer description...
```

### Publications

Add entries to `content/publications.bib`:

```bibtex
@article{smith2024,
  author = "Smith, John and Doe, Jane",
  title = "A Great Paper",
  journal = "Nature",
  year = "2024",
  url = "https://...",
  code = "https://github.com/..."
}
```

## Markdown Features

### Wiki Links

```markdown
Link to another page: [[page-title]]
Link with custom text: [[page-title|custom text]]
```

### Callouts

```markdown
> [!note] Note Title
> Callout content here

> [!warning] Warning
> This is important!
```

Supported types: `note`, `warning`, `tip`, `important`, `caution`, `info`

### Images with Captions

```markdown
![This is the caption](image.png)
```

### Code Blocks

````markdown
```python
def hello():
    print("world")
```
````

### Math

```markdown
Inline math: $E = mc^2$

Display math:
$$
\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
$$
```

### Citations (v1.1)

```markdown
As shown in recent work [@smith2024], we can...
Multiple citations: [@smith2024; @doe2023]
```

## Configuration

Edit `config.yaml` to customize:

- Site title, description, author
- Navigation menu
- Colors and fonts
- Enable/disable MathJax

## Deployment to GitHub Pages

Recommended (GitHub Actions):

1. Push to `main`
2. In GitHub repo settings: enable Pages with “Source: GitHub Actions”
3. The workflow in `.github/workflows/pages.yml` builds and deploys `output/`

## Tests

```bash
python -m unittest discover -s tests
```

## Roadmap

### v1.0 (Current)
- ✅ Core markdown processing
- ✅ Wiki links, tags, callouts
- ✅ Code highlighting, MathJax
- ✅ Dark mode toggle
- ✅ Publications list
- ✅ RSS feed (Writing)
- ✅ sitemap.xml + robots.txt + 404

### v1.1 (Planned)
- In-text citations `[@key]`
- Live reload dev server

### v1.2 (Future)
- Client-side search
- Backlinks support
- Margin notes

## License

MIT License - feel free to use and modify for your own site.

## Credits

Inspired by:
- [Bear Blog](https://bearblog.dev/) - Minimalist design
- [Distill.pub](https://distill.pub/) - Academic typography
- [Obsidian](https://obsidian.md/) - Markdown extensions
- [al-folio](https://github.com/alshedivat/al-folio) - Academic themes
