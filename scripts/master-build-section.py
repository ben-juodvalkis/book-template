#!/usr/bin/env python3
"""
master-build-section.py — Single-section build using the active pipeline.

Renders one spread fragment using the exact same render path as
master-build.py. Page numbers start at 1 (preview mode, not book position).

Usage:
  python3 master-build-section.py 01-title
  python3 master-build-section.py src/spreads/01-title.html
  python3 master-build-section.py 01-title --html-only
  python3 master-build-section.py 01-title --out .temp/title-check.pdf
  python3 master-build-section.py 01-title --first-page 7  # preview at book position 7

Output (default):
  .temp/{section-name}.pdf
"""

import os
import re
import sys

from _build import (
    PROJECT_ROOT,
    SPREADS_DIR,
    build_section_html,
    read,
    resolve_section,
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
        print(f"  Expected: a file in {SPREADS_DIR}/ or a full path")
        sys.exit(1)

    section_name = os.path.splitext(os.path.basename(src_rel))[0]

    if out_path is None:
        out_pdf  = os.path.join(TEMP_DIR, f"{section_name}.pdf")
        out_html = os.path.join(TEMP_DIR, f"{section_name}.html")
    else:
        out_pdf  = out_path
        out_html = re.sub(r'\.pdf$', '.html', out_path)

    print(f"Section:    {src_rel}")
    print(f"Output:     {out_pdf}")
    print(f"First page: {first_page} ({'verso' if first_page % 2 == 0 else 'recto'})")

    wrapped = build_section_html(read(src_rel), first_page_num=first_page)
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
