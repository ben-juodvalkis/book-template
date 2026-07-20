## What & why

<!-- What does this change, and why? Link any related issue. -->

## How I verified

<!-- Check what you ran. CI runs the same. -->

- [ ] `./book test` passes
- [ ] `./book build --no-trim` passes (bleed-parity + safe-margin guards green)
- [ ] Touched cover/spine or geometry → also ran `./book cover --pages 120`
- [ ] Added/updated a test for new geometry, presets, or helpers

## Print-safety

<!-- Delete if N/A. If this touches print.css, _build.py geometry, or the guards: -->

- [ ] Geometry still comes from `book.config` (no hardcoded trim/bleed/safe values)
- [ ] New page-size presets cite a current printer spec sheet
- [ ] I explained why any change to the guards is safe

## Notes

<!-- Anything reviewers should know: trade-offs, follow-ups, screenshots. -->
