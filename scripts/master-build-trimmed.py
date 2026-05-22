#!/usr/bin/env python3
"""
master-build-trimmed.py — Build a trim-cropped preview PDF from the master.

Reads the current build's master PDF (builds/<branch>-<commit>/master-...pdf) and
produces ...-trimmed.pdf in the same folder. Each page's MediaBox and CropBox are
set to its TrimBox (8.0×10.0"), removing the bleed area so you see exactly what
will remain after Blurb cuts the book.

The source PDF must already exist. Run master-build.py first if it doesn't.

After cropping, this also builds a small shareable draft of the trimmed PDF
(...-trimmed-draft.pdf) via master-build-draft.py. Pass --no-draft to skip it.

Usage:
  python3 master-build-trimmed.py
  python3 master-build-trimmed.py --in  path/to/input.pdf
  python3 master-build-trimmed.py --out path/to/output.pdf
  python3 master-build-trimmed.py --no-draft
"""

import importlib.util
import os
import sys

import pikepdf

from _build import PROJECT_ROOT, SCRIPTS_DIR, build_paths


def _load_build_draft():
    spec = importlib.util.spec_from_file_location(
        "master_build_draft",
        os.path.join(SCRIPTS_DIR, "master-build-draft.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_draft


_PATHS = build_paths()
DEFAULT_IN  = os.path.join(PROJECT_ROOT, _PATHS["master"])
DEFAULT_OUT = os.path.join(PROJECT_ROOT, _PATHS["trimmed"])


def parse_args():
    args = sys.argv[1:]
    in_path  = DEFAULT_IN
    out_path = DEFAULT_OUT
    make_draft = True
    i = 0
    while i < len(args):
        if args[i] == "--in" and i + 1 < len(args):
            in_path = os.path.join(PROJECT_ROOT, args[i + 1])
            i += 2
        elif args[i] == "--out" and i + 1 < len(args):
            out_path = os.path.join(PROJECT_ROOT, args[i + 1])
            i += 2
        elif args[i] == "--no-draft":
            make_draft = False
            i += 1
        else:
            print(f"Unknown argument: {args[i]}")
            sys.exit(1)
    return in_path, out_path, make_draft


def crop_to_trim(in_path, out_path):
    if not os.path.exists(in_path):
        print(f"Error: source PDF not found: {in_path}")
        print("Run master-build.py first.")
        sys.exit(1)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with pikepdf.open(in_path) as pdf:
        for page_obj in pdf.pages:
            trim = page_obj.get("/TrimBox")
            if trim is None:
                continue
            page_obj["/MediaBox"] = trim
            page_obj["/CropBox"] = trim
        pdf.Root.PageLayout = pikepdf.Name("/TwoPageRight")
        pdf.save(out_path)

    size_mb = os.path.getsize(out_path) / 1e6
    page_count = len(pikepdf.open(out_path).pages)
    print(f"Trimmed PDF written: {os.path.relpath(out_path, PROJECT_ROOT)}")
    print(f"  Pages: {page_count}  |  Size: {size_mb:.1f} MB")
    print(f"  Each page: 8.0×10.0\" (trim, no bleed)")


def main():
    in_path, out_path, make_draft = parse_args()
    crop_to_trim(in_path, out_path)

    if make_draft:
        draft_out = out_path.replace(".pdf", "-draft.pdf")
        if draft_out == out_path:
            draft_out = out_path + "-draft.pdf"
        print()
        build_draft = _load_build_draft()
        build_draft(out_path, draft_out)


if __name__ == "__main__":
    main()
