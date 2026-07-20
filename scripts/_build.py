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

# ── Page geometry ────────────────────────────────────────────────────────────
# Built-in page-size presets for saddle-stitch POD (all values in INCHES, except
# dpi). A book selects one via `page_size = <name>` in book.config and may override
# any single field (see GEOMETRY_KEYS). These are the SINGLE SOURCE OF TRUTH for
# print geometry: the build injects them into every render as CSS custom properties
# (see geometry_css_vars), and print.css / design.css read them via var(). Verify
# each preset against your printer's current spec sheet before shipping.
PAGE_SIZE_PRESETS = {
    # ── Saddle-stitch photo books (Blurb-style) ──────────────────────────────
    "blurb-8x10": {  # Blurb 8×10 portrait — the template default
        "trim_width": 8.0, "trim_height": 10.0, "bleed": 0.125,
        "safe_binding": 0.5, "safe_outside": 0.5, "safe_top": 0.25, "safe_bottom": 0.25,
        "dpi": 300, "binding": "saddle-stitch",
    },
    "blurb-7x7": {  # Blurb 7×7 square
        "trim_width": 7.0, "trim_height": 7.0, "bleed": 0.125,
        "safe_binding": 0.5, "safe_outside": 0.5, "safe_top": 0.25, "safe_bottom": 0.25,
        "dpi": 300, "binding": "saddle-stitch",
    },
    "blurb-10x8-landscape": {  # Blurb 10×8 landscape
        "trim_width": 10.0, "trim_height": 8.0, "bleed": 0.125,
        "safe_binding": 0.5, "safe_outside": 0.5, "safe_top": 0.25, "safe_bottom": 0.25,
        "dpi": 300, "binding": "saddle-stitch",
    },
    "us-letter": {  # 8.5×11 portrait
        "trim_width": 8.5, "trim_height": 11.0, "bleed": 0.125,
        "safe_binding": 0.5, "safe_outside": 0.5, "safe_top": 0.25, "safe_bottom": 0.25,
        "dpi": 300, "binding": "saddle-stitch",
    },
    # ── Perfect-bound trade sizes (KDP / IngramSpark / Lulu share these) ──────
    # 0.125" bleed is the standard for US POD. The binding (gutter) safe margin
    # GROWS with page count on perfect-bound books — 0.5" here is a safe starting
    # value for books up to ~300 pages; increase safe_binding in book.config for
    # thicker books (KDP: 0.625" for 301–500pp, 0.75" for 501–700pp). Always verify
    # against your printer's current spec sheet.
    "trade-6x9": {  # 6×9 — the most common paperback
        "trim_width": 6.0, "trim_height": 9.0, "bleed": 0.125,
        "safe_binding": 0.5, "safe_outside": 0.375, "safe_top": 0.375, "safe_bottom": 0.375,
        "dpi": 300, "binding": "perfect-bound",
    },
    "trade-5x8": {  # 5×8 — compact paperback
        "trim_width": 5.0, "trim_height": 8.0, "bleed": 0.125,
        "safe_binding": 0.5, "safe_outside": 0.375, "safe_top": 0.375, "safe_bottom": 0.375,
        "dpi": 300, "binding": "perfect-bound",
    },
    "trade-5.5x8.5": {  # 5.5×8.5 — US digest
        "trim_width": 5.5, "trim_height": 8.5, "bleed": 0.125,
        "safe_binding": 0.5, "safe_outside": 0.375, "safe_top": 0.375, "safe_bottom": 0.375,
        "dpi": 300, "binding": "perfect-bound",
    },
    "trade-8.5x11": {  # 8.5×11 — manuals, workbooks, photo-heavy trade
        "trim_width": 8.5, "trim_height": 11.0, "bleed": 0.125,
        "safe_binding": 0.5, "safe_outside": 0.375, "safe_top": 0.375, "safe_bottom": 0.375,
        "dpi": 300, "binding": "perfect-bound",
    },
    "square-8.5x8.5": {  # 8.5×8.5 — square perfect-bound photo book
        "trim_width": 8.5, "trim_height": 8.5, "bleed": 0.125,
        "safe_binding": 0.5, "safe_outside": 0.375, "safe_top": 0.375, "safe_bottom": 0.375,
        "dpi": 300, "binding": "perfect-bound",
    },
}

