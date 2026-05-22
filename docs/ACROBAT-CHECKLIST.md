# Acrobat Pro Checklist — Press-Ready PDF

Take the master PDF from the build pipeline (`builds/<branch>-<commit>/master-<branch>-<commit>.pdf`)
to a press-ready, CMYK, PDF/X-4 file. WeasyPrint output is RGB; this turns it into
what the printer wants.

Run this every time you produce a press-ready PDF. Steps are in order — **Convert
Colors must run before Output Preview is meaningful.**

Replace `<your-printer>.icc` below with the ICC profile in `printer-specs/`.

### Page dimensions (example: 8×10 trim)

| Box | Size |
|---|---|
| Trim box | **8.0 × 10.0"** |
| Bleed box (delivered PDF page) | **8.125 × 10.25"** |

Bleed is 0.125" on the outside edges only (asymmetric — 0 at the binding).
Adjust if your trim differs.

---

## Step 1 — Open the raw PDF

Open the master PDF from the build (the WeasyPrint output). It's RGB at this
point. Don't skip to preflight.

## Step 2 — Convert Colors

**Tools → Print Production → Convert Colors**

| Setting | Value |
|---|---|
| Object Type | Any Object |
| Color Type | Any Colorspace |
| Convert Command | Convert to Profile |
| Conversion Profile | `<your-printer>.icc` |
| Rendering Intent | **Perceptual** ← default is usually wrong, change it |
| Convert Options | **Preserve Black** ← must be checked |
| Convert Pages | All |

- [ ] Rendering Intent = Perceptual (not "Use Document Intent")
- [ ] Preserve Black checked
- [ ] Conversion Profile is your printer's ICC (not a generic FOGRA39/SWOP)
- [ ] OK and save

## Step 3 — Output Preview (read-only inspection)

**Tools → Print Production → Output Preview** — does not modify the file. Run it
at least once on any new build.

Setup:
- [ ] Simulation Profile: `<your-printer>.icc`
- [ ] Simulate Overprinting: checked
- [ ] Show art, trim & bleed boxes: checked

Boxes:
- [ ] Bleed box at the bleed size (outer edge)
- [ ] Trim box at the trim size (inner edge)
- [ ] Colored border visible in the bleed zone on every page — correct and intentional

TAC (Total Area Coverage) at 300%:
- [ ] Body text reads **C0 M0 Y0 K100** when hovered — if not, black text has a color problem
- [ ] Black graphic blocks read **C0 M0 Y0 K100**
- [ ] Flat (non-photo) color backgrounds show no TAC highlights — if highlighted, investigate
- [ ] Photo highlights are expected — ignore them
- [ ] Note how much your saturated colors shifted; flag any unacceptable ones for a CSS revision

TAC rules: pre-conversion readings are simulations (run Convert Colors first);
photo shadows over 300% are usually fine on digital presses; only flat color and
text matter.

## Step 4 — Preflight

**Tools → Print Production → Preflight**

- [ ] **Profiles** tab (not Fixups)
- [ ] Expand **PDF/X**, select **Convert to PDF/X-4 (Coated GRACoL 2006)** (or your printer's spec)
- [ ] **Analyze and fix** (not Analyze alone)
- [ ] Results show **No problems found**
- [ ] Save as a `-fixed` / `-READY` variant — do NOT overwrite the raw build

Expected fixes (normal for WeasyPrint output): convert to PDF/X-4, set Trapped key,
set transparency blend color space, make XMP compliant, recompress objects.

Actual errors (go back and fix in CSS / rebuild): RGB objects remaining, missing
font embeddings, images below 300 DPI at print size.

## Step 5 — Final save & upload

- [ ] Saved as the press-ready PDF with a clearly distinct filename
- [ ] Don't re-open and re-save without re-running the pipeline (round-trips degrade the file)
- [ ] Upload to the printer; review their online preview (page order, no blanks, cover correct)
- [ ] Order ONE physical proof before a full print run

---

## Color risk reference (fill in for YOUR palette)

| Color | Hex | Risk | Watch for |
|---|---|---|---|
| Black | `#000000` | None | Must read K100 only |
| ... | ... | ... | ... |

Never use near-black RGB values like `#232023` — they exceed 300% TAC after CMYK
conversion. Use `#000000` for all black, text and graphics alike. Saturated RGB
greens, magentas, and deep purples are the usual gamut casualties — soft-proof them.
