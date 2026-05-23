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

## Orientation — settled: page 1 is a RIGHT-hand page

The bleed side flip-flopped repeatedly in the sibling project this template was
extracted from, because it was *reasoned about* instead of *verified against a
physical proof*. The settled, correct answer:

**Page 1 is a RIGHT-hand page.** The first interior page of any bound book is a
right-hand recto (it sits opposite the inside front cover). This was confirmed by
uploading a built PDF to Blurb and observing its previewer place page 1 on the
right — ground truth, not inference. Therefore:

**CANONICAL ORIENTATION (do not paraphrase):**
Page 1 is a RIGHT-hand page. **Odd pages = RIGHT-hand (binding on LEFT, bleed on
RIGHT/outside). Even pages = LEFT-hand (binding on RIGHT, bleed on LEFT/outside).**
WeasyPrint assigns the first physical page of every render to the CSS `:right`
selector, so `@page :right` styles an ODD / RIGHT-hand page and `@page :left` styles
an EVEN / LEFT-hand page — here the selector name matches the physical hand. Bleed
always goes on the OUTSIDE edge.

This is the *standard* book convention. An earlier note here claimed the opposite
("odd = LEFT-hand, bleed on binding") — that was wrong and has been removed. If you
ever doubt the orientation, do not re-derive it: upload to the printer and look at
which side page 1 lands on.

**How it's enforced:** `print.css` sets `:right`→bleed RIGHT, `:left`→bleed LEFT;
`_build.py`'s even-start swap mirrors that for sections beginning on a left-hand
page; and `assert_bleed_parity()` in `master-build.py` fails the build unless page 1
bleeds RIGHT and page 2 bleeds LEFT. The `.safe-left`/`.safe-right` helpers are keyed
to physical hand (left-hand = even, right-hand = odd). No spread content edits are
needed when the orientation is correct — only the bleed metadata is parity-dependent.
