---
title: "Example Project"
description: "A demonstration of the project card feature"
image: "example.svg"
links:
  - label: "Paper"
    url: "https://arxiv.org/abs/example"
  - label: "Code"
    url: "https://github.com/yourusername/project"
  - label: "Demo"
    url: "https://example.com/demo"
order: 1
---

# Project Details

This is an example project card. Projects are displayed on the research page as cards with optional images and links.

## Features

- Automatic card layout on research page
- Support for multiple links (paper, code, demo, etc.)
- Optional images for visual appeal
- Manual ordering via the `order` field

## Usage

Create project markdown files in `content/projects/` with frontmatter specifying the title, description, optional image, and links.

Projects are sorted by the `order` field (ascending), so lower numbers appear first.
