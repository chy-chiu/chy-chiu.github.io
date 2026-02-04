"""
BibTeX parsing and citation rendering
"""

import bibtexparser
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class Publication:
    key: str
    authors: List[str]
    title: str
    venue: str
    year: str
    url: Optional[str] = None
    code: Optional[str] = None
    abstract: Optional[str] = None


def load_bibtex(path: str) -> Dict[str, Publication]:
    """
    Load and parse BibTeX file.

    Args:
        path: Path to .bib file

    Returns:
        Dictionary mapping citation keys to Publication objects
    """
    if not Path(path).exists():
        return {}

    try:
        with open(path, 'r') as f:
            bib_database = bibtexparser.load(f)
    except Exception as e:
        print(f"Warning: Failed to parse BibTeX file: {e}")
        return {}

    publications = {}

    for entry in bib_database.entries:
        try:
            # Parse authors
            authors_str = entry.get('author', '')
            authors = [a.strip() for a in authors_str.split(' and ')]

            # Get venue (journal or booktitle)
            venue = entry.get('journal') or entry.get('booktitle', '')

            pub = Publication(
                key=entry['ID'],
                authors=authors,
                title=entry.get('title', ''),
                venue=venue,
                year=entry.get('year', ''),
                url=entry.get('url'),
                code=entry.get('code'),
                abstract=entry.get('abstract')
            )

            publications[entry['ID']] = pub
        except KeyError as e:
            print(f"Warning: Skipping invalid BibTeX entry {entry.get('ID', 'unknown')}: missing field {e}")
            continue

    return publications


def format_citation(pub: Publication) -> str:
    """
    Format publication as full citation for bibliography.

    Returns formatted string like:
    "Author1, Author2. "Title." Venue, Year."
    """
    authors_str = ', '.join(pub.authors)
    citation = f'{authors_str}. "{pub.title}." <em>{pub.venue}</em>, {pub.year}.'
    return citation


def format_inline_citation(pub: Publication) -> str:
    """
    Format publication as short citation for tooltips.

    Returns formatted string like:
    "Author et al. (Year)"
    """
    if len(pub.authors) == 0:
        author_str = "Unknown"
    elif len(pub.authors) == 1:
        author_str = pub.authors[0].split(',')[0]  # Get last name
    else:
        author_str = pub.authors[0].split(',')[0] + " et al."

    return f"{author_str} ({pub.year})"
