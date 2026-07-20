# CLAUDE.md — Print Book Template

A starter for print-ready books designed in HTML/CSS and printed via a
saddle-stitched POD printer (Blurb by default). Rendered with WeasyPrint and
merged with pikepdf into a Blurb-spec PDF. Read this before touching anything.

> **This is a template.** When starting a real book: set the title and fonts in
> `src/master-header.html`, the palette in `src/styles/design.css`, replace the
> stub spreads in `src/spreads/`, and edit `book.spreads` to list your sections
> in page order. Set the page size (trim, bleed, safe margins) in `book.config`;
> the geometry rules in `src/styles/print.css` and the build scripts in `scripts/`
> should not need changing.

---

## The Pipeline

```
src/spreads/*.html  →  ./book build  →  builds/<branch>-<commit>/master-<branch>-<commit>.pdf  →  printer
```

The build renders each spread to its own PDF via WeasyPrint, then merges them
with pikepdf. No master-HTML stitching, no `@page` renumbering, no post-export
crop — WeasyPrint produces the bleed page size natively via per-side bleed in
`src/styles/print.css`. See
`docs/adr/0001-per-section-render-and-native-asymmetric-bleed.md`.

**Which sections build, and in what order, is defined entirely by `book.spreads`**
(one spread path per line, in page order; `#` comments and blank lines ignored).
The scripts read it via `_build.load_spreads()` — you never edit a Python list.

**Toolchain** — the build needs Python 3 with `weasyprint`, `pikepdf`, and
`Pillow`, plus WeasyPrint's own system libraries (Pango et al., which pip can't
install). The recommended, cross-platform setup is a virtualenv:

```
python3 -m venv .venv
. .venv/bin/activate                 # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Then drive everything through the `./book` CLI (below); it auto-selects `.venv`
even when the venv isn't activated, and `./book doctor` verifies the toolchain.
On macOS the Homebrew WeasyPrint formula still works — point the CLI at its
interpreter via `BOOK_PYTHON`:
`BOOK_PYTHON="$(ls -d /opt/homebrew/Cellar/weasyprint/*/libexec/bin/python3.*)" ./book build`.
The shareable-draft builder also needs `mutool` (`brew install mupdf-tools` /
`apt install mupdf-tools`). The full build's safe-margin check uses `pdftotext`
(`brew install poppler` / `apt install poppler-utils`); if it's missing the check
is skipped with a warning rather than failing the build. The included `Dockerfile`
bundles all of this for a known-good build on any OS.

### Commands

```
./book init                  # turn the demo into a fresh book (run once after cloning)
./book build                 # render all sections + merge → builds/<slug>/
./book build --no-trim       # master PDF only (skip trimmed + draft)
./book build --html-only     # write per-section wrapped HTML, skip render

