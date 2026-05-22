# CLAUDE.md — Print Book Template

A starter for print-ready books designed in HTML/CSS and printed via a
saddle-stitched POD printer (Blurb by default). Rendered with WeasyPrint and
merged with pikepdf into a Blurb-spec PDF. Read this before touching anything.

> **This is a template.** When starting a real book: set the title and fonts in
> `src/master-header.html`, the palette in `src/styles/design.css`, replace the
> stub spreads in `src/spreads/`, and edit `book.spreads` to list your sections
> in page order. The print geometry in `src/styles/print.css` and the build
> scripts in `scripts/` should not need changing.

---

## The Pipeline

```
src/spreads/*.html  →  python3 scripts/master-build.py  →  builds/<branch>-<commit>/master-<branch>-<commit>.pdf  →  printer
```

The build renders each spread to its own PDF via WeasyPrint, then merges them
with pikepdf. No master-HTML stitching, no `@page` renumbering, no post-export
crop — WeasyPrint produces the bleed page size natively via per-side bleed in
`src/styles/print.css`. See
`docs/adr/0001-per-section-render-and-native-asymmetric-bleed.md`.

**Which sections build, and in what order, is defined entirely by `book.spreads`**
(one spread path per line, in page order; `#` comments and blank lines ignored).
The scripts read it via `_build.load_spreads()` — you never edit a Python list.

**Toolchain** — WeasyPrint (Homebrew formula) ships its own virtualenv that has
both `weasyprint` and `pikepdf`. The build scripts `import weasyprint` directly,
so run them with that interpreter, not a plain `python3`. Find it with:

```
ls -d /opt/homebrew/Cellar/weasyprint/*/libexec/bin/python3.* 
```

Sanity-check a candidate: `<interp> -c "import weasyprint, pikepdf"`.
The draft builder also needs `mutool` (`brew install mupdf-tools`) and Pillow.

### Commands

```
python3 scripts/master-build.py             # render all sections + merge → builds/<slug>/
python3 scripts/master-build.py --no-trim   # master PDF only (skip trimmed + draft)
python3 scripts/master-build.py --html-only # write per-section wrapped HTML, skip render

python3 scripts/master-build-section.py 01-title          # one section → .temp/
python3 scripts/master-build-page.py    01-title --page 2 # one page (or 2-4) → .temp/
python3 scripts/master-build-trimmed.py                   # trim-cropped 8×10 preview + draft
python3 scripts/master-build-draft.py                     # small shareable rasterized draft
```

Output lands in `builds/<branch>-<commit>/` — each branch/commit gets its own
self-labeled folder. `builds/` is gitignored. The trimmed/draft PDFs are for
screen review only — never submit them to the printer.

Shared rendering logic lives in `scripts/_build.py`.

---

## How the Build Works — Page Size & Bleed

> **CANONICAL ORIENTATION (do not paraphrase):**
> Page 1 is a LEFT-hand page. **Odd pages = LEFT-hand (binding on RIGHT, bleed on
> LEFT). Even pages = RIGHT-hand (binding on LEFT, bleed on RIGHT).** WeasyPrint
> assigns the first physical page of every render to the CSS `:right` selector, so
> in this project **`@page :right` styles an ODD / LEFT-hand page** and
> **`@page :left` styles an EVEN / RIGHT-hand page** — the selector NAME is the
> OPPOSITE of the physical hand. Never reason from the selector name; reason from
> odd/even and physical hand.

`print.css` declares asymmetric bleed via per-side properties on `:left`/`:right`
page selectors. `master-build.py` runs `assert_bleed_parity()` after merge and
FAILS the build if page 1 isn't bleeding LEFT — trust that guard.

When a spread starts on an even / RIGHT-hand page, the build injects a CSS swap
of `:left`/`:right` bleed so WeasyPrint's physical-page alternation lands the
bleed on the correct (outside) side.

The `.page` div is sized 8.25×10.25" with `margin: -0.125in` so it extends into
all four bleed regions; WeasyPrint clips it at the asymmetric page edge, so the
binding gets no bleed. This is what lets `background-color`/`background-image` on
`.page` reach the outside bleed.

---

## Non-Negotiable Print Rules

**Page dimensions (example: Blurb 8×10 trim — change in `print.css` if different)**
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
4. `python3 scripts/master-build-section.py NN-name` to preview, then a full build.
5. Keep the total page count EVEN for saddle-stitch (the build warns if it's odd).

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
| `scripts/master-build.py` | Full-book build (per-section render + merge + parity/margin checks) |
| `scripts/master-build-trimmed.py` | Trim-cropped 8×10 preview + shareable draft (review only) |
| `scripts/master-build-draft.py` | Rasterize any build PDF → small shareable draft |
| `scripts/master-build-section.py` | Single-section build for iteration |
| `scripts/master-build-page.py` | Single-page build for iteration |
| `scripts/_build.py` | Shared rendering primitives + `load_spreads()` + `builds/<slug>/` scheme |
| `src/spreads/` | Spread source files (start from the stubs) |
| `src/styles/print.css` | Print geometry — page size, asymmetric bleed, safe zones |
| `src/styles/design.css` | Palette + typography + layout components (customize per book) |
| `src/master-header.html` / `src/master-footer.html` | HTML head/body wrappers |
| `printer-specs/` | Drop your printer's ICC profile here (gitignored) |
| `docs/ACROBAT-CHECKLIST.md` | Acrobat preflight → press-ready PDF/X-4 |
| `docs/adr/` | Architecture decision records |