# Service-named aliases for the canonical presets above. KDP, IngramSpark, and
# Lulu all print the same standard trim sizes, so these resolve to one geometry —
# pick whichever name you recognize. (Values still come from the target above;
# verify margins against the service's live spec sheet, especially the gutter.)
PAGE_SIZE_ALIASES = {
    "kdp-6x9": "trade-6x9",
    "ingramspark-6x9": "trade-6x9",
    "lulu-6x9": "trade-6x9",
    "kdp-5x8": "trade-5x8",
    "kdp-5.5x8.5": "trade-5.5x8.5",
    "lulu-5.5x8.5": "trade-5.5x8.5",
    "kdp-8.5x11": "trade-8.5x11",
    "kdp-square-8.5": "square-8.5x8.5",
}

DEFAULT_PAGE_SIZE = "blurb-8x10"

# Paper stock -> PPI (pages per inch), used to compute a perfect-bound spine:
#   spine_inches = page_count / ppi
# These are typical POD values; confirm against your printer/paper before print.
PAPER_STOCKS = {
    "white":        444,   # KDP white / standard 50–60# uncoated
    "cream":        370,   # KDP cream novel stock
    "standard-color": 400, # KDP standard-color paper
    "premium-color": 340,  # KDP premium-color / heavier photo stock
    "blurb-standard": 460, # Blurb standard paper (approx.)
}
DEFAULT_PAPER_PPI = PAPER_STOCKS["white"]
DEFAULT_BINDING = "saddle-stitch"

# Geometry fields a book may override individually in book.config. Length fields
# are in inches (accept `8`, `8in`, or `203mm`); dpi is an integer. Any field left
# unset inherits from the selected page_size preset.
GEOMETRY_LENGTH_KEYS = (
    "trim_width", "trim_height", "bleed",
    "safe_binding", "safe_outside", "safe_top", "safe_bottom",
)
GEOMETRY_KEYS = GEOMETRY_LENGTH_KEYS + ("dpi",)

# Defaults for book.config keys. A book overrides these in book.config.
CONFIG_DEFAULTS = {
    # Number of leading physical pages that carry NO printed folio (front matter:
    # opening page, blank, title, contents, etc.). Arabic numbering restarts at 1
    # on the first body page after them. 0 = number every page from 1 (simple book).
    "front_matter_pages": 0,
    # Page-size preset name (see PAGE_SIZE_PRESETS / PAGE_SIZE_ALIASES).
    "page_size": DEFAULT_PAGE_SIZE,
    # Binding style: "saddle-stitch" or "perfect-bound". None = inherit from the
    # selected preset. Drives the page-count sanity check and the cover/spine math.
    "binding_type": None,
    # Minimum page count the build warns below. None = a binding-aware default
    # (saddle-stitch 20, perfect-bound 24).
    "min_pages": None,
    # Perfect-bound spine math (see scripts/cover.py). paper_stock names a PAPER_STOCKS
    # entry; paper_ppi overrides it with an explicit pages-per-inch value.
    "paper_stock": None,
    "paper_ppi": None,
    # Per-field geometry overrides; None = inherit from the selected preset.
    **{k: None for k in GEOMETRY_KEYS},
}


def parse_length_in(val):
    """Parse a length like '8', '8in', '0.125in', or '203mm' → inches (float)."""
    s = str(val).strip().lower()
    if s.endswith("mm"):
        return float(s[:-2].strip()) / 25.4
    if s.endswith("in"):
        s = s[:-2].strip()
    return float(s)


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
            if key in ("front_matter_pages", "min_pages"):
                try:
                    val = int(val)
                except ValueError:
                    print(f"  {BOOK_CONFIG}: {key} must be an integer, got {val!r}; using default")
                    val = CONFIG_DEFAULTS[key]
            elif key in ("dpi", "paper_ppi"):
                try:
                    val = int(float(val))
                except ValueError:
                    print(f"  {BOOK_CONFIG}: {key} must be a number, got {val!r}; ignoring")
                    val = None
            elif key in GEOMETRY_LENGTH_KEYS:
                try:
                    val = parse_length_in(val)
                except ValueError:
                    print(f"  {BOOK_CONFIG}: {key} must be a length (e.g. 8in, 203mm), got {val!r}; ignoring")
                    val = None
            cfg[key] = val
    return cfg


