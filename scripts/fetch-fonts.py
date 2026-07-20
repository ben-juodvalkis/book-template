#!/usr/bin/env python3
"""
fetch-fonts.py — self-host fonts for reproducible, offline, CI-safe renders.

Rendering with a CDN <link> (e.g. Google Fonts) means every build depends on the
network and can shift when the hosted font updates. Self-hosting pins the exact
files into fonts/ and generates fonts/fonts.css (@font-face rules) so the output
is identical everywhere.

Reads the manifest fonts/fonts.txt — one font per line, pipe-separated:

    family | weight | style | source

  family  the CSS font-family name you'll use (e.g. Work Sans)
  weight  400, 700, or a range like 100 900
  style   normal or italic
  source  an https URL to an OFL/permissively-licensed font file, OR a local
          path (relative to the project root or absolute) to copy in

Lines starting with # and blank lines are ignored. Only add fonts you have the
right to redistribute (OFL fonts qualify — keep their license file in fonts/).

Usage:
  ./book fonts               # fetch/copy everything in the manifest, write fonts.css
  ./book fonts --list        # show what the manifest declares, download nothing

Then link the result in src/master-header.html:
  <link rel="stylesheet" href="fonts/fonts.css">
and set the family in src/styles/design.css. See docs/FONTS.md.
"""

import os
import shutil
import ssl
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _build import PROJECT_ROOT  # noqa: E402

FONTS_DIR = "fonts"
MANIFEST = "fonts/fonts.txt"
OUT_CSS = "fonts/fonts.css"
FORMATS = {".woff2": "woff2", ".woff": "woff", ".ttf": "truetype", ".otf": "opentype"}


def parse_manifest():
    path = os.path.join(PROJECT_ROOT, MANIFEST)
    if not os.path.exists(path):
        print(f"No manifest at {MANIFEST}. Create it (see the header of this script "
              f"or docs/FONTS.md) with lines like:\n  Work Sans | 400 | normal | <url-or-path>")
        sys.exit(1)
    entries = []
    with open(path) as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 4:
                print(f"  {MANIFEST}:{lineno}: expected 'family | weight | style | source', "
                      f"skipping: {line!r}")
                continue
            family, weight, style, source = parts
            entries.append({"family": family, "weight": weight, "style": style, "source": source})
    return entries


def fetch_one(source):
    """Return the local fonts/ filename for a source, downloading/copying as needed."""
    fonts_abs = os.path.join(PROJECT_ROOT, FONTS_DIR)
    os.makedirs(fonts_abs, exist_ok=True)
    base = os.path.basename(source.split("?", 1)[0])
    if not base:
        raise ValueError(f"can't derive a filename from {source!r}")
    dest = os.path.join(fonts_abs, base)

    if source.lower().startswith(("http://", "https://")):
        # urllib honors HTTPS_PROXY/HTTP_PROXY from the environment. Corporate
        # proxies may need SSL_CERT_FILE pointed at their CA bundle.
        ctx = ssl.create_default_context()
        req = urllib.request.Request(source, headers={"User-Agent": "book-template/fetch-fonts"})
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r, open(dest, "wb") as out:
            shutil.copyfileobj(r, out)
    else:
        src_abs = source if os.path.isabs(source) else os.path.join(PROJECT_ROOT, source)
        if not os.path.exists(src_abs):
            raise FileNotFoundError(f"local source not found: {source}")
        shutil.copyfile(src_abs, dest)
    return base


def font_format(filename):
    return FORMATS.get(os.path.splitext(filename)[1].lower(), "truetype")


def face_rule(entry, filename):
    weight = entry["weight"].strip()
    return (
        "@font-face {\n"
        f"  font-family: '{entry['family']}';\n"
        f"  font-style: {entry['style']};\n"
        f"  font-weight: {weight};\n"
        f"  font-display: swap;\n"
        f"  src: url('{filename}') format('{font_format(filename)}');\n"
        "}\n"
    )


def main():
    argv = sys.argv[1:]
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    list_only = "--list" in argv

    entries = parse_manifest()
    if not entries:
        print(f"{MANIFEST} declares no fonts yet — add lines and re-run. See docs/FONTS.md.")
        sys.exit(0)

    if list_only:
        print(f"{MANIFEST} declares {len(entries)} font(s):")
        for e in entries:
            print(f"  {e['family']}  {e['weight']}  {e['style']}  ← {e['source']}")
        return

    rules, ok = [], 0
    for e in entries:
        try:
            fn = fetch_one(e["source"])
            rules.append(face_rule(e, fn))
            print(f"  ✓ {e['family']} {e['weight']} {e['style']} → {FONTS_DIR}/{fn}")
            ok += 1
        except Exception as ex:
            print(f"  ✗ {e['family']} {e['weight']} {e['style']}: {ex}")

    if not rules:
        print("\nNo fonts fetched. Fix the sources above (URL reachable? local path correct?).")
        sys.exit(1)

    header = ("/* Generated by scripts/fetch-fonts.py from fonts/fonts.txt.\n"
              "   Link this from src/master-header.html; set the family in design.css. */\n")
    out_abs = os.path.join(PROJECT_ROOT, OUT_CSS)
    with open(out_abs, "w") as f:
        f.write(header + "\n" + "\n".join(rules))
    print(f"\nWrote {OUT_CSS} ({ok}/{len(entries)} font(s)).")
    print(f"Next: add  <link rel=\"stylesheet\" href=\"{OUT_CSS}\">  to src/master-header.html")
    print(f"      and set the family in src/styles/design.css. See docs/FONTS.md.")


if __name__ == "__main__":
    main()
