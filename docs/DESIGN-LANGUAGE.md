# Design Language

The visual identity for these books: **maximalist collage** — full-bleed
saturated color, oversized display type, and rotated photo cards with hand-cut
edges arranged in overlapping arrangements. Photos sit inside color fields, not
in white space. The look is unapologetic; don't soften or neutralize it.

This doc is a working **component library** with copy-paste recipes. Every
snippet is print-safe as written (it respects the bleed/safe-margin geometry in
[print.css](../src/styles/print.css)); adjust positions, colors, and rotations
to taste. Reusable classes referenced below live in
[design.css](../src/styles/design.css).

> **Read first:** [CLAUDE.md](../CLAUDE.md) for the non-negotiable print rules
> (page geometry, bleed orientation, safe zones, color/CMYK). Everything here
> assumes those constraints. In particular: positions are measured from the
> `.page` div edge, which overhangs trim by 0.125" on all four sides, so
> "safe" content sits **≥ 0.625in** from the div edge (binding and outside),
> **≥ 0.375in** top/bottom. Rotated elements need ~0.7in.

---

## 1. Photo cards — the signature element

A photo card is a **two-layer structure**:

- **Outer div** — a colored rectangle (the visible "mount"/border), positioned
  absolutely and usually rotated a few degrees. This is the card.
- **Inner div** — inset from the outer by the border thickness, clips the photo.
- **`<img>`** — fills the inner div with `object-fit: cover`.

The colored gap between the outer and inner edges *is* the border. Optionally a
`clip-path: polygon()` on either layer turns the straight edge into a hand-cut
one. The base classes are in design.css:

```css
.photo-card        { position:absolute; background:#000; transform-origin:center center; }
.photo-card-inner  { position:absolute; top:.18in; left:.18in; right:.18in; bottom:.18in; overflow:hidden; }
.photo-card-inner img { width:100%; height:100%; object-fit:cover; object-position:center; display:block; }
```

> **Rotated cards & safe margins:** a rotation swings the corners outward past
> the nominal inset. Keep rotated cards **~0.7in** from the `.page` div edge.
> The build's safe-margin check measures rendered ink and will flag a corner
> that crosses the line — trust it.

> **Image resolution:** size the photo for ≥300 DPI at the card's printed size.
> A 3.5in-wide card needs ≥1050px; a 7.5in card needs ≥2250px. Note the source
> px in a comment next to the card (the Bianca spreads do this religiously).

### Recipe 1a — Jagged colored-border card (the classic)

The default look: a saturated mount with a hand-cut edge, rotated a few degrees.
Double clip-path (different polygons on outer vs inner) gives the richest "torn
frame" feel.

```html
<div class="photo-card jagged" style="
  top:3.45in; right:0.65in; width:2.2in; height:3.35in;
  background:var(--accent-1); transform:rotate(-4deg); z-index:3;">
  <div class="photo-card-inner">
    <!-- 666×1012px source → 2.2in wide ≈ 303 DPI -->
    <img src="assets/photo.jpg" style="object-position:center top;" alt="">
  </div>
</div>
```

- **Rotation:** ±1° to ±5° is the calm range; ±6° to ±9° for high-energy pages.
- **Border thickness:** the default 0.18in mount. Bump `bottom` to ~0.6in if you
  want room for a caption strip under the photo (see Recipe 1e).
- **Edge variety:** vary the inner polygon per card so no two look identical.
  Proven inner polygons (each a subtle ±10% corner jitter):
  ```
  polygon(0% 8%, 90% 0%, 100% 88%, 6% 100%)
  polygon(10% 0%, 100% 10%, 88% 100%, 0% 92%)
  polygon(8% 0%, 100% 6%, 94% 100%, 0% 88%)
  polygon(0% 12%, 88% 0%, 100% 88%, 6% 100%)
  ```
  Keep the **outer** polygon subtle — `polygon(2% 0%, 100% 1%, 98% 100%, 0% 98%)`
  — so the card still reads as a rectangle.

### Recipe 1b — Large hero card (bottom-anchored, gentle tilt)

A single dominant card, e.g. a portrait filling most of a page. Small rotation
so it stays grand rather than chaotic.

