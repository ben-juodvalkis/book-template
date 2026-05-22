# ADR 0001 — Per-section render + native asymmetric bleed

**Status:** Accepted (v9 pipeline, 2026-05-16)

**Supersedes:** the original v9 single-pass build (`master-v9.html` stitching + symmetric bleed + pikepdf binding-edge crop)

## Context

The v9 build that we inherited from v8 worked like this:

1. Concatenate all 21 spread fragments into one giant `master-v9.html`. Each fragment is its own little HTML document with its own `<style>` block and `@page` rules.
2. To avoid `@page p1`, `@page p2` collisions across fragments, the build script regex-renamed them to globally unique `@page g1`, `@page g2`, …, also rewriting the matching `page: pN` inline styles.
3. To make sure every `.page` div extended into the bleed area, regex-inject `margin: -0.125in; width: 8.25in; height: 10.25in` into every `<div class="page …">` tag.
4. To make sure every `@page` rule had the right page geometry, regex-inject `size: 8.0in 10.0in; bleed: 0.125in;` into each one.
5. Run WeasyPrint once on the stitched file. This produced 8.25 × 10.25" pages with **symmetric** 0.125" bleed on all four sides.
6. Open the PDF with pikepdf and crop 0.125" off the binding edge of every page (left for recto, right for verso) to produce the Blurb-spec 8.125 × 10.25" final output.

The three build scripts (`master-build-v9.py`, `master-build-section-v9.py`, `master-build-page-v9.py`) each carried near-duplicate copies of the regex injection machinery, totaling roughly 300 lines of fragile string manipulation. The pikepdf crop existed because WeasyPrint's `bleed: 0.125in` shorthand was symmetric, but Blurb's binding spec required no bleed on the binding edge.

Two things drove this ADR:

- The post-export crop felt like a symptom — we were fighting WeasyPrint instead of telling it what we actually wanted.
- The regex injection coupled the orchestrator to the internal shape of every fragment. Adding or removing a spread required reasoning about how the renumbering would behave; a malformed fragment could silently corrupt the stitched master.

## Decision

Two changes, made together:

### 1. Native asymmetric bleed in CSS

`src-v2/styles-v9/print.css` now uses CSS Paged Media's per-side bleed properties on `:left`/`:right` page selectors:

```css
@page :right {
  size: 8.0in 10.0in !important;
  bleed-top:    0.125in !important;
  bleed-right:  0.125in !important;  /* outside edge */
  bleed-bottom: 0.125in !important;
  bleed-left:   0       !important;  /* binding edge */
}
@page :left { /* mirror */ }
```

WeasyPrint produces 8.125 × 10.25" pages directly. The pikepdf crop step is deleted entirely.

`!important` is intentional: some spreads declare their own `@page p1 { size: ...; bleed: ...; }` rules, and named `@page` selectors have higher specificity than parity selectors. Without `!important`, a spread's `bleed: 0.125in` shorthand would clobber the asymmetric per-side longhand and silently produce 8.25"-wide pages. `!important` locks the Blurb-spec geometry while still letting spreads freely override colors and other per-page properties.

### 2. Per-section render + pikepdf merge

The build pipeline is now:

```
for each spread:
    wrap fragment with shared header/footer + per-section style block
    render to its own PDF via WeasyPrint
merge all PDFs with pikepdf
```

The "per-section style block" injects two things:

- `counter-reset: page-num <N-1>` — so each section's page numbers continue from the right global position across the render boundary.
- When a section starts on a verso (global even page), a swap of `:left`/`:right` bleed definitions — so WeasyPrint's physical-page parity alternation lands on the correct side.

No more `@page` renumbering, no more regex-injected styles, no more outer-tag stripping. Each spread is a self-contained fragment; collisions can't happen because each render is isolated.

Shared logic lives in `_build_v9.py`. The three entry-point scripts (`master-build-v9.py`, `master-build-section-v9.py`, `master-build-page-v9.py`) became thin wrappers over the common module.

## Consequences

**Wins:**

