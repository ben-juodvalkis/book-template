#!/usr/bin/env python3
"""
master-build.py — full-book pipeline. Asymmetric bleed on the OUTSIDE edge
(page 1 = RIGHT-hand; odd = right-hand → bleed RIGHT, even = left-hand → bleed
LEFT) and a 0.5" outside-edge safe margin.

The ordered list of sections lives in `book.spreads` (one path per line) — edit
that to wire up your book. Uses src/styles/print.css and writes to
builds/<branch>-<commit>/.

Usage:
  python3 master-build.py             # build all sections + merge, then trimmed + draft
  python3 master-build.py --no-trim   # build the master PDF only (skip trimmed + draft)
  python3 master-build.py --html-only # write per-section wrapped HTML, skip render

Output (paths carry the current <branch>-<commit>, e.g. main-fcbfb7d):
  builds/<branch>-<commit>/master-<branch>-<commit>.pdf               (final book, 8.125×10.25")
  builds/<branch>-<commit>/master-<branch>-<commit>-trimmed.pdf       (trim preview, no bleed)
  builds/<branch>-<commit>/master-<branch>-<commit>-trimmed-draft.pdf (small shareable draft)
  builds/<branch>-<commit>/sections/<name>.pdf                        (per-section PDFs)
  builds/<branch>-<commit>/sections/<name>.html                       (per-section wrapped HTML)
"""

import importlib.util
import os
import sys

from _build import (
    PROJECT_ROOT,
    SCRIPTS_DIR,
    build_paths,
    build_section_html,
    count_page_divs,
    load_config,
    load_spreads,
    merge_pdfs,
    read,
    spread_photo_parity_warnings,
    weasyprint_render,
    write,
)

PATHS        = build_paths()
OUT_DIR      = PATHS["dir"]
SECTIONS_DIR = PATHS["sections_dir"]
MASTER_PDF   = PATHS["master"]
CONFIG       = load_config()
FRONT_MATTER_PAGES = CONFIG["front_matter_pages"]