```html
<div class="photo-card" style="
  top:3.075in; left:0.75in; right:0.75in; height:6.8in;
  background:var(--accent-1);
  clip-path:polygon(0% 1%, 98% 0%, 100% 98%, 2% 100%);
  transform:rotate(-2deg); z-index:4;">
  <div class="photo-card-inner" style="top:0.22in; left:0.22in; right:0.22in; bottom:0.22in;">
    <img src="assets/hero.jpg" style="object-position:center top;" alt="">
  </div>
</div>
```

A thicker 0.22in mount suits a large card. Anchor with `right` + `height` (not
`width`) when you want it to span a fixed left/right inset.

### Recipe 1c — Film-still border (tight black mount, no jaggies)

For performance documentation / contact-sheet energy: precise rectangles, thin
black border, packed into a grid. Use the `.film` modifier (0.07in border).

```html
<div class="photo-card film" style="
  top:0.4in; left:0.7in; width:3.5in; height:3.5in;
  transform:rotate(-1deg); z-index:4;">
  <div class="photo-card-inner"><img src="assets/still-01.jpg" alt=""></div>
</div>
```

Lay several in rows with ±1°–2° rotations and overlapping z-indexes for a
hand-arranged contact sheet. To preserve a square/standard photo's full frame
without cropping, set the image to `object-fit:contain`:

```html
<div class="photo-card-inner"><img src="assets/square.jpg" style="object-fit:contain;" alt=""></div>
```

### Recipe 1d — Gradient-fade collage card (borderless, for dark pages)

Large photos that bleed into a dark page background via a gradient fade instead
of a border. Best on black/near-black pages; rotate hard (±5°–9°) and overlap.

```html
<div style="position:absolute; top:0.4in; right:-0.4in; width:7.5in; height:5.0in;
            transform:rotate(7deg); z-index:3; overflow:hidden;">
  <img src="assets/big.jpg" style="width:100%; height:100%; object-fit:cover; display:block;" alt="">
  <!-- fade the bottom into the page color -->
  <div style="position:absolute; bottom:0; left:0; right:0; height:40%;
              background:linear-gradient(to bottom, transparent, #000000);"></div>
</div>
```

Negative `left`/`right` (e.g. `right:-0.4in`) intentionally runs the card off the
page into the bleed — fine for a borderless photo, since there's no mount edge to
protect. Stack 3–5 of these at different sizes/angles for a collage.

### Recipe 1e — Caption strip on a card

Anchor an italic caption inside the mount, below the photo. Give the inner div a
deeper `bottom` so the photo doesn't run under the caption.

```html
<div class="photo-card jagged" style="top:1in; right:0.65in; width:2.2in; height:3.35in;
                                      background:var(--accent-1); transform:rotate(-4deg);">
  <div class="photo-card-inner" style="bottom:0.6in;">
    <img src="assets/baby.jpg" alt="">
  </div>
  <div class="caption">Michelin Tire Baby</div>
</div>
```

---

## 2. Color system

The palette lives in [design.css](../src/styles/design.css) as CSS variables.
Replace the example values with your book's colors and **soft-proof every one**
in Acrobat before committing (see [ACROBAT-CHECKLIST.md](ACROBAT-CHECKLIST.md)).
Saturated greens, magentas, and deep purples are the usual CMYK casualties.

```css
:root {
  --accent-1: #E8338A;
  --accent-2: #4AABDF;
  --accent-3: #D4882A;
  --paper:    #FFFFFF;
  --ink:      #000000;   /* always pure K — text and large black areas */
}
```

### Per-section background color

Each section owns a background color, set on both the page and the `@page` rule
(the `@page` color fills the bleed). Rotate the dominant color section to section
so flipping through feels like moving through chapters.

```html
<style>
  @page p1 { background-color: var(--accent-2); }
  @page p2 { background-color: var(--accent-3); }
</style>
<div class="page" style="page:p1; background-color:var(--accent-2);"> ... </div>
```

A photo card's mount color need not match its page — contrast (pink card on a
green page) is part of the language.

### Rotated color blocks (banners & slabs)

Flat colored rectangles, slightly rotated, used as title banners or as collage
slabs behind/around content. The signature "punctuation" mark.

```html
<!-- Title banner: colored bar with display type sitting just inside it -->
<div style="position:absolute; top:0.38in; left:0.75in; width:3.8in; height:0.66in;
            background-color:var(--accent-1); transform:rotate(-3deg); z-index:2;"></div>
<div style="position:absolute; top:0.43in; left:0.855in; z-index:3;">
  <span style="font-family:'Display', serif; font-size:44pt; color:#000; line-height:1;">Title</span>
</div>
```

