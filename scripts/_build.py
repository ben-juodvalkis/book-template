"""
_build.py — shared rendering primitives for the print-book build pipeline.

Asymmetric bleed (0.125" top/bottom/outside, none at binding), 0.5" outside-edge
safe margin. Geometry lives in src/styles/print.css. Build outputs are written
under builds/<branch>-<commit>/ — see build_paths().
"""

import os
import re
import subprocess
import sys

# Scripts live in scripts/; the project root is one level up. All relative paths
# (src/, builds/, book.spreads) are resolved against this.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

HEADER = "src/master-header.html"
FOOTER = "src/master-footer.html"

SPREADS_DIR = "src/spreads"
SPREADS_CONFIG = "book.spreads"
BOOK_CONFIG = "book.config"

BUILDS_DIR = "builds"

# Defaults for book.config keys. A book overrides these in book.config.
CONFIG_DEFAULTS = {
    # Number of leading physical pages that carry NO printed folio (front matter:
    # opening page, blank, title, contents, etc.). Arabic numbering restarts at 1
    # on the first body page after them. 0 = number every page from 1 (simple book).
    "front_matter_pages": 0,
}


def load_config():
    """Return the book's config dict, merging book.config over CONFIG_DEFAULTS.

    book.config is optional. Format: one `key = value` per line; blank lines and
    `#` comments ignored. Integer-valued keys are parsed as ints. Unknown keys are
    kept (forward-compatible) but a warning is printed so typos are visible.
    """
    cfg = dict(CONFIG_DEFAULTS)
    path = os.path.join(PROJECT_ROOT, BOOK_CONFIG)
    if not os.path.exists(path):
        return cfg
    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                print(f"  {BOOK_CONFIG}: ignoring malformed line (no '='): {line!r}")
                continue
            key, val = (s.strip() for s in line.split("=", 1))
            if key not in CONFIG_DEFAULTS:
                print(f"  {BOOK_CONFIG}: warning — unknown key {key!r} (kept anyway)")
            if isinstance(CONFIG_DEFAULTS.get(key), int):
                try:
                    val = int(val)
                except ValueError:
                    print(f"  {BOOK_CONFIG}: {key} must be an integer, got {val!r}; using default")
                    val = CONFIG_DEFAULTS[key]
            cfg[key] = val
    return cfg


def load_spreads():
    """Return the ordered list of spread paths for the full-book build.

    Reads `book.spreads` (one path per line, relative to the project root).
    Blank lines and lines beginning with `#` are ignored, so the file can be
    commented and visually grouped. The order of lines is the page order of
    the book. This is the ONE file a new book edits to wire up its sections —
    the build scripts themselves stay book-agnostic.
    """
    path = os.path.join(PROJECT_ROOT, SPREADS_CONFIG)
    if not os.path.exists(path):
        print(f"Error: {SPREADS_CONFIG} not found at {path}")
        print(f"  Create it with one spread path per line, e.g. {SPREADS_DIR}/01-title.html")
        sys.exit(1)
    spreads = []
    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            spreads.append(line)
    if not spreads:
        print(f"Error: {SPREADS_CONFIG} lists no spreads (all blank/comments).")
        sys.exit(1)
    missing = [s for s in spreads if not os.path.exists(os.path.join(PROJECT_ROOT, s))]
    if missing:
        print(f"Error: {SPREADS_CONFIG} references {len(missing)} missing file(s):")
        for m in missing:
            print(f"  {m}")
        sys.exit(1)
    return spreads


