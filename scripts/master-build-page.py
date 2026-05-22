#!/usr/bin/env python3
"""
master-build-page.py — Single-page (or range) build using the active pipeline.

Extracts one or more .page divs from a spread fragment and renders them via
the same path as master-build.py. Page numbers start at 1 (preview mode).

Usage:
  python3 master-build-page.py 01-title --page 2
  python3 master-build-page.py 01-title --page 2-4
  python3 master-build-page.py src/spreads/01-title.html --page 1
  python3 master-build-page.py 01-title --page 2 --html-only
  python3 master-build-page.py 01-title --page 2 --out .temp/title-p2-check.pdf
  python3 master-build-page.py 01-title --page 2 --first-page 7  # preview at book pos 7

Output (default):
  .temp/{section-name}-p{N}.pdf          (single page)
  .temp/{section-name}-p{N}-{M}.pdf      (range)
"""

import os
import re
import sys

from _build import (
    PROJECT_ROOT,
    SPREADS_DIR,
    build_section_html,
    extract_pages,
    parse_page_range,
    read,
    resolve_section,
    strip_outer_tags,
    weasyprint_render,
    write,
)

TEMP_DIR = ".temp"


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)

    html_only = '--html-only' in args
    args = [a for a in args if a != '--html-only']

    page_spec = None
    if '--page' in args:
        i = args.index('--page')
        if i + 1 >= len(args):
            print("Error: --page requires a value (e.g. --page 2 or --page 2-4)")
            sys.exit(1)
        page_spec = args[i + 1]
        args = args[:i] + args[i + 2:]

    if page_spec is None:
        print("Error: --page N (or --page N-M) is required")
        print("  Example: python3 master-build-page.py 09-feral --page 2")
        sys.exit(1)

    page_indices = parse_page_range(page_spec)

    first_page = 1
    if '--first-page' in args:
        i = args.index('--first-page')
        first_page = int(args[i + 1])
        args = args[:i] + args[i + 2:]

    out_path = None
    if '--out' in args:
        i = args.index('--out')
        out_path = args[i + 1]
        args = args[:i] + args[i + 2:]

    if not args:
        print("Error: no section specified.")
        sys.exit(1)

    src_rel = resolve_section(args[0], SPREADS_DIR)
    if src_rel is None:
        print(f"Error: could not find section '{args[0]}'")
        sys.exit(1)

    section_name = os.path.splitext(os.path.basename(src_rel))[0]

    if len(page_indices) == 1:
        page_suffix = f"p{page_indices[0] + 1}"
    else:
        page_suffix = f"p{page_indices[0] + 1}-{page_indices[-1] + 1}"

    if out_path is None:
        out_pdf  = os.path.join(TEMP_DIR, f"{section_name}-{page_suffix}.pdf")
        out_html = os.path.join(TEMP_DIR, f"{section_name}-{page_suffix}.html")
    else:
        out_pdf  = out_path
        out_html = re.sub(r'\.pdf$', '.html', out_path)

    print(f"Section:    {src_rel}")
    print(f"Pages:      {page_spec}")
    print(f"Output:     {out_pdf}")
    print(f"First page: {first_page} ({'verso' if first_page % 2 == 0 else 'recto'})")

    fragment = strip_outer_tags(read(src_rel))
    fragment = extract_pages(fragment, page_indices)
    wrapped = build_section_html(fragment, first_page_num=first_page)
    write(out_html, wrapped)

    if html_only:
        print(f"  → {out_html}")
        return

    print(f"\nRendering via WeasyPrint...")
    ok, stderr = weasyprint_render(out_html, out_pdf)
    for line in stderr.splitlines():
        if line.strip():
            print(f"  weasyprint: {line}")
    if not ok:
        print(f"\nERROR: WeasyPrint failed")
        sys.exit(1)

    size_mb = os.path.getsize(os.path.join(PROJECT_ROOT, out_pdf)) / 1e6
    print(f"\n→ {out_pdf} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
