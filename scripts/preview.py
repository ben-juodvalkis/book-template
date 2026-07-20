#!/usr/bin/env python3
"""
preview.py — live browser preview of a section for fast layout iteration.

Renders a section's wrapped HTML and serves it locally so you can eyeball layout,
color, and type in a browser without a full PDF render on every tweak. With
--watch, edits to the source are picked up automatically.

IMPORTANT: a browser is NOT WeasyPrint. Use this for quick layout/positioning
iteration; always confirm bleed, safe margins, and pagination in a real
`./book section` / `./book build` PDF before shipping.

Usage:
  ./book preview-web 01-title                 # serve, open a browser
  ./book preview-web 01-title --watch         # + auto-reload on source changes
  ./book preview-web 01-title --port 9000
  ./book preview-web 01-title --first-page 7  # preview at a book position (parity)

Ctrl-C to stop.
"""

import functools
import http.server
import os
import sys
import threading
import time
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _build import (  # noqa: E402
    PROJECT_ROOT, SPREADS_DIR, build_section_html, read, resolve_section,
)

PREVIEW_REL = ".temp/preview.html"
POLL_SECONDS = 0.5


def render_preview(src_rel, first_page, watch):
    """Write the wrapped section HTML to .temp/preview.html for serving.

    Injects <base href="/"> so the page's root-relative assets (src/styles/…,
    assets/…) resolve against the server root (PROJECT_ROOT). With watch, also
    injects a meta refresh so the browser reloads as the file is rebuilt.
    """
    html = build_section_html(read(src_rel), first_page_num=first_page)
    inject = '<base href="/">'
    if watch:
        inject += '\n<meta http-equiv="refresh" content="1">'
    html = html.replace("<head>", "<head>\n  " + inject, 1)
    out_abs = os.path.join(PROJECT_ROOT, PREVIEW_REL)
    os.makedirs(os.path.dirname(out_abs), exist_ok=True)
    with open(out_abs, "w") as f:
        f.write(html)


def watch_loop(src_rel, first_page, stop):
    """Rebuild the preview whenever the source file's mtime changes."""
    src_abs = os.path.join(PROJECT_ROOT, src_rel)
    last = None
    while not stop.is_set():
        try:
            m = os.path.getmtime(src_abs)
            if m != last:
                last = m
                render_preview(src_rel, first_page, watch=True)
        except OSError:
            pass
        time.sleep(POLL_SECONDS)


def parse_args(argv):
    opts = {"port": 8000, "watch": False, "first_page": 1, "section": None}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help"):
            print(__doc__)
            sys.exit(0)
        elif a == "--watch":
            opts["watch"] = True
            i += 1
        elif a in ("--port", "--first-page"):
            if i + 1 >= len(argv):
                print(f"Error: {a} needs a value")
                sys.exit(1)
            opts["port" if a == "--port" else "first_page"] = int(argv[i + 1])
            i += 2
        elif opts["section"] is None:
            opts["section"] = a
            i += 1
        else:
            print(f"Unknown argument: {a}")
            sys.exit(1)
    if opts["section"] is None:
        print("Error: a section is required, e.g. ./book preview-web 01-title")
        sys.exit(1)
    return opts


def main():
    opts = parse_args(sys.argv[1:])
    src_rel = resolve_section(opts["section"], SPREADS_DIR)
    if src_rel is None:
        print(f"Error: could not find section {opts['section']!r}")
        sys.exit(1)

    render_preview(src_rel, opts["first_page"], opts["watch"])

    stop = threading.Event()
    if opts["watch"]:
        threading.Thread(target=watch_loop, args=(src_rel, opts["first_page"], stop),
                         daemon=True).start()

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=PROJECT_ROOT)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", opts["port"]), handler)
    url = f"http://127.0.0.1:{opts['port']}/{PREVIEW_REL}"

    print(f"Serving {src_rel} at:\n  {url}")
    print("  (browser preview ≠ WeasyPrint — confirm print output in a PDF build)")
    if opts["watch"]:
        print("  --watch on: the browser reloads as you edit the source.")
    print("Ctrl-C to stop.")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        stop.set()
        httpd.server_close()


if __name__ == "__main__":
    main()