./book section 01-title           # one section → .temp/
./book page    01-title --page 2  # one page (or 2-4) → .temp/
./book trimmed                    # trim-cropped preview + draft (alias: preview)
./book draft                      # small shareable rasterized draft
./book cover --pages 120          # perfect-bound cover; spine = pages ÷ paper ppi
./book generate gallery assets/trip # photo-grid spread pages from a folder of images
./book spread-photo assets/raw.jpg  # prep a cross-gutter photo → assets/raw-spread.jpg
./book fonts                      # self-host fonts (fonts/fonts.txt → fonts/fonts.css)
./book preview-web 01-title --watch # live browser preview of a section (layout iteration)
./book doctor                     # check the toolchain (Python libs + optional tools)
./book test                       # run the geometry/helper test suite (needs pytest)
```

`./book <cmd>` just forwards to the matching `scripts/master-*.py` with the right
interpreter; run those directly (`python scripts/master-build.py`) if you prefer.
Windows users without a POSIX shell can use `book.cmd <cmd>` or `python book.py <cmd>`.

The single-section/page iteration commands share these flags: `--first-page N`
(preview at a real book position so odd/even bleed parity matches the final book —
defaults to 1), `--out PATH` (override the `.temp/` destination), and `--html-only`
(write the wrapped HTML, skip the WeasyPrint render). A section/page argument may be
a bare name (`01-title`), a name with `.html`, or a full path. `./book page`
requires `--page N` or `--page N-M` (1-based).

Output lands in `builds/<branch>-<commit>/` — each branch/commit gets its own
self-labeled folder, with the final/trimmed/draft PDFs at its top level and the
per-section PDFs and wrapped HTML under `sections/`. `builds/` is gitignored. The
trimmed/draft PDFs are for screen review only — never submit them to the printer.

Shared rendering logic lives in `scripts/_build.py`.

---

## How the Build Works — Page Size & Bleed

> **CANONICAL ORIENTATION (do not paraphrase):**
> Page 1 is a RIGHT-hand page — the first interior page of a bound book is always
> a right-hand recto. **Odd pages = RIGHT-hand (binding on LEFT, bleed on
> RIGHT/outside). Even pages = LEFT-hand (binding on RIGHT, bleed on LEFT/outside).**
> WeasyPrint assigns the first physical page of every render to the CSS `:right`
> selector, so in this project **`@page :right` styles an ODD / RIGHT-hand page**
> and **`@page :left` styles an EVEN / LEFT-hand page** — here the selector name
> matches the physical hand. Reason from odd/even + physical hand, and remember
> **bleed always goes on the OUTSIDE edge.**

**Geometry comes from `book.config`.** Trim size, bleed, and safe margins are set
there (a `page_size` preset plus optional per-field overrides) and injected into
every render as CSS custom properties; `print.css` and `design.css` consume them via
`var()`. The values below are the `blurb-8x10` default — to change size, edit
`book.config`, not the CSS. `scripts/_build.py` (`geometry()`) is the single place
the numbers are computed.

`print.css` declares asymmetric bleed via per-side properties on `:left`/`:right`
page selectors. After merge, `master-build.py` runs two guards: `assert_bleed_parity()`
FAILS the build if page 1 isn't bleeding RIGHT (and page 2 LEFT), and
`assert_safe_margins()` measures rendered text ink against the trim box and reports
anything crossing the binding/outside safe zone (real FOLD/OUTSIDE violations print
as errors; near-edge TOP/BOTTOM hits print as warnings, since big display titles
report phantom font-box bounds). Trust the parity guard absolutely.

When a spread starts on an even / LEFT-hand page, the build injects a CSS swap
of `:left`/`:right` bleed so WeasyPrint's physical-page alternation lands the
bleed on the correct (outside) side.

The `.page` div is sized 8.25×10.25" with `margin: -0.125in` so it extends into
all four bleed regions; WeasyPrint clips it at the asymmetric page edge, so the
binding gets no bleed. This is what lets `background-color`/`background-image` on
`.page` reach the outside bleed.

---

## Front matter & page numbering

By default every page prints its physical position as the folio, numbering from 1.
Many books instead want **unnumbered front matter** (opening page, blank, title,
contents) with **arabic numbers restarting at 1 on the first body page**. Set that
up with `book.config`:

```
front_matter_pages = 5
```

This shifts the *displayed* folio by N (displayed = physical − N), so the body's
first page prints "1". It does NOT suppress the folio by itself — you must also:

1. Put `.no-number` on the `.page-number` span of every front-matter page.
2. Count N correctly: e.g. opening page (1) + blank (1) + title (1) + contents (2)
   = `front_matter_pages = 5`.
3. Make any in-book page references (a contents list, photo credits) use the
   **displayed** body folios, not physical positions.

**Single opening page** (title/logo alone on the right, nothing facing it): because
page 1 is a RIGHT-hand recto, make the title page 1 and follow it with a blank
(page 2, a LEFT-hand verso). Use `src/spreads/_blank.html`. If the title shares a
file with another page, put the blank `.page` div *inside* that file in the right
spot — a separate `book.spreads` entry lands after the whole section, not mid-file.
Remember the total must stay EVEN for saddle stitch; a trailing blank (or a
full-bleed closing page) absorbs the odd page a leading blank introduces.

---

## Binding, page sizes & covers

`book.config` picks a `page_size` preset and a `binding_type`. Presets cover
saddle-stitch photo books (`blurb-*`, `us-letter`) and perfect-bound trade sizes
(`trade-6x9`, `trade-5.5x8.5`, …); service-named aliases (`kdp-6x9`,
`ingramspark-6x9`, `lulu-6x9`, …) resolve to the same geometry. Binding is
inherited from the preset unless set explicitly, and drives two things:

- **Page-count check** — saddle-stitch wants multiples of 4 (the build warns on
  odd; imposition detail noted in `book.config`); perfect-bound needs an even
  count and a binding safe margin that grows with thickness.
- **Cover/spine** — `./book cover --pages N` renders a perfect-bound wraparound
  cover (back + spine + front) as one flat sheet. Spine width = `page_count ÷
  paper_ppi` (name a `paper_stock` or pass `--ppi`). Geometry is computed in
  `_build.cover_geometry`; layout is `src/styles/cover.css`, content is
  `src/cover/cover.html`. The cover render is symmetric-bleed and standalone — it
  does NOT use `print.css`.

The safe-margin guard reads its thresholds from the resolved geometry, so it's
correct for every preset (not hardcoded to Blurb's 0.5"/0.25").

---

## Generating content, fonts & preview

- **`./book generate gallery <dir>`** writes a spread file of photo-grid pages
  from a folder of images (chunked N-per-page via the `.photo-grid` component in
  design.css). The output is a normal spread — add it to `book.spreads`. Extend
  `scripts/generate.py` with more `gen_*` generators (the pattern is one function
  returning page HTML).
- **`./book fonts`** self-hosts fonts from `fonts/fonts.txt` into `fonts/fonts.css`
  for reproducible/offline/CI renders (the default header uses a CDN, which is
  not reproducible). See `docs/FONTS.md`.
- **`./book preview-web <section> --watch`** serves a section in a browser for
  fast layout iteration. A browser is NOT WeasyPrint — always confirm bleed, safe
  margins, and pagination in a PDF build before shipping.

---

## Non-Negotiable Print Rules

**Page dimensions (Blurb 8×10 default — set trim/bleed/safe margins in `book.config`)**
- Trim: 8.0×10.0" portrait; final PDF page: 8.125×10.25" (bleed)
- Safe margins from trim: binding 0.5", outside 0.5", top/bottom 0.25"
- **CSS safe-zone thresholds (measured from the `.page` div edge):** the div
  overhangs trim by 0.125" on ALL FOUR sides (including the binding, where
  WeasyPrint just clips it). So every inset is 0.125" closer to trim than nominal,
  and content must be **≥ 0.625in** from the div edge on binding AND outside to
  clear 0.5" from trim; **≥ 0.375in** top/bottom. Use the `.safe`, `.safe-left`,
  `.safe-right` helpers in `print.css`. Measure ink, not CSS, when in doubt.
- Account for corner displacement on `transform: rotate()` elements (~0.7in from
  the div edge for rotated cards).
- Never use `vw`, `vh`, or any viewport units — use `in`, `mm`, or `pt`.
- Do NOT add `bleed:` or `size:` to per-spread `@page` rules — `print.css` owns
  those via `!important`. Per-spread `@page p1 { background-color: ... }` is the
  intended pattern.

**Bleed images** — use `background-image` on `.page` (not `<img>`), with a
matching `background-color` fallback. No pre-expanded `-bleed.jpg` needed; the
`.page` overhang carries the image into the bleed. Aim for ≥300 DPI at print size
(~2476×3076px for a full 8×10 bleed page).

**Color** — all black (text and graphics) must be `#000000` (pure K). Never use
near-black RGB like `#232023` (exceeds 300% TAC after CMYK). Soft-proof every
saturated color in Acrobat with your printer's ICC before committing.