Use the `.color-block` class for free-floating slabs:

```html
<div class="color-block bg-1" style="top:2in; left:1in; width:4in; height:3in;
                                     transform:rotate(-6deg);"></div>
```

Banners may intentionally overhang the outside/binding into the bleed (negative
`left`) for an off-the-edge feel — fine for solid color, never for text.

---

## 3. Typography

Two-font system: an expressive **display face** for titles and a clean
**body face** for running copy. Set both in
[master-header.html](../src/master-header.html) (Google Fonts or `@font-face`)
and reference them in design.css. The Bianca book pairs *Barriecito* (display)
with *Work Sans* (body).

| Role | Class / usage | Size | Line-height |
|---|---|---|---|
| Hero title | `.heading-xl` | 72pt | 1 |
| Section header | `.heading-lg` | 36pt | 1.1 |
| Subhead | `.heading-sm` | 18pt | — |
| Project title (display, on photo) | inline | 84–96pt | 0.88 |
| Body | `.body` | 11pt | 1.55 |

Body copy is the **single source of truth** at 11pt/1.55 — don't shrink it to
make text fit; add a page instead. `.body` uses `overflow:visible` on purpose so
overset copy spills *visibly* at proof time rather than being silently clipped.

### Tapering headline

A display block where each line steps down in size — a visual cascade for poetic
or emphatic text. One `<div>` per line, fixed pt sizes and line-heights (don't
rely on auto leading).

```html
<div style="position:absolute; top:0.375in; left:0.875in; right:4.25in; z-index:2;
            font-family:'Display', serif; color:#fff; text-align:left;">
  <div style="font-size:26pt; line-height:25pt; margin-bottom:0.04in;">So my mouth was messy. My mind was all mixed up.</div>
  <div style="font-size:21pt; line-height:28pt;">What does the body do</div>
  <div style="font-size:17pt; line-height:28pt;">when it is taught</div>
  <div style="font-size:13pt; line-height:18pt;">to be silent,</div>
  <div style="font-size:13pt; line-height:18pt;">yet has so much to say?</div>
</div>
```

### Drop cap

```html
<span style="font-family:'Display',serif; font-size:28pt; float:left;
             margin-right:0.05in; margin-top:-0.02in;">T</span>he rest of the paragraph…
```

### Redaction bar

Hide a word under a colored bar (text color = bar color). Newspaper/redacted-doc
effect.

```html
<span style="background-color:var(--accent-1); color:var(--accent-1);
             padding:0 0.02in; box-decoration-break:clone;
             -webkit-box-decoration-break:clone;">redacted</span>
```

### Two-column body

```html
<div class="body" style="column-count:2; column-gap:0.35in;">
  <p>…</p><p>…</p>
</div>
```

---

## 4. Layout patterns

### Full-bleed photo page

Photo as the page `background-image` (reaches the bleed automatically via the
`.page` overhang — no pre-expanded `-bleed.jpg` needed). Always set a matching
`background-color` fallback close to the photo's edge color.

```html
<div class="page" style="page:p1;
  background-color:#1a1a1a;
  background-image:url('assets/hero.jpg');
  background-size:cover; background-position:center bottom;">
  <span class="page-number left on-dark"></span>
</div>
```

### Full-spread (cross-gutter) photo

One photo spanning **both** facing pages. Put the *same* image on the two `.page`
divs and add the `.spread-photo` classes: the image is sized to the whole flat
spread and each page is offset to show its half, so they meet exactly at the fold —
no cutting the image, no hand-tuned offsets, and it re-derives automatically if you
change page size in `book.config`.

First cover-crop the photo to the spread's aspect ratio (the tool reads
`book.config`, so the ratio is right for any page size, and it warns below 300 DPI):

```
python3 scripts/spread-photo.py assets/raw.jpg --focus center   # → assets/raw-spread.jpg
```

Then place it — `.spread-photo-verso` on the LEFT-hand (even) page,
`.spread-photo-recto` on the RIGHT-hand (odd) page facing it:

