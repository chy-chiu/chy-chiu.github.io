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
│   ├── about.md          # Homepage content (also shows recent writing + papers)
│   ├── now.md            # "Now" page
│   ├── research.md       # Research page
│   ├── publications.bib  # BibTeX file
│   ├── projects/         # Project markdown files
│   ├── writing/          # Long-form writing
│   └── notes/            # Short notes
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

### Build with Drafts

```bash
python build.py --drafts
```

### Clean Build

```bash
python build.py --clean
```

### Deploy

The generated site will be in the `output/` directory. Deploy to:

- **GitHub Pages**: Push `output/` to `gh-pages` branch
- **Netlify**: Point to `output/` directory
- **Any static host**: Upload `output/` contents

## Content Guide

### Static Pages

**Homepage** (`content/about.md`):
```markdown
---
title: "About"
---

Your about content here...
```

**Now Page** (`content/now.md`):
```markdown
---
title: "Now"
---

What you’re focused on right now...
```

**Research Page** (`content/research.md`):
```markdown
---
title: "Research"
---

Research overview...
```

### Writing & Notes

Create markdown files in `content/writing/` or `content/notes/`:

```markdown
---
title: "My Post Title"
subtitle: "Optional subtitle"
date: 2024-01-15
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

1. Build the site: `python build.py`
2. Create a `gh-pages` branch
3. Copy contents of `output/` to the branch
4. Push to GitHub
5. Enable GitHub Pages in repository settings

Or use GitHub Actions for automatic deployment (see `.github/workflows/` for examples).

## Roadmap

### v1.0 (Current)
- ✅ Core markdown processing
- ✅ Wiki links, tags, callouts
- ✅ Code highlighting, MathJax
- ✅ Dark mode toggle
- ✅ Publications list

### v1.1 (Planned)
- In-text citations `[@key]`
- Live reload dev server
- RSS feed generation

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
