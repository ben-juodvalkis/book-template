#!/usr/bin/env python3
"""
master-build-draft.py — Build a small, shareable draft of a build PDF.

Rasterizes every page to a JPEG and reassembles them into a new PDF. This is the
ONLY robust way to shrink these books: WeasyPrint renders full-bleed CSS
`background-image` photos as tiling PATTERNS with the image nested inside, and
every PDF-restructuring compressor (Ghostscript `pdfwrite`, `mutool clean`,
`mutool convert`) silently DROPS that pattern-nested image — the full-bleed photo
vanishes, leaving only the fallback color (e.g. the 07-in-that-skirt left page).
`mutool draw` to a raster, by contrast, renders the pattern faithfully, so we
flatten each page to an image and rebuild from those. Output is screen-only —
never submit a draft to Blurb.

Default source is the trimmed preview; pass --in to draft any other build PDF
(e.g. the Acrobat-processed READY-FOR-BLURB file).

Requires `mutool` (mupdf-tools) on PATH and Pillow in the interpreter.

Usage:
  python3 master-build-draft.py                       # trimmed → trimmed-draft
  python3 master-build-draft.py --in  path/to/in.pdf
  python3 master-build-draft.py --out path/to/out.pdf
  python3 master-build-draft.py --dpi 150 --quality 80
"""

import glob
import os
import subprocess
import sys
import tempfile

import pikepdf
from PIL import Image

from _build import PROJECT_ROOT, build_paths

_PATHS = build_paths()
DEFAULT_IN  = os.path.join(PROJECT_ROOT, _PATHS["trimmed"])
DEFAULT_OUT = os.path.join(PROJECT_ROOT, _PATHS["trimmed_draft"])
DEFAULT_DPI = 125
DEFAULT_QUALITY = 72


def build_draft(in_path, out_path, dpi=DEFAULT_DPI, quality=DEFAULT_QUALITY):
    """Rasterize each page (mutool draw) and reassemble into a JPEG-backed PDF."""
    if not os.path.exists(in_path):
        print(f"Error: source PDF not found: {in_path}")
        print("Run master-build.py / master-build-trimmed.py first.")
        sys.exit(1)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with pikepdf.open(in_path) as src:
        npages = len(src.pages)
    print(f"Drafting {os.path.relpath(in_path, PROJECT_ROOT)}: "
          f"{npages} pages → raster {dpi}dpi q{quality}")

    with tempfile.TemporaryDirectory() as td:
        png_pat = os.path.join(td, "p%04d.png")
        result = subprocess.run(
            ["mutool", "draw", "-r", str(dpi), "-c", "rgb", "-o", png_pat, in_path],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print("ERROR: mutool draw failed:")
            print(result.stderr)
            sys.exit(1)

        pngs = sorted(glob.glob(os.path.join(td, "p*.png")))
        if len(pngs) != npages:
            print(f"ERROR: expected {npages} rasterized pages, got {len(pngs)}")
            sys.exit(1)

        imgs = []
        for i, p in enumerate(pngs):
            jp = os.path.join(td, f"j{i:04d}.jpg")
            Image.open(p).convert("RGB").save(jp, "JPEG", quality=quality, optimize=True)
            imgs.append(Image.open(jp).convert("RGB"))
            if (i + 1) % 20 == 0:
                print(f"  rasterized {i + 1}/{npages}")

        imgs[0].save(
            out_path, "PDF", save_all=True, append_images=imgs[1:],
            resolution=float(dpi),
        )

    size_mb = os.path.getsize(out_path) / 1e6
    print(f"Draft PDF written: {os.path.relpath(out_path, PROJECT_ROOT)}")
    print(f"  Pages: {npages}  |  Size: {size_mb:.1f} MB  |  {dpi}dpi JPEG q{quality}")
    print(f"  Screen-only — never submit a draft to Blurb.")


def parse_args():
    args = sys.argv[1:]
    in_path, out_path = DEFAULT_IN, DEFAULT_OUT
    dpi, quality = DEFAULT_DPI, DEFAULT_QUALITY
    i = 0
    while i < len(args):
        if args[i] == "--in" and i + 1 < len(args):
            in_path = os.path.join(PROJECT_ROOT, args[i + 1]); i += 2
        elif args[i] == "--out" and i + 1 < len(args):
            out_path = os.path.join(PROJECT_ROOT, args[i + 1]); i += 2
        elif args[i] == "--dpi" and i + 1 < len(args):
            dpi = int(args[i + 1]); i += 2
        elif args[i] == "--quality" and i + 1 < len(args):
            quality = int(args[i + 1]); i += 2
        else:
            print(f"Unknown argument: {args[i]}")
            sys.exit(1)
    return in_path, out_path, dpi, quality


def main():
    in_path, out_path, dpi, quality = parse_args()
    build_draft(in_path, out_path, dpi, quality)


if __name__ == "__main__":
    main()
