"""Validate local Markdown links and in-document anchors."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .toc import LINK, Heading, extract_headings, slugify


@dataclass(slots=True, frozen=True)
class LinkIssue:
    line: int
    target: str
    reason: str

    def __str__(self) -> str:
        return f"line {self.line}: {self.target} -> {self.reason}"


def check_links(markdown: str, base_dir: Path, headings: list[Heading] | None = None) -> list[LinkIssue]:
    anchors = {h.slug for h in (headings if headings is not None else extract_headings(markdown))}
    issues: list[LinkIssue] = []
    in_fence = False
    for number, raw in enumerate(markdown.splitlines(), start=1):
        if raw.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for _, target in LINK.findall(raw):
            target = target.strip()
            if target.startswith(("http://", "https://", "mailto:", "tel:")):
                continue
            if target.startswith("#"):
                if slugify(target[1:]) not in anchors:
                    issues.append(LinkIssue(number, target, "anchor not found in this document"))
                continue
            path_part, _, fragment = target.partition("#")
            candidate = (base_dir / path_part.split("?")[0]).resolve()
            if not candidate.exists():
                issues.append(LinkIssue(number, target, "file does not exist"))
            elif fragment and candidate.suffix == ".md":
                other = candidate.read_text(encoding="utf-8", errors="replace")
                if slugify(fragment) not in {h.slug for h in extract_headings(other)}:
                    issues.append(LinkIssue(number, target, "anchor not found in target file"))
    return issues
