# Print Book Template

A starter for print-ready books authored in **HTML/CSS**, rendered with
**WeasyPrint**, merged with **pikepdf**, and printed via a saddle-stitched
print-on-demand service (Blurb by default). Designed for collage-style,
full-bleed photo books — but the pipeline works for any HTML-laid-out book.

> Use this as a GitHub template ("Use this template" → create a new repo), or
> `git clone` it and start a fresh history.

## What you get

- **A per-section render pipeline** that produces a Blurb-spec PDF (8.125×10.25"
  with correct asymmetric bleed) directly — no post-export cropping.
- **A bleed-parity guard** that fails the build if the odd/even bleed side is
  ever wrong (an easy mistake that ruins a print run).
- **A safe-margin check** so ink never lands too close to the trim or binding.
- **Iteration tools**: build a single section or a single page in seconds.
- **A shareable-draft builder** that rasterizes to a small PDF you can email
  (the only reliable way to shrink these full-bleed books — see CLAUDE.md).
- **Stub spreads** and an **Acrobat → press-ready** checklist to copy from.

## Quick start

1. **Install the toolchain**
   ```
   brew install weasyprint mupdf-tools
   ```
   WeasyPrint ships its own Python with `weasyprint` + `pikepdf`. Find it:
   ```
   ls -d /opt/homebrew/Cellar/weasyprint/*/libexec/bin/python3.*
   ```
   Use that interpreter to run the scripts (it must import both modules).

2. **Make it your book**
   - `src/master-header.html` — set the `<title>` and fonts.
   - `src/styles/design.css` — set the color palette and type.
   - `src/spreads/` — replace the stubs (copy them as starting points).
   - `book.spreads` — list your sections, in page order.
   - `printer-specs/` — drop in your printer's ICC profile.

3. **Build**
   ```
   <weasyprint-python> scripts/master-build.py
   ```
   Output: `builds/<branch>-<commit>/master-<branch>-<commit>.pdf`.

4. **Preview & ship**
   - `scripts/master-build-trimmed.py` → 8×10 trim preview (review only).
   - Follow `docs/ACROBAT-CHECKLIST.md` to convert to CMYK / PDF/X-4.
   - Order one physical proof before a full run.

## Layout

```
book.spreads        # ordered section list — THE file you edit to wire up the book
scripts/            # build pipeline (run from the repo root)
src/spreads/        # spread HTML (start from the stubs)
src/styles/         # print.css (geometry, don't touch) + design.css (your palette/type)
src/master-*.html   # head/body wrappers
assets/             # photos (gitignored except the placeholder)
printer-specs/      # your printer's ICC profile (gitignored)
docs/               # ADR + Acrobat checklist
```

See **CLAUDE.md** for the full pipeline reference, the canonical page-orientation
rules, and the non-negotiable print rules. See **docs/DESIGN-LANGUAGE.md** for the
visual identity and copy-paste recipes (photo cards with jagged edges and
rotation, color blocks, display type, collage layouts).