```html
<div class="page spread-photo spread-photo-verso" style="page:p1;
     background-image:url('assets/raw-spread.jpg'); background-color:#111;">
  <span class="page-number left on-dark"></span>
</div>
<div class="page spread-photo spread-photo-recto" style="page:p2;
     background-image:url('assets/raw-spread.jpg'); background-color:#111;">
  <span class="page-number right on-dark"></span>
</div>
```

The section **must start on an even page** (so the verso is a left-hand page);
`master-build.py` warns if a spread photo lands on the wrong hand. Full stub:
`src/spreads/04-spread-photo.html`.

### Scrim for text over photos

Gradient overlay so type stays legible on a busy/dark photo.

```html
<!-- top-down scrim (title at top) -->
<div style="position:absolute; inset:0;
            background:linear-gradient(to bottom, rgba(0,0,0,0.88) 60%, rgba(0,0,0,0.72) 80%, rgba(0,0,0,0));"></div>

<!-- edge scrims (text against left/right edge over a centered subject) -->
<div style="position:absolute; inset:0;
            background:linear-gradient(to right, rgba(0,0,0,1) 40%, rgba(0,0,0,0));"></div>
```

### Collage grid

Rows of `.photo-card.film` (or jagged) cards with small alternating rotations and
overlapping z-indexes. Use a consistent card size and a fixed horizontal step.

```html
<div class="photo-card film" style="top:0.4in; left:0.70in;  width:3.5in; height:3.5in; transform:rotate(-1deg);  z-index:4;"><div class="photo-card-inner"><img src="assets/01.jpg" alt=""></div></div>
<div class="photo-card film" style="top:0.4in; left:3.725in; width:3.5in; height:3.5in; transform:rotate(1.5deg); z-index:5;"><div class="photo-card-inner"><img src="assets/02.jpg" alt=""></div></div>
<!-- next row: top += card height + small gap -->
```

### Overlapping dynamic collage

Borderless gradient-fade cards (Recipe 1d) at ±5°–9°, varying sizes, overlapping,
some running off-page into the bleed. The high-energy section treatment.

### Page folios

Auto-incrementing via CSS counter (wired in print.css). Place one per page;
match the color to the background.

```html
<span class="page-number left on-dark"></span>     <!-- LEFT/odd page, dark bg  -->
<span class="page-number right on-light"></span>   <!-- RIGHT/even page, light bg -->
<span class="page-number left no-number"></span>   <!-- count the page, hide the number -->
```

### Title bar (skewed black slab)

A slightly skewed black bar grounding a title while adding geometric interest.

```html
<div style="position:absolute; top:1in; left:0.7in; right:0.7in; height:1.4in;
            background:#000; clip-path:polygon(0% 0%, 100% 1%, 99% 100%, 0% 98%);
            transform:rotate(-0.8deg);"></div>
```

---

## 5. Motif quick reference

| Motif | Technique | When to use |
|---|---|---|
| Jagged photo card | `clip-path:polygon()` on colored mount + `rotate()` | Default photo treatment |
| Film-still card | `.photo-card.film`, tight black border, ±1–2° | Documentation grids |
| Gradient-fade card | borderless img + `linear-gradient` fade to page color | Dark-page collage |
| Full-bleed photo | `background-image` on `.page` | Hero / title spreads |
| Full-spread photo | same image both pages + `.spread-photo-verso/-recto` | One photo across the fold |
| Scrim | `linear-gradient` rgba overlay | Text over photos |
| Rotated color block | flat colored div, ±2–3° | Title banners, slabs |
| Tapering headline | per-line decreasing pt | Poetic / emphatic text |
| Redaction bar | text color = background color | Censored words |
| Skewed black title bar | `clip-path` + small `rotate` | Grounding a title |

---

## 6. Print-safety checklist for any new layout

- [ ] Content (esp. text) ≥ 0.625in from the `.page` div edge on binding & outside,
      ≥ 0.375in top/bottom. Rotated cards ~0.7in.
- [ ] All black is `#000000` (pure K). No near-black RGB like `#232023`.
- [ ] Saturated colors soft-proofed in Acrobat with the printer ICC.
- [ ] Full-bleed photos have a matching `background-color` fallback.
- [ ] Images ≥ 300 DPI at printed size.
- [ ] No `vw`/`vh`/viewport units; no hover/animation/transition; no `position:fixed`.
- [ ] `@page` rules set only `background-color` (never `size`/`bleed` — print.css owns those).
- [ ] Ran `master-build.py`; bleed-parity and safe-margin checks pass.