def build_slug():
    """`<branch>-<commit>` for the current git state, e.g. `main-fcbfb7d`.

    Falls back to `nogit` for either part if git is unavailable. Plain commit
    hash even with a dirty tree (no `-dirty` suffix), by project convention.
    """
    def git(*args, default):
        try:
            out = subprocess.run(
                ["git", *args], cwd=PROJECT_ROOT,
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            return out or default
        except (subprocess.CalledProcessError, FileNotFoundError):
            return default

    branch = git("rev-parse", "--abbrev-ref", "HEAD", default="nogit")
    commit = git("rev-parse", "--short", "HEAD", default="nogit")
    return f"{branch}-{commit}"


def build_paths(slug=None):
    """Return the per-build output paths, all under builds/<slug>/.

    Keys: dir, sections_dir, master, trimmed, trimmed_draft, stem.
    `stem` is `master-<slug>` for composing other names. Paths are relative to
    PROJECT_ROOT (join with it when passing to file I/O).
    """
    slug = slug or build_slug()
    out_dir = os.path.join(BUILDS_DIR, slug)
    stem = f"master-{slug}"
    return {
        "slug": slug,
        "dir": out_dir,
        "sections_dir": os.path.join(out_dir, "sections"),
        "stem": stem,
        "master": os.path.join(out_dir, f"{stem}.pdf"),
        "trimmed": os.path.join(out_dir, f"{stem}-trimmed.pdf"),
        "trimmed_draft": os.path.join(out_dir, f"{stem}-trimmed-draft.pdf"),
    }


def read(path):
    with open(os.path.join(PROJECT_ROOT, path)) as f:
        return f.read()


def write(path, content):
    full = os.path.join(PROJECT_ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)


def count_page_divs(html):
    """Count top-level <div class='page ...'> elements in a spread fragment."""
    return len(re.findall(r'<div[^>]+class="[^"]*\bpage\b[^"]*"', html))


def strip_outer_tags(html):
    """Remove <html>, <head>, <body> wrappers from a fragment if present."""
    html = re.sub(r'(?s)<html[^>]*>.*?</head>', '', html)
    html = re.sub(r'<body[^>]*>', '', html)
    html = re.sub(r'</body>', '', html)
    html = re.sub(r'</html>', '', html)
    return html.strip()


def per_section_style(first_page_num, front_matter_pages=0):
    """
    Build the per-section <style> block injected before the spread fragment.

    1. counter-reset sets the displayed folio. By default (front_matter_pages=0)
       a page's folio equals its physical position, numbering from 1. If the book
       has unnumbered front matter, set `front_matter_pages` (see book.config):
       the first N physical pages carry no printed folio and arabic numbering
       restarts at 1 on the first body page. The displayed folio is then physical
       position minus N, so the counter-reset value is
       `first_page_num - 1 - front_matter_pages`. Front-matter pages compute a
       zero/negative counter (never shown — those pages use `.no-number`), and the
       first body page lands on 1.

    2. CANONICAL ORIENTATION (do not paraphrase): page 1 is a RIGHT-hand page.
       Odd pages = RIGHT-hand (binding LEFT, bleed RIGHT/outside); even pages =
       LEFT-hand (binding RIGHT, bleed LEFT/outside). WeasyPrint assigns the first
       physical page of every render to the CSS `:right` selector, so `@page :right`
       styles an ODD / RIGHT-hand page and `@page :left` styles an EVEN / LEFT-hand
       page — here the selector name matches the physical hand.

       When a section starts on an even (LEFT-hand) page, WeasyPrint's physical
       :left/:right alternation is off by one — its first physical page is :right
       (which our base CSS styles as odd/RIGHT-hand, bleeding RIGHT) but this
       section's first page is even/LEFT-hand and must bleed LEFT. We swap the
       per-side bleed definitions so the asymmetric bleed lands on the correct
       (outside) edge for this section's parity.

       (Backgrounds and other @page properties are not swapped — only the
       bleed geometry is parity-dependent.)
    """
    parts = [f"body {{ counter-reset: page-num {first_page_num - 1 - front_matter_pages}; }}"]

    if first_page_num % 2 == 0:
        # Section starts on an even / LEFT-hand page. Mirror of the base CSS so the
        # outside edge (LEFT for a left-hand page) bleeds: physical :right bleeds
        # LEFT, physical :left bleeds RIGHT.
        parts.append("""
@page :right {
  bleed-left:   0.125in !important;
  bleed-right:  0       !important;
}
@page :left {
  bleed-left:   0       !important;
  bleed-right:  0.125in !important;
}
""")

    return "<style>\n" + "\n".join(parts) + "\n</style>"


def build_section_html(fragment, first_page_num=1, front_matter_pages=0):
    """Wrap a spread fragment with header + per-section style + footer."""
    header = read(HEADER)
    footer = read(FOOTER)
    style = per_section_style(first_page_num, front_matter_pages)
    fragment = strip_outer_tags(fragment)
    return header + "\n" + style + "\n" + fragment + "\n" + footer


def weasyprint_render(html_path, pdf_path):
    """Run WeasyPrint. Returns (success: bool, stderr: str)."""
    result = subprocess.run(
        ["weasyprint", "--base-url", PROJECT_ROOT, html_path, pdf_path],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stderr


def merge_pdfs(pdf_paths, out_path):
    """Merge a list of PDFs into one. Preserves per-page MediaBox / asymmetric bleed."""
    import pikepdf
    out = pikepdf.Pdf.new()
    for p in pdf_paths:
        with pikepdf.open(p) as src:
            out.pages.extend(src.pages)
    out.Root.PageLayout = pikepdf.Name("/TwoPageRight")
    out.save(out_path)


def resolve_section(arg, spreads_dir):
    """Accept a bare name (09-feral), name with .html, or full path."""
    if os.path.exists(os.path.join(PROJECT_ROOT, arg)):
        return arg
    with_ext = arg if arg.endswith('.html') else arg + '.html'
    candidate = os.path.join(spreads_dir, with_ext)
    if os.path.exists(os.path.join(PROJECT_ROOT, candidate)):
        return candidate
    return None


def extract_pages(html, page_indices):
    """
    Extract specific .page divs (0-based indices) plus the preamble (style blocks).

    Splits the fragment at top-level <div class='page ...'> boundaries and
    returns preamble + selected pages.
    """
    first = re.search(r'<div[^>]+class="[^"]*\bpage\b[^"]*"', html)
    if first is None:
        return html

    preamble = html[:first.start()]

    starts = [m.start() for m in re.finditer(r'<div[^>]+class="[^"]*\bpage\b[^"]*"', html)]
    blocks = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(html)
        blocks.append(html[s:e].rstrip())

    for idx in page_indices:
        if idx < 0 or idx >= len(blocks):
            print(f"Error: page {idx + 1} does not exist (file has {len(blocks)} page(s))")
            sys.exit(1)

    return preamble + "\n".join(blocks[i] for i in page_indices)


def parse_page_range(spec):
    """Parse '2' or '2-4' into a 0-based index list."""
    spec = spec.strip()
    m_range = re.fullmatch(r'(\d+)-(\d+)', spec)
    m_single = re.fullmatch(r'(\d+)', spec)
    if m_range:
        lo, hi = int(m_range.group(1)), int(m_range.group(2))
        if lo < 1 or hi < lo:
            print(f"Error: invalid page range '{spec}'")
            sys.exit(1)
        return list(range(lo - 1, hi))
    if m_single:
        n = int(m_single.group(1))
        if n < 1:
            print("Error: --page must be >= 1")
            sys.exit(1)
        return [n - 1]
    print(f"Error: invalid --page value '{spec}' — expected N or N-M")
    sys.exit(1)