def _load_trimmed_builder():
    spec = importlib.util.spec_from_file_location(
        "master_build_trimmed",
        os.path.join(SCRIPTS_DIR, "master-build-trimmed.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assert_bleed_parity(pdf_path):
    """Guard against the recurring odd/even bleed-side bug.

    CANONICAL ORIENTATION: page 1 is a RIGHT-hand page → odd pages bleed on the
    RIGHT (outside; binding LEFT), even pages bleed on the LEFT (outside; binding
    RIGHT). This is easy to get backwards. This check opens the merged PDF and
    exits non-zero if page 1 isn't bleeding RIGHT (and page 2 LEFT), so the bug
    can never silently reach the printer.
    """
    import pikepdf

    def bleed_side(pg):
        mb = [float(x) for x in pg.MediaBox]
        tb = [float(x) for x in pg.TrimBox]
        left = round(tb[0] - mb[0], 1)   # >0 → bleed extends past trim on the left
        right = round(mb[2] - tb[2], 1)  # >0 → bleed on the right
        return "L" if left > right else "R"

    with pikepdf.open(pdf_path) as p:
        p1, p2 = bleed_side(p.pages[0]), bleed_side(p.pages[1])

    if p1 != "R" or p2 != "L":
        print(f"\n{'='*60}")
        print("  BLEED PARITY CHECK FAILED")
        print(f"  Expected page 1 bleed RIGHT, page 2 bleed LEFT (odd=RIGHT-hand).")
        print(f"  Got: page 1 = {p1}, page 2 = {p2}.")
        print("  This is the recurring odd/even bleed-side bug. Do NOT send to Blurb.")
        print("  Fix the @page :left/:right bleed values in src/styles/print.css")
        print("  and the swap block in _build.py (they must be mirror images).")
        print(f"{'='*60}")
        sys.exit(1)

    print(f"  Bleed parity OK: page 1 = {p1} (RIGHT-hand), page 2 = {p2} (LEFT-hand).")


def assert_safe_margins(pdf_path, fail_hard=False):
    """Guard against the recurring safe-margin bug (text/ink crossing the trim-safe zone).

    Background: the .page div overhangs trim by 0.125" on ALL sides (margin:-0.125in),
    so a CSS inset of 0.5in lands only 0.375" from trim. In 2026-05 a full audit found
    ~26 pages where binding/outside text sat 0.375" from trim instead of the required
    0.5". This check measures rendered TEXT ink (via pdftotext -bbox) against the trim
    box on every page and reports anything closer than spec:
        fold/outside >= 0.5"   top/bottom >= 0.25"   (measured FROM TRIM)

    Orientation is derived from the bleed geometry (which side has bleed = outside),
    NOT assumed from odd/even. Folios (bare page numbers) are excluded. Big Barriecito
    display titles report phantom descender/ascender boxes, so TOP/BOT flags are
    downgraded to warnings; FOLD/OUTSIDE flags on text are real.

    Prints a per-page report. With fail_hard=True, exits non-zero if any FOLD/OUTSIDE
    text violation is found. Requires `pdftotext` (poppler) on PATH; if absent, warns
    and skips (does not break the build).
    """
    import shutil, subprocess, re, xml.etree.ElementTree as ET
    import pikepdf

    if shutil.which("pdftotext") is None:
        print("  Safe-margin check SKIPPED (pdftotext/poppler not on PATH).")
        return

    PT = 72.0
    FOLD = OUT = 0.5
    TB = 0.25

    with pikepdf.open(pdf_path) as p:
        boxes = [([float(x) for x in pg.MediaBox], [float(x) for x in pg.TrimBox])
                 for pg in p.pages]

    out = subprocess.run(["pdftotext", "-bbox", "-q", pdf_path, "-"],
                         capture_output=True, text=True).stdout
    out = re.sub(r'xmlns="[^"]+"', "", out, count=1)
    pages = ET.fromstring(out).find("body").find("doc").findall("page")

    hard = []   # real FOLD/OUTSIDE text violations
    soft = []   # TOP/BOT (often title font-box artifacts)
    for i, (pgx, (mb, tb)) in enumerate(zip(pages, boxes), start=1):
        bL, bR = tb[0] - mb[0], mb[2] - tb[2]
        outside = "L" if bL > bR else "R"
        fold = "R" if outside == "L" else "L"
        mx0 = mb[0]
        L = R = T = B = None
        for w in pgx.iter("word"):
            t = (w.text or "").strip()
            if t.isdigit() and len(t) <= 2:   # skip folio
                continue
            x0 = mx0 + float(w.get("xMin")); x1 = mx0 + float(w.get("xMax"))
            ytop = mb[3] - float(w.get("yMin")); ybot = mb[3] - float(w.get("yMax"))
            L = x0 if L is None else min(L, x0); R = x1 if R is None else max(R, x1)
            T = ytop if T is None else max(T, ytop); B = ybot if B is None else min(B, ybot)
        if L is None:
            continue
        tl = (L - tb[0]) / PT; tr = (tb[2] - R) / PT
        tt = (tb[3] - T) / PT; tbo = (B - tb[1]) / PT
        fold_d = tr if fold == "R" else tl
        out_d = tl if outside == "L" else tr
        if fold_d < FOLD - 0.01:
            hard.append((i, "FOLD", round(fold_d, 3)))
        if out_d < OUT - 0.01:
            hard.append((i, "OUTSIDE", round(out_d, 3)))
        if tt < TB - 0.01:
            soft.append((i, "TOP", round(tt, 3)))
        if tbo < TB - 0.01:
            soft.append((i, "BOTTOM", round(tbo, 3)))

    if soft:
        print(f"  Safe-margin: {len(soft)} TOP/BOTTOM near-edge text (often big-title "
              f"font-box artifacts — verify by eye):")
        for pg, edge, v in soft:
            print(f"      p{pg} {edge} {v}in from trim (min {TB})")
    if hard:
        print(f"\n{'='*60}")
        print("  SAFE-MARGIN CHECK FAILED")
        print("  Text ink crosses the binding/outside safe zone (min 0.5\" from trim).")
        print("  Likely the div-overhang bug: a CSS inset of 0.5in lands 0.375\" from")
        print("  trim — binding/outside content needs 0.625in from the .page div edge.")
        for pg, edge, v in hard:
            print(f"      p{pg} {edge} {v}in from trim (min {FOLD})")
        print(f"{'='*60}")
        if fail_hard:
            sys.exit(1)
    elif not soft:
        print("  Safe-margin OK: all text clears 0.5\" binding/outside, 0.25\" top/bottom.")


SPREADS = load_spreads()


def main():
    html_only = "--html-only" in sys.argv
    no_trim   = "--no-trim" in sys.argv

    print(f"Building {len(SPREADS)} section(s) — build {PATHS['slug']} ...")
    total_pages = 0
    rendered_pdfs = []

    for src in SPREADS:
        name = os.path.splitext(os.path.basename(src))[0]
        fragment = read(src)
        page_count = count_page_divs(fragment)
        first_page = total_pages + 1

        wrapped = build_section_html(fragment, first_page_num=first_page,
                                     front_matter_pages=FRONT_MATTER_PAGES)
        html_out = os.path.join(SECTIONS_DIR, f"{name}.html")
        write(html_out, wrapped)

        parity = "verso" if first_page % 2 == 0 else "recto"
        print(f"  [{name}] pages {first_page}-{first_page + page_count - 1} ({page_count}, starts on {parity})")

        for warning in spread_photo_parity_warnings(fragment, first_page):
            print(f"    WARNING: {warning}")

        if not html_only:
            pdf_out = os.path.join(SECTIONS_DIR, f"{name}.pdf")
            ok, stderr = weasyprint_render(html_out, pdf_out)
            if not ok:
                print(f"    ERROR rendering {name}:")
                for line in stderr.splitlines():
                    if line.strip():
                        print(f"      {line}")
                sys.exit(1)
            for line in stderr.splitlines():
                if "WARNING" in line or "ERROR" in line:
                    print(f"    weasyprint: {line.strip()}")
            rendered_pdfs.append(os.path.join(PROJECT_ROOT, pdf_out))

        total_pages += page_count

    print(f"\n  Total: {total_pages} pages")
    if total_pages % 2 != 0:
        print(f"  WARNING: page count is ODD ({total_pages}) — saddle-stitch requires even.")
    if total_pages < 20:
        print(f"  WARNING: page count < 20 (Blurb minimum)")

    if html_only:
        print(f"\nDone (--html-only). Per-section HTML in {SECTIONS_DIR}/")
        return

    print(f"\nMerging {len(rendered_pdfs)} section PDF(s) → {MASTER_PDF} ...")
    merge_pdfs(rendered_pdfs, os.path.join(PROJECT_ROOT, MASTER_PDF))

    assert_bleed_parity(os.path.join(PROJECT_ROOT, MASTER_PDF))
    assert_safe_margins(os.path.join(PROJECT_ROOT, MASTER_PDF))

    size_mb = os.path.getsize(os.path.join(PROJECT_ROOT, MASTER_PDF)) / 1e6
    print(f"\n{'='*60}")
    print(f"  Master build complete — build {PATHS['slug']}.")
    print(f"  PDF:         {MASTER_PDF} ({size_mb:.1f} MB)")
    print(f"  Total pages: {total_pages}")
    print(f"  Per-section PDFs kept in {SECTIONS_DIR}/")

    if no_trim:
        print(f"\nSkipping trimmed + draft (--no-trim).")
        return

    print(f"\nBuilding trimmed preview + shareable draft ...")
    trimmed = _load_trimmed_builder()
    master_abs  = os.path.join(PROJECT_ROOT, MASTER_PDF)
    trimmed_abs = os.path.join(PROJECT_ROOT, PATHS["trimmed"])
    trimmed.crop_to_trim(master_abs, trimmed_abs)
    draft_abs = trimmed_abs.replace(".pdf", "-draft.pdf")
    print()
    build_draft = trimmed._load_build_draft()
    build_draft(trimmed_abs, draft_abs)


if __name__ == "__main__":
    main()
