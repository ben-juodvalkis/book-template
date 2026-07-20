# Print Book Template

[![build](https://github.com/ben-juodvalkis/book-template/actions/workflows/build.yml/badge.svg)](https://github.com/ben-juodvalkis/book-template/actions/workflows/build.yml)

A starter for print-ready books authored in **HTML/CSS**, rendered with
**WeasyPrint**, merged with **pikepdf**, and printed via a saddle-stitched
print-on-demand service (Blurb by default). Designed for collage-style,
full-bleed photo books — but the pipeline works for any HTML-laid-out book.

> Use this as a GitHub template ("**Use this template**" → create a new repo), or
> `git clone` it and start a fresh history. It's MIT-licensed; the book you make
> with it is entirely yours (see [License](#license)).

## What you get

- **A per-section render pipeline** that produces a Blurb-spec PDF (8.125×10.25"
  with correct asymmetric bleed) directly — no post-export cropping.
- **A bleed-parity guard** that fails the build if the odd/even bleed side is
  ever wrong (an easy mistake that ruins a print run).
- **A safe-margin check** so ink never lands too close to the trim or binding.
- **One `./book` CLI** for every step, with a `./book doctor` toolchain check.
- **A reproducible, cross-platform toolchain** — a virtualenv + pinned deps, or a
  bundled `Dockerfile` — plus **CI** that renders the book and runs the guards on
  every push.
- **Iteration tools**: build a single section or a single page in seconds.
- **A shareable-draft builder** that rasterizes to a small PDF you can email
  (the only reliable way to shrink these full-bleed books — see CLAUDE.md).
- **Stub spreads** and an **Acrobat → press-ready** checklist to copy from.

## Quick start

### 1. Install the toolchain

WeasyPrint needs a few **system libraries** (Pango et al.) that pip can't install.
Install them for your OS, then set up a Python virtualenv:

| OS | System libraries |
|---|---|
| macOS (Homebrew) | `brew install pango` (or the all-in-one `brew install weasyprint`) |
| Debian / Ubuntu | `sudo apt install libpango-1.0-0 libpangoft2-1.0-0` |
| Fedora | `sudo dnf install pango` |
| Windows | Native install is fussy — use the **Dockerfile** below or WSL |

```
python3 -m venv .venv
. .venv/bin/activate                 # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Optional command-line tools: **`pdftotext`** (poppler) enables the safe-margin
guard, and **`mutool`** (mupdf-tools) is needed only for shareable drafts —
`brew install poppler mupdf-tools` / `apt install poppler-utils mupdf-tools`.

**Prefer containers?** `docker build -t book-template .` then
`docker run --rm -v "$PWD:/book" book-template ./book build` — everything
(including the system libraries and optional tools) is baked in.

### 2. Check it

```
./book doctor
```

This reports which interpreter will run the build and whether every required
library and optional tool is present.

### 3. Make it your book

- `src/master-header.html` — set the `<title>` and fonts.
- `src/styles/design.css` — set the color palette and type.
- `src/spreads/` — replace the stubs (copy them as starting points).
- `book.spreads` — list your sections, in page order.
- `book.config` — set the page size / bleed / safe margins (see the presets).
- `printer-specs/` — drop in your printer's ICC profile (gitignored).

### 4. Build

```
./book build
```

Output: `builds/<branch>-<commit>/master-<branch>-<commit>.pdf`. The build runs
the bleed-parity and safe-margin guards automatically.

> On Windows without a POSIX shell, use `book.cmd build` or `python book.py build`.
> Already have a Homebrew WeasyPrint? Point the CLI at it:
> `BOOK_PYTHON="$(ls -d /opt/homebrew/Cellar/weasyprint/*/libexec/bin/python3.*)" ./book build`.

### 5. Preview & ship

- `./book trimmed` → 8×10 trim preview + a small shareable draft (review only).
- Follow `docs/ACROBAT-CHECKLIST.md` to convert to CMYK / PDF/X-4.
- Order one physical proof before a full run.

## Starting a real book

After clicking "Use this template" (or cloning), make it yours:

1. Do the five quick-start steps above.
2. Replace the stub spreads and the sample `book.spreads` with your sections.
3. Update this `README.md` and the `LICENSE` copyright line for your project.
4. Commit — CI will render your book and run the guards on every push.

## Layout

```
book                # the CLI: ./book build | section | page | trimmed | draft | doctor
book.config         # page size / bleed / safe margins (single source of truth for geometry)
book.spreads        # ordered section list — THE file you edit to wire up the book
requirements.txt    # pinned Python deps for a reproducible virtualenv
Dockerfile          # known-good, cross-platform build environment
scripts/            # build pipeline (the CLI dispatches to these)
src/spreads/        # spread HTML (start from the stubs)
src/styles/         # print.css (geometry, don't touch) + design.css (your palette/type)
src/master-*.html   # head/body wrappers
assets/             # photos (gitignored except the placeholder)
printer-specs/      # your printer's ICC profile (gitignored)
docs/               # design language, Acrobat checklist, ADRs, and optional recipes
.github/workflows/  # CI that renders the book and runs the print-safety guards
```

See **CLAUDE.md** for the full pipeline reference, the canonical page-orientation
rules, and the non-negotiable print rules. See **docs/DESIGN-LANGUAGE.md** for the
visual identity and copy-paste recipes (photo cards with jagged edges and
rotation, color blocks, display type, collage layouts). See **docs/recipes/** for
optional add-ons (e.g. a two-person collaboration workflow where one person uses
git only through Claude Code).

## License

MIT — see [`LICENSE`](LICENSE). The license covers the **template** (the pipeline,
styles, and docs). It lays no claim to the **book** you make with it: your words,
photographs, layouts, and finished PDF are entirely yours, with no attribution
required.

## Contributing

Issues and pull requests are welcome. CI renders the sample book and runs the
bleed-parity and safe-margin guards on every PR, so you'll know immediately if a
change breaks the print geometry.
