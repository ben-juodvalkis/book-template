#!/usr/bin/env python3
"""
cover.py — render a PERFECT-BOUND wraparound cover (back + spine + front).

The spine width is computed from the interior page count and the paper stock:

    spine_inches = page_count / paper_ppi        (pages-per-inch)

so the flat cover sheet is sized 2*trim_width + spine wide by trim_height tall,
plus bleed on all four outer edges. Content lives in src/cover/cover.html; layout
and geometry in src/styles/cover.css. Both read the same book.config geometry as
the interior, so a change in trim size reflows the cover too.

Usage:
  ./book cover --pages 120                 # spine from 120 pages + book.config paper
  ./book cover --pages 120 --stock cream   # override the paper stock (see PAPER_STOCKS)
  ./book cover --pages 120 --ppi 400       # override pages-per-inch directly
  ./book cover                             # auto-detect page count from the latest build
  ./book cover --pages 120 --out my-cover.pdf
  ./book cover --pages 120 --html-only

Output (default): builds/<slug>/cover-<slug>.pdf
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _build import (  # noqa: E402
    PROJECT_ROOT,
    PAPER_STOCKS,
    build_paths,
    cover_css_vars,
    cover_geometry,
    load_config,
    read,
    resolve_binding,
    resolve_ppi,
    strip_outer_tags,
    weasyprint_render,
    write,
)

COVER_TEMPLATE = "src/cover/cover.html"
MIN_SPINE_TEXT_IN = 0.0625   # ~1/16"; below this most printers disallow spine text


def detect_page_count():
    """Page count from the current build's master PDF, or None if not built yet."""
    master = os.path.join(PROJECT_ROOT, build_paths()["master"])
    if not os.path.exists(master):
        return None
    try:
        import pikepdf
        with pikepdf.open(master) as p:
            return len(p.pages)
    except Exception:
        return None


def parse_args(argv):
    opts = {"pages": None, "ppi": None, "stock": None, "template": COVER_TEMPLATE,
            "out": None, "html_only": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help"):
            print(__doc__)
            sys.exit(0)
        elif a == "--html-only":
            opts["html_only"] = True
            i += 1
        elif a in ("--pages", "--ppi", "--stock", "--template", "--out"):
            if i + 1 >= len(argv):
                print(f"Error: {a} needs a value")
                sys.exit(1)
            key = a[2:]
            val = argv[i + 1]
            if key in ("pages", "ppi"):
                try:
                    val = int(val)
                except ValueError:
                    print(f"Error: {a} must be an integer, got {val!r}")
                    sys.exit(1)
            opts[key] = val
            i += 2
        else:
            print(f"Unknown argument: {a}")
            sys.exit(1)
    return opts


def build_cover_html(fragment, cov):
    """Minimal self-contained cover document: design.css + cover.css + geometry vars."""
    head = (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        "  <meta charset=\"UTF-8\">\n"
        "  <title>Cover</title>\n"
        "  <link rel=\"stylesheet\" href=\"src/styles/design.css\">\n"
        "  <link rel=\"stylesheet\" href=\"src/styles/cover.css\">\n"
        + cover_css_vars(cov) + "\n</head>\n<body>\n"
    )
    return head + strip_outer_tags(fragment) + "\n</body>\n</html>\n"


def main():
    opts = parse_args(sys.argv[1:])
    cfg = load_config()

    # Command-line overrides win over book.config for this one render.
    if opts["ppi"] is not None:
        cfg["paper_ppi"] = opts["ppi"]
    if opts["stock"] is not None:
        if opts["stock"] not in PAPER_STOCKS:
            print(f"Error: unknown --stock {opts['stock']!r}. Known: {', '.join(PAPER_STOCKS)}")
            sys.exit(1)
        cfg["paper_stock"] = opts["stock"]
        cfg["paper_ppi"] = None   # let the stock name resolve

    pages = opts["pages"]
    if pages is None:
        pages = detect_page_count()
        if pages is None:
            print("Error: --pages N is required (couldn't auto-detect — run `./book build` first).")
            sys.exit(1)
        print(f"Auto-detected {pages} pages from the latest build.")
    if pages < 1:
        print("Error: --pages must be >= 1")
        sys.exit(1)

    cov = cover_geometry(pages, cfg)
    ppi = cov["ppi"]
    spine = cov["spine_w"]

    binding = resolve_binding(cfg)
    if binding != "perfect-bound":
        print(f"NOTE: book.config binding is {binding!r}; a spine only applies to "
              f"perfect-bound books. Rendering anyway with the computed spine.")

    out_rel = opts["out"] or os.path.join(build_paths()["dir"], f"cover-{build_paths()['slug']}.pdf")
    html_rel = out_rel[:-4] + ".html" if out_rel.endswith(".pdf") else out_rel + ".html"

    fragment = read(opts["template"])
    write(html_rel, build_cover_html(fragment, cov))

    print(f"Cover for {pages} pages on {ppi} ppi paper "
          f"({opts['stock'] or cfg.get('paper_stock') or 'default'}):")
    print(f"  Spine width:  {spine:.4f}in ({spine * 25.4:.2f}mm)")
    print(f"  Flat cover:   {cov['cover_trim_w']:.4f} × {cov['cover_trim_h']:.4f}in trim, "
          f"{cov['cover_div_w']:.4f} × {cov['cover_div_h']:.4f}in with bleed")
    print(f"  Fold lines (from the sheet's LEFT trim edge): "
          f"back|spine at {cov['trim_width']:.4f}in, spine|front at {cov['trim_width'] + spine:.4f}in")
    if spine < MIN_SPINE_TEXT_IN:
        print(f"  WARNING: spine {spine:.4f}in is under {MIN_SPINE_TEXT_IN}in — most printers "
              f"disallow spine text this thin. Remove the .spine-title or add pages.")

    if opts["html_only"]:
        print(f"\n  → {html_rel} (--html-only)")
        return

    print(f"\nRendering via WeasyPrint...")
    ok, stderr = weasyprint_render(html_rel, out_rel)
    for line in stderr.splitlines():
        if "WARNING" in line or "ERROR" in line:
            print(f"  weasyprint: {line.strip()}")
    if not ok:
        print("\nERROR: WeasyPrint failed")
        for line in stderr.splitlines():
            if line.strip():
                print(f"  {line}")
        sys.exit(1)

    size_mb = os.path.getsize(os.path.join(PROJECT_ROOT, out_rel)) / 1e6
    print(f"\n→ {out_rel} ({size_mb:.1f} MB)")
    print("  Screen proof only — soft-proof colors and confirm the spine against your")
    print("  printer's cover template before submitting.")


if __name__ == "__main__":
    main()