- Final PDF is Blurb-spec (8.125 × 10.25") natively. Geometry verified across all 82 pages of the current book.
- ~300 lines of regex-driven HTML rewriting deleted across the three scripts.
- Single-section and single-page builds now use identical machinery to the master build — what you preview is what you ship.
- Per-section PDFs are kept in `exports-v2/master-v9/sections/`, so a broken spread doesn't lose the work of the other 20.
- Incremental rebuilds are now natural: only re-render sections whose source changed.
- Adding or removing a spread is a one-line change to `SPREADS` in `master-build-v9.py`; no orchestrator changes.

**Costs / things to watch:**

- Page-number continuity across sections depends on the build script computing offsets correctly. Verified by inspecting that the merged PDF has the expected total page count (82) and correct per-section starting parity.
- The `:left`/`:right` parity swap requires the build script to know each section's starting global page number. This is straightforward (running sum over the SPREADS list) but means sections can't be rendered in arbitrary order if you care about parity.
- `!important` in `print.css` is technically a smell, but it's the cleanest defense against spreads accidentally re-declaring `bleed:` and breaking Blurb-spec output. Documented inline in `print.css`.
- Requires WeasyPrint version with per-side bleed + `:left`/`:right` selector support. Verified on WeasyPrint 68.1.

**Verification artifacts:**

- See `docs/bleed-experiments.md` for the WeasyPrint feature tests run during this refactor (per-side bleed, named-page cascade, `!important` override, pikepdf merge, counter-reset offset, parity-swap behavior).

## Post-merge verification (2026-05-16)

A full comparison was run between the PR2 output (this pipeline) and the v11 output (old pipeline), both built from the same spread source files. Methodology and findings:

**Method:**
1. Built PR2 PDF from `claude/simplify-pdf-workflow-2qgh0` using `_build_v9.py` → `exports-v2/master-v9/master-v9.pdf`
2. Built v11 PDF from `v11` branch using the old `master-build-v9.py` → same output path
3. Saved both as `.temp/master-v9-pr2.pdf` and `.temp/master-v9-v11.pdf`
4. Compared page dimensions, BleedBox values, and pixel-rendered content (pdftoppm at 150 DPI)

**Page count & dimensions:**
- Both: 82 pages, all 8.125 × 10.25" (585 × 738 pts). Exact match across all 82 pages.

**BleedBox geometry:**

| Pipeline | Recto BleedBox (x) | Verso BleedBox (x) | Correct? |
|---|---|---|---|
| v11 (old) | `[-9, 585]` — symmetric, includes binding edge | `[-9, 585]` — same | ✗ |
| PR2 (this) | `[0, 585]` — no left/binding bleed | `[-9, 576]` — no right/binding bleed | ✓ |

The old pipeline cropped the MediaBox correctly but left a symmetric BleedBox in the PDF — the binding-edge bleed was declared in the metadata even though it wasn't in the page content. PR2 is the first build to produce a structurally correct BleedBox on all 82 pages.

**Visual content:**
- 57 / 82 pages are pixel-perfect identical.
- 25 / 82 pages show subpixel text rendering differences only — same layout, same images, same colors. This is a normal WeasyPrint artifact of rendering sections in separate passes vs. one giant document; the PDF glyph outlines are identical and the variation is invisible at print resolution.
- No layout differences, no image differences, no color differences on any page.

**Conclusion:** PR2 output is correct and structurally cleaner than the v11 output. The BleedBox fix is a genuine improvement. Safe to merge.

## Alternatives considered

- **Keep the crop, just per-section render.** Would have removed the regex machinery but kept the symptom. Rejected — once we'd verified per-side bleed worked, there was no reason to keep the pikepdf surgery.
- **Edit every spread to remove redundant `size:`/`bleed:` from its `@page` rules.** Equivalent in correctness but invasive (13+ edits across 21 files) and brittle (a future spread author re-introducing the declaration would silently break Blurb-spec). `!important` in shared CSS achieves the same outcome with one decision in one place.
- **Move all `.page` bleed extension and background-image handling into `@page` rules.** WeasyPrint propagates `@page { background-color }` and `@page { background-image }` to the bleed area natively, which means the `margin: -0.125in` trick is unnecessary for many spreads. This is a real opportunity for a follow-up cleanup but was deferred because it requires touching each spread individually and visually verifying the result.

## Correction — bleed side was backwards (2026-05-19, fixed in v25)

The asymmetric bleed described above was implemented on the **wrong side** in v9
through v24. The CSS mapped `@page :right` → "recto (odd)" → bleed on the right,
following the *standard book* convention (odd = recto = right-hand page).

**This project's convention is the opposite:** page 1 is a LEFT-hand page, so
**odd pages = LEFT-hand (binding RIGHT, bleed LEFT)** and **even pages = RIGHT-hand
(binding LEFT, bleed RIGHT)**. Confirmed with the developer 2026-05-19. Every build
v9–v24 therefore put the asymmetric bleed on the binding side instead of the outside
on every page.

It went undetected because the "Post-merge verification" above only checked that the
BleedBox was *structurally asymmetric* (no binding-edge bleed) — it never checked
*which physical side* odd pages land on. The bug also recurred repeatedly in review
because the codebase mixed two vocabularies: CSS `:right`/"recto" vs. the project's
"odd = LEFT-hand". The same words meant different things in different files.

**CANONICAL ORIENTATION (do not paraphrase):**
Page 1 is a LEFT-hand page. Odd pages = LEFT-hand (binding on RIGHT, bleed on LEFT).
Even pages = RIGHT-hand (binding on LEFT, bleed on RIGHT). WeasyPrint assigns the
first physical page of every render to the CSS `:right` selector, so in this project
`@page :right` styles an ODD / LEFT-hand page and `@page :left` styles an EVEN /
RIGHT-hand page — the selector NAME is the OPPOSITE of the physical hand. Never reason
from the selector name; reason from odd/even and physical hand.

**Fix (v25):** swapped the `bleed-left`/`bleed-right` values between `@page :right`
and `@page :left` in `src-v2/styles-v25/print.css` and the mirror swap in
`_build_v25.py`. Renamed the unused `.safe-recto`/`.safe-verso` helper classes to
`.safe-left`/`.safe-right` (keyed to physical hand) to kill the recto/verso ambiguity.
Added a build-time guard `assert_bleed_parity()` in `master-build-v25.py` that opens
the merged PDF and fails the build if page 1 isn't bleeding LEFT. v24 and earlier are
left frozen as-is. No spread content edits were needed — content margins were already
authored to the correct convention; only the bleed metadata was wrong.
