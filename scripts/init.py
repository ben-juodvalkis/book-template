#!/usr/bin/env python3
"""
init.py — turn the demo template into a fresh book.

Run this once right after cloning / "Use this template". It sets your title, page
size, and license holder, and resets book.spreads to a minimal starting book. The
stub spreads in src/spreads/ are LEFT in place as references to copy from.

Usage:
  ./book init                                    # interactive prompts
  ./book init --title "Wild Coast" --author "Sam Rivera"
  ./book init --title "Field Notes" --page-size trade-6x9 --author "A. Nguyen"
  ./book init --keep-spreads                     # don't touch book.spreads
  ./book init --dry-run                          # show the plan, change nothing
  ./book init --yes ...                          # non-interactive (needs flags)

What it changes:
  • src/master-header.html   <title>…</title>
  • book.config              page_size = …
  • LICENSE                  Copyright (c) YEAR HOLDER
  • book.spreads             reset to a minimal title + blank (unless --keep-spreads)
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _build import PAGE_SIZE_ALIASES, PAGE_SIZE_PRESETS, PROJECT_ROOT  # noqa: E402

HEADER = "src/master-header.html"
CONFIG = "book.config"
LICENSE = "LICENSE"
SPREADS = "book.spreads"

MINIMAL_SPREADS = """\
# book.spreads — the ordered list of sections in this book (page order).
# Blank lines and lines starting with # are ignored. This is the ONE file you
# edit to wire up sections. Copy a stub from src/spreads/ or run
# `./book generate gallery <dir>`, then list it below. Keep the total EVEN
# (saddle-stitch imposes in multiples of 4). See CLAUDE.md.

src/spreads/01-title.html
src/spreads/_blank.html
"""


def rel(p):
    return os.path.join(PROJECT_ROOT, p)


def prompt(label, default):
    if not sys.stdin.isatty():
        return default
    try:
        ans = input(f"{label}" + (f" [{default}]" if default else "") + ": ").strip()
    except EOFError:
        return default
    return ans or default


def plan_title(title):
    path = rel(HEADER)
    html = open(path).read()
    new = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", html, count=1, flags=re.S)
    return (HEADER, html, new, new != html)


def plan_page_size(page_size):
    path = rel(CONFIG)
    txt = open(path).read()
    if re.search(r"(?m)^\s*page_size\s*=", txt):
        new = re.sub(r"(?m)^\s*page_size\s*=.*$", f"page_size = {page_size}", txt, count=1)
    else:
        new = txt.rstrip() + f"\npage_size = {page_size}\n"
    return (CONFIG, txt, new, new != txt)


def plan_license(holder, year):
    path = rel(LICENSE)
    txt = open(path).read()

    def repl(m):
        yr = year or m.group(1)
        return f"Copyright (c) {yr} {holder}"
    new = re.sub(r"Copyright \(c\) (\d{4}).*", repl, txt, count=1)
    return (LICENSE, txt, new, new != txt)


def plan_spreads():
    path = rel(SPREADS)
    txt = open(path).read()
    return (SPREADS, txt, MINIMAL_SPREADS, MINIMAL_SPREADS != txt)


def parse_args(argv):
    opts = {"title": None, "author": None, "page_size": None, "year": None,
            "keep_spreads": False, "yes": False, "dry_run": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help"):
            print(__doc__)
            sys.exit(0)
        elif a == "--keep-spreads":
            opts["keep_spreads"] = True; i += 1
        elif a == "--yes":
            opts["yes"] = True; i += 1
        elif a == "--dry-run":
            opts["dry_run"] = True; i += 1
        elif a in ("--title", "--author", "--page-size", "--year"):
            if i + 1 >= len(argv):
                print(f"Error: {a} needs a value"); sys.exit(1)
            opts[a[2:].replace("-", "_")] = argv[i + 1]; i += 2
        else:
            print(f"Unknown argument: {a}"); sys.exit(1)
    return opts


def main():
    opts = parse_args(sys.argv[1:])
    interactive = sys.stdin.isatty() and not opts["yes"]

    title = opts["title"] or (prompt("Book title", "Book Title") if interactive else "Book Title")
    author = opts["author"] or (prompt("Author / copyright holder", "") if interactive else "")
    page_size = opts["page_size"] or (
        prompt("Page size preset", "blurb-8x10") if interactive else None)

    if page_size and page_size not in PAGE_SIZE_PRESETS and page_size not in PAGE_SIZE_ALIASES:
        print(f"Error: unknown page size {page_size!r}.")
        print(f"  Presets: {', '.join(PAGE_SIZE_PRESETS)}")
        print(f"  Aliases: {', '.join(PAGE_SIZE_ALIASES)}")
        sys.exit(1)

    changes = [plan_title(title)]
    if page_size:
        changes.append(plan_page_size(page_size))
    if author:
        changes.append(plan_license(author, opts["year"]))
    if not opts["keep_spreads"]:
        changes.append(plan_spreads())

    todo = [c for c in changes if c[3]]
    print("\nPlanned changes:")
    if not todo:
        print("  (nothing to change — already set)")
    for path, _old, _new, _ in todo:
        print(f"  • {path}")
    print()

    if opts["dry_run"]:
        print("Dry run — nothing written. Re-run without --dry-run to apply.")
        return
    if not todo:
        return

    if interactive:
        if input("Apply these changes? [y/N] ").strip().lower() not in ("y", "yes"):
            print("Aborted."); return

    for path, _old, new, _ in todo:
        with open(rel(path), "w") as f:
            f.write(new)
        print(f"  wrote {path}")

    print("\nInitialized. Next steps:")
    print("  1. Edit the title-page text/logo in src/spreads/01-title.html")
    print("  2. Set your palette + fonts in src/styles/design.css (and ./book fonts)")
    print("  3. Add sections to book.spreads (copy a stub or ./book generate)")
    print("  4. Rewrite README.md for your book")
    print("  5. ./book build")


if __name__ == "__main__":
    main()
