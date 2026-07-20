# Contributing

Thanks for helping improve the Print Book Template! This project is the **engine
and scaffolding** for making print-ready books — contributions that make it more
robust, more flexible, or easier to start with are very welcome.

> Making a *book* with the template? You don't need any of this — see the README.
> This guide is for changing the template itself.

## Setup

```
python3 -m venv .venv
. .venv/bin/activate                 # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt  # build deps + pytest
./book doctor                        # confirm the toolchain
```

You'll also need WeasyPrint's system libraries (see the README "Install the
toolchain" table), or just use the `Dockerfile`.

## Before you open a PR

```
./book test                 # geometry + helper unit tests
./book build --no-trim      # renders the sample; runs the bleed-parity + safe-margin guards
```

Both must pass — CI runs exactly these on every PR. If you touched cover/spine or
page geometry, also run `./book cover --pages 120`.

## What we look for

- **Never weaken the print guards.** The bleed-parity check and the safe-margin
  check exist because these mistakes ruin real print runs. Changes to `print.css`,
  `_build.py` geometry, or the guards need a test and a note on why they're safe.
- **`book.config` is the single source of truth for geometry.** Don't hardcode
  trim/bleed/safe values in scripts or CSS — read them from the injected variables.
- **Add a test** for new geometry, presets, or helpers (`tests/`), and prefer
  extending the existing patterns (a new generator = one `gen_*` function; a new
  page size = one `PAGE_SIZE_PRESETS` entry + a preset assertion).
- **Match the surrounding style** — comment density, naming, and the "explain the
  print reasoning" tone of the existing code and docs.
- **Verify printer specs.** New presets must cite a real, current spec; keep the
  "verify against your printer's spec sheet" caveat.

## Scope

Good fits: new page-size presets, printer profiles, generators, robustness/tests,
docs, cross-platform fixes. Please open an issue first for large architectural
changes (the render/merge pipeline, the bleed model) so we can talk it through.

## Commits & PRs

- Write intent-based commit messages (the *why*, not a file list).
- Keep PRs focused; describe what changed and how you verified it.
- By contributing you agree your work is licensed under the project's
  [MIT License](LICENSE).

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By
participating you're expected to uphold it.
