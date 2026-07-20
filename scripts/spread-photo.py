#!/usr/bin/env python3
"""
spread-photo.py — prepare one photo to span a full two-page (cross-gutter) spread.

A cross-gutter / "double-truck" photo is placed as the SAME background image on
both facing pages, sized to the whole flat spread; the `.spread-photo` CSS classes
(design.css) offset each page so the two halves meet exactly at the fold. For the
halves to line up WITHOUT stretching, the image must match the spread's aspect
ratio. This tool cover-crops any photo to that exact ratio — derived from the
book's geometry in book.config (page size + bleed), so it stays correct if you
change page size — and writes one ready-to-use image.

It does NOT slice the photo in half or bake in any offset: one file, used on both
pages, with the alignment handled by the CSS classes. Nothing in the render/merge
pipeline changes.

Usage:
  python3 scripts/spread-photo.py assets/raw.jpg
  python3 scripts/spread-photo.py assets/raw.jpg --out assets/hero-spread.jpg
  python3 scripts/spread-photo.py assets/raw.jpg --focus left        # keep the left of a too-wide photo
  python3 scripts/spread-photo.py assets/raw.jpg --dpi 300 --quality 95

Then put the SAME file on both facing pages of a spread (see 04-spread-photo.html):
  <div class="page spread-photo spread-photo-verso" style="page:p1;
       background-image:url('assets/hero-spread.jpg'); background-color:#111;"></div>
  <div class="page spread-photo spread-photo-recto" style="page:p2;
       background-image:url('assets/hero-spread.jpg'); background-color:#111;"></div>

The verso half must land on a LEFT-hand (even) page and the recto half on the
RIGHT-hand (odd) page facing it. master-build.py warns if a spread photo is placed
on the wrong parity. See docs/DESIGN-LANGUAGE.md for the full recipe.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _build import PROJECT_ROOT, geometry, load_config  # noqa: E402


def cover_crop(img, target_ratio, focus="center"):
    """Crop img to exactly target_ratio (w/h) without scaling, keeping `focus`."""
    w, h = img.size
    ratio = w / h
    if ratio > target_ratio:  # too wide → trim the sides
        new_w = round(h * target_ratio)
        if focus == "left":
            x0 = 0
        elif focus == "right":
            x0 = w - new_w
        else:
            x0 = (w - new_w) // 2
        return img.crop((x0, 0, x0 + new_w, h))
    if ratio < target_ratio:  # too tall → trim top/bottom (kept centered)
        new_h = round(w / target_ratio)
        y0 = (h - new_h) // 2
        return img.crop((0, y0, w, y0 + new_h))
    return img


def parse_args(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    src = argv[0]
    opts = {"focus": "center", "out": None, "dpi": None, "quality": 92}
    i = 1
    while i < len(argv):
        a = argv[i]
        if a in ("--focus", "--out", "--dpi", "--quality"):
            if i + 1 >= len(argv):
                print(f"Error: {a} needs a value")
                sys.exit(1)
            key = a[2:]
            val = argv[i + 1]
            opts[key] = int(val) if key in ("dpi", "quality") else val
            i += 2
        else:
            print(f"Unknown argument: {a}")
            sys.exit(1)
    if opts["focus"] not in ("left", "center", "right"):
        print("Error: --focus must be left, center, or right")
        sys.exit(1)
    return src, opts


def main():
    src, opts = parse_args(sys.argv[1:])
    from PIL import Image

    src_abs = src if os.path.isabs(src) else os.path.join(PROJECT_ROOT, src)
    if not os.path.exists(src_abs):
        print(f"Error: source image not found: {src}")
        sys.exit(1)

    geom = geometry(load_config())
    sw, sh = geom["spread_w"], geom["spread_h"]
    target_ratio = sw / sh
    target_dpi = opts["dpi"] or int(geom["dpi"])

    img = Image.open(src_abs)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    cropped = cover_crop(img, target_ratio, opts["focus"])
    cw, ch = cropped.size
    eff_dpi = min(cw / sw, ch / sh)

    if opts["out"] is None:
        base, _ = os.path.splitext(src_abs)
        out_abs = base + "-spread.jpg"
    else:
        out_abs = opts["out"] if os.path.isabs(opts["out"]) else os.path.join(PROJECT_ROOT, opts["out"])
    os.makedirs(os.path.dirname(out_abs) or ".", exist_ok=True)

    save_kw = {"quality": opts["quality"]} if out_abs.lower().endswith((".jpg", ".jpeg")) else {}
    cropped.convert("RGB").save(out_abs, **save_kw)

    rel = os.path.relpath(out_abs, PROJECT_ROOT)
    print(f"Spread photo written: {rel}")
    print(f"  Spread canvas: {sw:g}×{sh:g}in  (aspect {target_ratio:.4f}, from book.config)")
    print(f"  Cropped {img.size[0]}×{img.size[1]}px → {cw}×{ch}px  ≈ {eff_dpi:.0f} DPI at print size")
    if eff_dpi < target_dpi - 1:
        need_w, need_h = round(sw * target_dpi), round(sh * target_dpi)
        print(f"  WARNING: {eff_dpi:.0f} DPI is below the {target_dpi} DPI target — the print may look soft.")
        print(f"           For {target_dpi} DPI use a source that crops to ≥ {need_w}×{need_h}px.")
    print()
    print("  Place the SAME file on both facing pages, adding:")
    print("    .spread-photo .spread-photo-verso   on the LEFT-hand (even) page")
    print("    .spread-photo .spread-photo-recto   on the RIGHT-hand (odd) page facing it")


if __name__ == "__main__":
    main()
