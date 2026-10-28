from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .linkcheck import check_links
from .toc import extract_headings, inject_toc, render_toc


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mdtoc", description="Generate a Markdown TOC and check links.")
    p.add_argument("files", nargs="+", type=Path)
    p.add_argument("--write", action="store_true", help="inject the TOC into the file in place")
    p.add_argument("--min-level", type=int, default=2)
    p.add_argument("--max-level", type=int, default=3)
    p.add_argument("--check-links", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code = 0
    for path in args.files:
        if not path.exists():
            print(f"error: {path} not found", file=sys.stderr)
            exit_code = 2
            continue
        text = path.read_text(encoding="utf-8")
        headings = extract_headings(text, max_level=args.max_level)
        toc = render_toc(headings, min_level=args.min_level)
        if args.write:
            path.write_text(inject_toc(text, toc), encoding="utf-8")
            print(f"updated {path} ({len(headings)} headings)")
        else:
            print(f"## {path}\n{toc}\n")
        if args.check_links:
            issues = check_links(text, path.parent, headings)
            for issue in issues:
                print(f"{path}:{issue}")
            if issues:
                exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