def resolve_geometry(cfg):
    """Merge the selected page_size preset with any explicit book.config overrides.

    Returns a dict of base geometry values (inches, plus integer dpi). An unknown
    preset name falls back to DEFAULT_PAGE_SIZE with a warning.
    """
    name = cfg.get("page_size") or DEFAULT_PAGE_SIZE
    name = PAGE_SIZE_ALIASES.get(name, name)   # service-named aliases -> canonical
    if name not in PAGE_SIZE_PRESETS:
        print(f"  {BOOK_CONFIG}: unknown page_size {name!r}; using {DEFAULT_PAGE_SIZE!r}")
        name = DEFAULT_PAGE_SIZE
    base = dict(PAGE_SIZE_PRESETS[name])
    for k in GEOMETRY_KEYS:
        if cfg.get(k) is not None:
            base[k] = cfg[k]
    return base


def resolve_binding(cfg=None, geom=None):
    """Effective binding style: explicit book.config wins, else the preset's, else default."""
    cfg = cfg if cfg is not None else load_config()
    bt = cfg.get("binding_type")
    if bt:
        return bt
    geom = geom if geom is not None else geometry(cfg)
    return geom.get("binding") or DEFAULT_BINDING


def min_pages(cfg=None, binding=None):
    """Page-count floor the build warns below. Explicit book.config wins, else
    a binding-aware default (saddle-stitch 20, perfect-bound 24)."""
    cfg = cfg if cfg is not None else load_config()
    if cfg.get("min_pages") is not None:
        return cfg["min_pages"]
    binding = binding or resolve_binding(cfg)
    return 24 if binding == "perfect-bound" else 20


def resolve_ppi(cfg=None):
    """Pages-per-inch for the spine calc: explicit paper_ppi wins, else the named
    paper_stock, else the white-paper default. Unknown stock names warn."""
    cfg = cfg if cfg is not None else load_config()
    if cfg.get("paper_ppi"):
        return int(cfg["paper_ppi"])
    stock = cfg.get("paper_stock")
    if stock:
        if stock in PAPER_STOCKS:
            return PAPER_STOCKS[stock]
        print(f"  {BOOK_CONFIG}: unknown paper_stock {stock!r}; using white "
              f"({DEFAULT_PAPER_PPI} ppi). Known: {', '.join(PAPER_STOCKS)}")
    return DEFAULT_PAPER_PPI


def spine_width_in(page_count, ppi):
    """Perfect-bound spine width in inches = page_count / pages-per-inch."""
    return page_count / float(ppi)


def cover_geometry(page_count, cfg=None):
    """Derived geometry for a perfect-bound wraparound cover (ONE flat sheet).

    Layout across the sheet: [outside bleed | BACK cover | SPINE | FRONT cover |
    outside bleed], full trim height plus top/bottom bleed. Keys (inches):
      spine_w                 page_count / ppi
      cover_trim_w/h          flat cover trim (2*trim + spine) x trim_h
      cover_div_w/h           the .cover element incl. bleed on all four sides
      back_w / front_w        panel widths incl. their one outside bleed
      ppi                     pages-per-inch used
    Also carries through trim_width/height, bleed, and the safe insets so the
    cover render reuses the same var() names as the interior.
    """
    cfg = cfg if cfg is not None else load_config()
    g = geometry(cfg)
    tw, th, bl = g["trim_width"], g["trim_height"], g["bleed"]
    ppi = resolve_ppi(cfg)
    spine = spine_width_in(page_count, ppi)
    d = dict(g)
    d.update({
        "page_count": page_count,
        "ppi": ppi,
        "spine_w": spine,
        "cover_trim_w": 2 * tw + spine,
        "cover_trim_h": th,
        "cover_div_w": 2 * tw + spine + 2 * bl,
        "cover_div_h": th + 2 * bl,
        "back_w": tw + bl,     # back panel incl. its outside (left) bleed
        "front_w": tw + bl,    # front panel incl. its outside (right) bleed
    })
    return d


