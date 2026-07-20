# ADR 0002 — Configurable page geometry + cross-gutter photo utility

**Status:** Accepted (2026-07-20)

**Builds on:** ADR 0001 (per-section render + native asymmetric bleed)

## Context

Two needs surfaced together:

1. **Full-spread (cross-gutter) photos.** A single photo spanning both facing pages
   had no first-class support. By hand it meant either cutting the image into two
   exactly-aligned halves, or placing one image on both pages with a hand-tuned
   `background-position` offset (≈ −8in) — plus a parity constraint (the halves must
   be a verso→recto pair) and an aspect-ratio constraint (or the image stretches).
   Error-prone, with nothing to catch a mistake.

2. **Page-size flexibility.** Geometry (trim, bleed, safe margins) was hardcoded in
   `print.css` and echoed in prose across the docs, so targeting a different trim
   size meant editing CSS in several places and re-deriving safe insets by hand.

The two are linked: for the cross-gutter feature to be page-size-agnostic, the photo
math (spread width, per-page offset) must derive from the *same* geometry the pages
render at, or the two silently disagree.

## Decision

### 1. Geometry is a single source of truth in `book.config`, injected as CSS variables

`book.config` gains a `page_size` preset plus optional per-field overrides (trim,
bleed, safe margins, dpi). `scripts/_build.py` (`geometry()`) computes every derived
value once and emits a `:root { --trim-w: …; --bleed: …; --spread-w: …; … }` block
that `build_section_html()` injects into `<head>` of every render. `print.css` and
`design.css` consume the variables via `var()`, with fallbacks equal to the previous
Blurb 8×10 literals so the stylesheets still render standalone.

We inject **CSS custom properties**, not generated literal CSS, because WeasyPrint 69
resolves `var()` inside `@page` rules and across separate stylesheets (verified during
this work). That keeps generation to one `:root` block and leaves the `@page` /
`.page` / `.safe` rules readable in `print.css`.

Default config renders **byte-identical** to the pre-change output (pixel diff 0 on
every page); other presets and overrides render at the correct size.

### 2. Cross-gutter photos are a utility layered on the existing pipeline — not a wide-canvas + slice

A full-spread photo is authored as the SAME image on both `.page` divs with the
`.spread-photo-verso` / `.spread-photo-recto` classes. The image is sized to the whole
flat spread (`--spread-w × --spread-h`) and each page offset by `--spread-recto-x`
(= −trim_width) so the halves meet exactly at the fold. `scripts/spread-photo.py`
prepares the image with a cover crop to the spread's aspect ratio (fills without
stretching), plus `--focus` (which part to keep) and `--zoom` (magnify) options.
`master-build.py` warns if a spread photo lands on the wrong page hand.

Crucially this changes **nothing** in the render/merge pipeline — no wide landscape
canvas, no post-render page slicing, no folio rework. It is CSS classes + an
image-prep tool on top of the per-section render from ADR 0001.

## Consequences

**Wins**
- One photo across the fold is two `.page` divs + one prepared image; the seam is
  exact by construction (verified: 0-px seam on the built book).
- Page size (trim/bleed/safe/gutter) is one edit in `book.config`; pages, bleed, safe
  zones, and the cross-gutter math all re-flow together.
- No regression risk to existing books: default geometry is byte-identical.
- The parity guard turns the one un-encapsulatable constraint (verso→recto placement)
  into a build-time warning.

**Costs / things to watch**
- The placed image must match the spread aspect ratio or `background-size` stretches
  it; `spread-photo.py` is the intended way to guarantee that (a raw url dropped
  straight onto the classes will stretch). Documented in the stub and DESIGN-LANGUAGE.
- Parity is a placement fact (in `book.spreads` order), not something the image tool
  can fix; the guard warns but does not hard-fail.
- Geometry now depends on the build injecting the `:root` block; a spread rendered
  without `build_section_html()` falls back to the 8×10 `var()` defaults.

## Alternatives considered

- **Wide-canvas + slice** — author a 16.25in landscape spread, render it, slice each
  page down the fold in the build. Rejected: it reintroduces the post-render PDF
  surgery ADR 0001 deliberately deleted, and reworks folios and the front/back
  boundary — a large change for one feature the layered utility delivers without
  touching the pipeline.
- **CSS-only cover** — avoid the prep script with `background-size: cover`. Rejected:
  `cover` is computed per element, so each 8.25in page covers independently and the
  halves no longer align; sizing by a single dimension only covers for wide-enough
  images and crops asymmetrically. Robust, centered, no-stretch placement needs the
  image at the spread ratio — i.e. the script.
- **Pre-cut halves** — two files per spread photo. Rejected: two derived files to
  manage and a cut that must be pixel-exact at the fold; one image + CSS offset is
  simpler and the seam is guaranteed.
- **Generated literal `@page` CSS** instead of `var()`. Unnecessary once `var()` in
  `@page` was verified on WeasyPrint 69; custom properties keep generation to one
  block and the CSS readable.

## Verification

- **Default config:** geometry boxes and rendered pixels identical to the pre-change
  build on all pages (pixel diff 0).
- **Agnostic sizing:** blurb-7x7 → 7.125×7.25, blurb-10x8-landscape → 10.125×8.25,
  8×10 + bleed 0.25in → 8.25×10.5, all exact.
- **Seam:** a gradient prepared by `spread-photo.py` and placed on pages 8–9 of the
  built book is continuous across the fold (0-px delta at the fold columns).
- **`--zoom`:** output stays at the spread aspect (seam-safe) while cropping tighter
  and lowering effective DPI (the sub-300-DPI warning fires as expected).
