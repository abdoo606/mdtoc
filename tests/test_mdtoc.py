from __future__ import annotations

import pytest

from mdtoc.linkcheck import check_links
from mdtoc.toc import extract_headings, inject_toc, render_toc, slugify

DOC = """# Title

Some intro.

## Getting Started
### Install
## Getting Started
## الأسئلة الشائعة

```md
## not a heading
```

### `code_span` and [link](http://x.com)
"""


def test_slugify_basics():
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("  multiple   spaces ") == "multiple-spaces"


def test_slugify_keeps_arabic():
    assert slugify("الأسئلة الشائعة") == "الأسئلة-الشائعة"


def test_duplicate_headings_get_suffixes():
    slugs = [h.slug for h in extract_headings(DOC)]
    assert slugs.count("getting-started") == 1
    assert "getting-started-1" in slugs


def test_fenced_code_is_ignored():
    assert "not-a-heading" not in [h.slug for h in extract_headings(DOC)]


def test_inline_code_and_links_in_headings():
    slugs = [h.slug for h in extract_headings(DOC)]
    assert "code_span-and-link" in slugs


def test_levels_are_recorded():
    levels = {h.text: h.level for h in extract_headings(DOC)}
    assert levels["Install"] == 3
    assert levels["Title"] == 1


def test_render_toc_indents_by_depth():
    toc = render_toc(extract_headings(DOC), min_level=2)
    assert "- [Getting Started](#getting-started)" in toc
    assert "  - [Install](#install)" in toc


def test_render_toc_empty_when_only_h1():
    assert render_toc(extract_headings("# Only\n"), min_level=2) == ""


def test_inject_after_h1():
    out = inject_toc("# T\n\nbody\n", "- [a](#a)")
    assert out.startswith("# T\n")
    assert "<!-- toc -->" in out
    assert "- [a](#a)" in out


def test_inject_replaces_marked_block_idempotently():
    once = inject_toc("# T\n\nbody\n", "- [old](#old)")
    twice = inject_toc(once, "- [new](#new)")
    assert "old" not in twice
    assert twice.count("<!-- toc -->") == 2


def test_check_links_flags_missing_file(tmp_path):
    md = "[broken](./nope.md)"
    issues = check_links(md, tmp_path)
    assert issues and "does not exist" in issues[0].reason


def test_check_links_accepts_existing_file(tmp_path):
    (tmp_path / "other.md").write_text("# Child\n## Section\n")
    assert check_links("[ok](./other.md)", tmp_path) == []


def test_check_links_validates_anchor_in_target(tmp_path):
    (tmp_path / "other.md").write_text("# Child\n## Section\n")
    issues = check_links("[bad](./other.md#ghost)", tmp_path)
    assert issues and "anchor not found" in issues[0].reason


def test_check_links_ignores_external_urls(tmp_path):
    assert check_links("[x](https://example.com) [y](mailto:a@b.c)", tmp_path) == []


def test_check_links_skips_code_fences(tmp_path):
    assert check_links("```\n[broken](./nope.md)\n```", tmp_path) == []