def cover_css_vars(cov):
    """:root custom properties for the cover render (mirrors geometry_css_vars)."""
    v = cov
    return (
        "<style>\n"
        "/* Cover geometry — generated from book.config + page count by scripts/cover.py. */\n"
        ":root {\n"
        f"  --trim-w: {_css_in(v['trim_width'])}; --trim-h: {_css_in(v['trim_height'])}; --bleed: {_css_in(v['bleed'])};\n"
        f"  --spine-w: {_css_in(v['spine_w'])};\n"
        f"  --cover-trim-w: {_css_in(v['cover_trim_w'])}; --cover-trim-h: {_css_in(v['cover_trim_h'])};\n"
        f"  --cover-div-w: {_css_in(v['cover_div_w'])}; --cover-div-h: {_css_in(v['cover_div_h'])};\n"
        f"  --back-w: {_css_in(v['back_w'])}; --front-w: {_css_in(v['front_w'])}; --page-margin: {_css_in(-v['bleed'])};\n"
        f"  --safe-binding: {_css_in(v['css_safe_binding'])}; --safe-outside: {_css_in(v['css_safe_outside'])};\n"
        f"  --safe-top: {_css_in(v['css_safe_top'])}; --safe-bottom: {_css_in(v['css_safe_bottom'])};\n"
        "}\n"
        "</style>"
    )


def geometry(cfg=None):
    """Full derived print geometry (inches) from book.config — ONE source of truth.

    Everything the CSS and the image tools need is computed here. Derived values:
      div_w/div_h     the .page div (trim + bleed on all four sides; the binding
                      overhang is clipped by WeasyPrint, giving no bleed at the fold)
      page_margin     the negative margin that pushes .page into the bleed
      page_w/page_h   the final per-side PDF page (trim + outside/top/bottom bleed)
      css_safe_*      safe insets measured from the .page div EDGE = safe-from-trim
                      + one bleed (the div overhangs trim by `bleed` on every side)
      spread_w/h      the full flat two-page spread incl. both outside bleeds
      spread_recto_x  background-position-x for the right page of a spread photo
                      (= -trim_width; see the .spread-photo classes in design.css)
    """
    cfg = cfg if cfg is not None else load_config()
    g = resolve_geometry(cfg)
    tw, th, bl = g["trim_width"], g["trim_height"], g["bleed"]
    sb, so = g["safe_binding"], g["safe_outside"]
    st, sbo = g["safe_top"], g["safe_bottom"]
    d = dict(g)
    d.update({
        "div_w": tw + 2 * bl,
        "div_h": th + 2 * bl,
        "page_margin": -bl,
        "page_w": tw + bl,
        "page_h": th + 2 * bl,
        "css_safe_binding": sb + bl,
        "css_safe_outside": so + bl,
        "css_safe_top": st + bl,
        "css_safe_bottom": sbo + bl,
        "css_safe_max": max(sb, so) + bl,
        "spread_w": 2 * (tw + bl),
        "spread_h": th + 2 * bl,
        "spread_recto_x": -tw,
    })
    return d


def _css_in(x):
    """Format an inch value as a CSS length, trimming trailing zeros."""
    s = f"{x:.4f}".rstrip("0").rstrip(".")
    return (s or "0") + "in"