**CSS to never use** — no hover/animation/transition, no `position: fixed`, no
viewport units.

---

## Adding a section

1. Copy a stub in `src/spreads/` (`02-photo-spread.html` for full-bleed photos,
   `03-color-spread.html` for solid-color collage pages) to `NN-name.html`.
2. Fill in content inside the `.safe*` wrappers.
3. Add the path to `book.spreads` in the right position.
4. `./book section NN-name` to preview, then a full build (`./book build`).
5. Keep the total page count EVEN for saddle-stitch (the build warns if it's odd).

For a **full-spread (cross-gutter) photo** — one image across both facing pages —
copy `04-spread-photo.html`, prep the image with `./book spread-photo
assets/your.jpg` (fills without stretching; `--focus`/`--zoom` control the crop), and
point both pages at the output. The section must start on an even page (verso); the
build warns if a spread photo lands on the wrong hand. See `docs/DESIGN-LANGUAGE.md`
and ADR 0002 (`docs/adr/`).

---

## File Hygiene

- Never write temp files, screenshots, or debug output to the project root.
- Screenshots → `.screenshots/`, other temp files → `.temp/` (both gitignored).
- Put photos in `assets/` (gitignored except the placeholder); the printer ICC in
  `printer-specs/` (gitignored).

---

## Key Files

| File | Purpose |
|---|---|
| `book.spreads` | **Ordered section list** — the one file you edit to wire up the book |
| `book.config` | Per-book settings: **page size / bleed / safe margins** (preset + overrides) and `front_matter_pages`. Single source of truth for geometry |
| `book` / `book.py` | The CLI you run (`./book build`, `./book doctor`, …); dispatches to the scripts with the right interpreter. `book.cmd` is the Windows shim |
| `scripts/init.py` | `./book init` — set title/page-size/license and reset `book.spreads` for a fresh book |
| `requirements.txt` / `requirements-dev.txt` | Pinned build deps (`weasyprint`, `pikepdf`, `Pillow`); dev adds `pytest` |
| `Dockerfile` | Known-good, cross-platform build environment (also bundles the system libraries and `mutool`/`pdftotext`) |
| `src/spreads/_blank.html` | Reusable blank page (single-opening-page + even-count padding) |
| `src/spreads/04-spread-photo.html` | Cross-gutter photo stub — one image across both facing pages |
| `scripts/master-build.py` | Full-book build (per-section render + merge + parity/margin checks) |
| `scripts/master-build-trimmed.py` | Trim-cropped 8×10 preview + shareable draft (review only) |
| `scripts/master-build-draft.py` | Rasterize any build PDF → small shareable draft |
| `scripts/master-build-section.py` | Single-section build for iteration |
| `scripts/master-build-page.py` | Single-page build for iteration |
| `scripts/spread-photo.py` | Cover-crop a photo to the spread aspect ratio for a cross-gutter image |
| `scripts/cover.py` | Render a perfect-bound cover; spine width from page count ÷ paper ppi |
| `scripts/generate.py` | Data-driven spreads (`generate gallery <dir>` → photo-grid pages) |
| `scripts/fetch-fonts.py` | Self-host fonts (`fonts/fonts.txt` → `fonts/fonts.css`) for reproducible renders |
| `scripts/preview.py` | Live browser preview of a section (`preview-web`, layout iteration only) |
| `fonts/` | Self-hosted fonts + manifest (`fonts.txt`) + generated `fonts.css`; see `docs/FONTS.md` |
| `scripts/_build.py` | Shared rendering primitives + `load_spreads()` + geometry/`load_config()` + presets/aliases + spine/cover math + `builds/<slug>/` scheme |
| `tests/` | pytest suite for the geometry/spine math and build helpers (`./book test`) |
| `src/cover/cover.html` / `src/styles/cover.css` | Perfect-bound cover content + layout (standalone; not print.css) |
| `src/spreads/` | Spread source files (start from the stubs) |
| `src/styles/print.css` | Print geometry rules — @page/bleed/safe zones (values come from `book.config` via injected CSS variables) |
| `src/styles/design.css` | Palette + typography + layout components (customize per book) |
| `src/master-header.html` / `src/master-footer.html` | HTML head/body wrappers |
| `printer-specs/` | Drop your printer's ICC profile here (gitignored) |
| `docs/DESIGN-LANGUAGE.md` | Visual identity + copy-paste recipes (photo cards, color, type, layout) |
| `docs/ACROBAT-CHECKLIST.md` | Acrobat preflight → press-ready PDF/X-4 |
| `docs/adr/` | Architecture decision records |
| `docs/recipes/` | Optional add-ons — e.g. two-person collaboration (one person uses git only through Claude) |
| `.github/workflows/build.yml` | CI: renders the book on every push/PR and runs the bleed-parity + safe-margin guards |
| `LICENSE` | MIT — covers the template; the book you make with it is entirely yours |
