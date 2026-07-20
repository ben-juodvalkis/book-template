# Changelog

All notable changes to this template are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-07-20

First open-source release: the private, macOS-only, two-person book project
became a flexible template anyone can fork.

### Added

- **License & community** — MIT `LICENSE` (with an explicit note that books made
  with the template are the author's own), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  issue/PR templates, and this changelog.
- **Reproducible, cross-platform toolchain** — pinned `requirements.txt` /
  `requirements-dev.txt`, a `Dockerfile`, and a single `./book` CLI
  (`book`/`book.py`/`book.cmd`) that auto-selects `.venv`, with `./book doctor`.
- **`./book init`** — turn the demo into a fresh book (title, page size, license
  holder, minimal `book.spreads`); supports `--dry-run`.
- **Print-format breadth** — perfect-bound trade-size presets (`trade-6x9`,
  `trade-5x8`, `trade-5.5x8.5`, `trade-8.5x11`, `square-8.5x8.5`) and
  service-named aliases (`kdp-*`, `ingramspark-*`, `lulu-*`); a `binding_type`
  (saddle-stitch / perfect-bound) that drives the page-count check and a
  binding-aware `min_pages`.
- **Cover generator** — `./book cover --pages N` renders a perfect-bound
  wraparound cover; spine width = page count ÷ paper PPI (named stocks or `--ppi`).
- **Content generation** — `./book generate gallery <dir>` builds photo-grid
  spread pages from a folder of images (new `.photo-grid` component).
- **Self-hosted fonts** — `./book fonts` pins fonts from `fonts/fonts.txt` into
  `fonts/fonts.css` for reproducible/offline/CI renders (see `docs/FONTS.md`).
- **Live preview** — `./book preview-web <section> --watch` serves a section in
  the browser for fast layout iteration.
- **Tests & CI** — a `pytest` suite over the geometry/spine math and build helpers
  (`./book test`), and a GitHub Actions workflow that renders the sample book and
  cover and runs the bleed-parity + safe-margin guards on every push/PR.

### Changed

- The two-person collaboration workflow (auto-pull hook, git safety block,
  plain-English commit protocol) moved out of the default and into optional,
  de-personalized recipes under `docs/recipes/`. The shipped `.claude/settings.json`
  is now neutral.
- The safe-margin guard reads its thresholds from `book.config` geometry, so it's
  correct for every page-size preset instead of hardcoded to Blurb's 0.5"/0.25".
- The renderer runs via `python -m weasyprint`, so builds no longer require an
  activated venv or a `weasyprint` console script on `PATH`.
- The sample book is padded to an even page count so it passes its own
  saddle-stitch check on first build.

[0.1.0]: https://github.com/ben-juodvalkis/book-template/releases/tag/v0.1.0
