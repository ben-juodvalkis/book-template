---
name: Bug report
about: Something in the template/pipeline doesn't work as expected
title: ""
labels: bug
assignees: ""
---

**What happened**
A clear description of the bug.

**What you expected**
What you expected instead.

**To reproduce**
Steps / the command you ran, e.g. `./book build`:

```
paste the command and any error output here
```

**Book config**
- Page size / preset: <!-- e.g. blurb-8x10, trade-6x9, or custom overrides -->
- Binding: <!-- saddle-stitch / perfect-bound -->

**Environment** (from `./book doctor`)
- OS:
- Python:
- WeasyPrint / pikepdf / Pillow versions:
- Install method: <!-- venv + requirements.txt / Docker / Homebrew WeasyPrint -->

**Print-safety note**
If this is about bleed, trim, or safe margins, please attach the relevant page of
the PDF (or the build's parity/safe-margin output) — it makes geometry bugs much
faster to diagnose.
