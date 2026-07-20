# Showcase

Books made with this template, and how to show off your own.

## Make a shareable preview of your book

The full build PDF is print-resolution and large. For sharing a look (email, a
README, social), make a small preview instead:

- **Small PDF draft** — `./book trimmed` produces a trim-cropped preview and a
  rasterized `*-trimmed-draft.pdf` you can email. (Needs `mutool`; see the README.)
- **Browser view** — `./book preview-web <section>` to screenshot a page from the
  browser. Quick, but a browser is not WeasyPrint — for a true-to-print image,
  screenshot the PDF instead.
- **Page images from the PDF** — with poppler installed:
  ```
  pdftoppm -png -r 150 builds/<slug>/master-<slug>-trimmed.pdf preview
  ```
  gives one PNG per page at 150 DPI.

Keep marketing images to the **trimmed** (no-bleed) preview so what people see is
what gets bound.

## Made with this template

Have you published something with it? Open a PR adding a row — title, a one-line
description, page size/binding, and a link (to the book, a shop page, or a photo).

| Book | By | Format | Link |
|---|---|---|---|
| _Your book here_ | you | e.g. trade-6x9 perfect-bound | link |

<!--
Add your book above. Keep the images light (link out to full-res); this table is
just a directory, not an asset dump. See CONTRIBUTING.md.
-->
