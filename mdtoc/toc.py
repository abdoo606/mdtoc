"""Markdown heading extraction and slug generation (GitHub-compatible)."""

from __future__ import annotations

import re
from dataclasses import dataclass

FENCE = re.compile(r"^\s{0,3}(```|~~~)")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
INLINE_CODE = re.compile(r"`[^`]*`")
LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


@dataclass(slots=True, frozen=True)
class Heading:
    level: int
    text: str
    line: int
    slug: str


def slugify(text: str) -> str:
    """Approximates GitHub's anchor algorithm."""
    text = INLINE_CODE.sub(lambda m: m.group(0).strip("`"), text)
    text = LINK.sub(lambda m: m.group(1), text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\s\u0600-\u06FF-]", "", text)  # keep letters incl. Arabic, digits, dash
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")


def extract_headings(markdown: str, *, min_level: int = 1, max_level: int = 6) -> list[Heading]:
    """Skips headings inside fenced code blocks and dedupes slugs like GitHub does."""
    headings: list[Heading] = []
    seen: dict[str, int] = {}
    in_fence = False
    for number, raw in enumerate(markdown.splitlines(), start=1):
        if FENCE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING.match(raw)
        if not match:
            continue
        level = len(match.group(1))
        if not (min_level <= level <= max_level):
            continue
        text = match.group(2).strip()
        base = slugify(text)
        count = seen.get(base, 0)
        seen[base] = count + 1
        slug = base if count == 0 else f"{base}-{count}"
        headings.append(Heading(level, text, number, slug))
    return headings


def render_toc(headings: list[Heading], *, min_level: int = 2, bullet: str = "-", indent: str = "  ") -> str:
    usable = [h for h in headings if h.level >= min_level]
    if not usable:
        return ""
    base = min(h.level for h in usable)
    lines = []
    for h in usable:
        depth = h.level - base
        lines.append(f"{indent * depth}{bullet} [{h.text}](#{h.slug})")
    return "\n".join(lines)


def inject_toc(markdown: str, toc: str, *, marker: str = "<!-- toc -->") -> str:
    """Replaces the block between two marker comments, or inserts after the first H1."""
    if markdown.count(marker) >= 2:
        start = markdown.index(marker) + len(marker)
        end = markdown.index(marker, start)
        return markdown[:start] + "\n" + toc + "\n" + markdown[end:]
    block = f"{marker}\n{toc}\n{marker}\n"
    match = HEADING.match(markdown.splitlines()[0]) if markdown.strip() else None
    if match and len(match.group(1)) == 1:
        first_newline = markdown.index("\n") + 1
        return markdown[:first_newline] + "\n" + block + markdown[first_newline:]
    return block + "\n" + markdown
