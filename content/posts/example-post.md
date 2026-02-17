---
title: "Example Writing Post"
subtitle: "A demonstration of the static site generator features"
date: 2024-01-15
post: true
tags: [example, tutorial]
draft: false
toc: true
---

# Introduction

This is an example writing post demonstrating the various markdown features supported by the static site generator.

## Wiki Links

You can link to other pages using wiki-style links: [[about]] or with custom text: [[research|my research]].

## Callouts

The generator supports various types of callouts:

> [!note] This is a note
> Callouts are great for highlighting important information.

> [!warning] Warning
> This is a warning callout with important information.

> [!tip] Pro Tip
> Use callouts to make your content more engaging and readable.

## Code Blocks

Python code with syntax highlighting:

```python
def fibonacci(n):
    """Generate Fibonacci sequence up to n."""
    a, b = 0, 1
    while a < n:
        print(a, end=' ')
        a, b = b, a + b
    print()

fibonacci(100)
```

JavaScript example:

```javascript
const greet = (name) => {
  console.log(`Hello, ${name}!`);
};

greet("World");
```

## Mathematics

The site supports LaTeX math via MathJax.

Inline math: The equation $E = mc^2$ is famous.

Display math:

$$
\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
$$

Another example:

$$
\nabla \times \mathbf{E} = -\frac{\partial \mathbf{B}}{\partial t}
$$

## Images

![narrow: Example image caption - images are automatically styled as wide figures](example.svg)

Images placed in `assets/images/` will be automatically resolved.

## Lists

Unordered list:
- Item 1
- Item 2
  - Nested item
  - Another nested item
- Item 3

Ordered list:
1. First step
2. Second step
3. Third step

## Quotes

> This is a blockquote. It can span multiple lines and is useful for highlighting important text or quotations from other sources.
>
> — Author Name

## Tables

| Feature | Supported | Notes |
|---------|-----------|-------|
| Wiki links | ✅ | `\\[\\[page\\]\\]` syntax |
| Callouts | ✅ | Obsidian-style |
| Math | ✅ | MathJax |
| Code | ✅ | Pygments highlighting |
| Dark mode | ✅ | Automatic |

## Conclusion

This static site generator provides a powerful yet simple way to create academic and personal websites from markdown files. Check out the [[research]] page for more examples!