def geometry_css_vars(geom):
    """The <style> block of :root custom properties injected into every render.

    print.css and design.css consume these via var(). It is injected into <head>
    so that @page rules (which also use var()) resolve — verified on WeasyPrint 69,
    which resolves var() inside @page and across separate stylesheets.
    """
    v = geom
    return (
        "<style>\n"
        "/* Print geometry — generated from book.config by scripts/_build.py.\n"
        "   SINGLE SOURCE OF TRUTH: change book.config, never these values. */\n"
        ":root {\n"
        f"  --trim-w: {_css_in(v['trim_width'])}; --trim-h: {_css_in(v['trim_height'])}; --bleed: {_css_in(v['bleed'])};\n"
        f"  --div-w: {_css_in(v['div_w'])}; --div-h: {_css_in(v['div_h'])}; --page-margin: {_css_in(v['page_margin'])};\n"
        f"  --safe-binding: {_css_in(v['css_safe_binding'])}; --safe-outside: {_css_in(v['css_safe_outside'])};\n"
        f"  --safe-top: {_css_in(v['css_safe_top'])}; --safe-bottom: {_css_in(v['css_safe_bottom'])}; --safe-max: {_css_in(v['css_safe_max'])};\n"
        f"  --spread-w: {_css_in(v['spread_w'])}; --spread-h: {_css_in(v['spread_h'])}; --spread-recto-x: {_css_in(v['spread_recto_x'])};\n"
        "}\n"
        "</style>"
    )


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
    # Branch names routinely contain '/' (e.g. "claude/foo", "feature/bar").
    # Left as-is that turns builds/<slug>/master-<slug>.pdf into an unintended
    # nested path (master-claude/...pdf) whose directory doesn't exist, and the
    # merge save fails. Flatten separators so the slug is always one path segment.
    branch = branch.replace("/", "-").replace(os.sep, "-")
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


def spread_photo_parity_warnings(html, first_page_num):
    """Warn if a full-spread (cross-gutter) photo half lands on the wrong hand.

    A `.spread-photo-verso` half must be a LEFT-hand (even) page and a
    `.spread-photo-recto` half a RIGHT-hand (odd) page facing it; otherwise the
    photo is split across a page TURN instead of a facing spread. Returns a list
    of human-readable warning strings (empty if all good).
    """
    warnings = []
    classes = re.findall(r'<div[^>]*\bclass="([^"]*\bpage\b[^"]*)"', html)
    for i, cls in enumerate(classes):
        gp = first_page_num + i
        if "spread-photo-verso" in cls and gp % 2 == 1:
            warnings.append(
                f"spread-photo-verso on page {gp} (a RIGHT-hand/odd page) — the verso half "
                f"must be a LEFT-hand/even page, or the photo splits across a page turn."
            )
        if "spread-photo-recto" in cls and gp % 2 == 0:
            warnings.append(
                f"spread-photo-recto on page {gp} (a LEFT-hand/even page) — the recto half "
                f"must be a RIGHT-hand/odd page facing its verso."
            )
    return warnings


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
  bleed-left:   var(--bleed) !important;
  bleed-right:  0            !important;
}
@page :left {
  bleed-left:   0            !important;
  bleed-right:  var(--bleed) !important;
}
""")

    return "<style>\n" + "\n".join(parts) + "\n</style>"


def build_section_html(fragment, first_page_num=1, front_matter_pages=0, cfg=None):
    """Wrap a spread fragment with header + geometry vars + per-section style + footer.

    The geometry custom properties (from book.config) are injected into <head> so
    print.css/design.css var() references — including inside @page — resolve. cfg
    is loaded from book.config when not supplied, so the single-section/page build
    scripts pick up the book's geometry without threading it through.
    """
    cfg = cfg if cfg is not None else load_config()
    geom = geometry(cfg)
    header = read(HEADER)
    footer = read(FOOTER)
    geo_style = geometry_css_vars(geom)
    if "</head>" in header:
        header = header.replace("</head>", geo_style + "\n</head>", 1)
    else:
        header = header + "\n" + geo_style
    style = per_section_style(first_page_num, front_matter_pages)
    fragment = strip_outer_tags(fragment)
    return header + "\n" + style + "\n" + fragment + "\n" + footer


def weasyprint_render(html_path, pdf_path):
    """Run WeasyPrint. Returns (success: bool, stderr: str).

    Invoked as `<this-interpreter> -m weasyprint` rather than a bare `weasyprint`
    CLI so the render always uses the same Python that's running the build — it
    works whether or not the virtualenv is activated, and needs no console script
    on PATH. (`python -m weasyprint` is equivalent to the CLI.)
    """
    result = subprocess.run(
        [sys.executable, "-m", "weasyprint", "--base-url", PROJECT_ROOT, html_path, pdf_path],
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
