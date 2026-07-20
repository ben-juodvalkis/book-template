# Fonts — self-hosting for reproducible renders

By default `src/master-header.html` loads a font from a CDN (Google Fonts). That's
fine for a quick start, but for **print** it has two problems:

- **Not reproducible** — the hosted font can update, so the same source can render
  differently over time or between machines.
- **Needs the network at build time** — offline builds and locked-down CI can't
  fetch it, and fall back to a different face silently.

Self-hosting pins the exact font files into `fonts/` and renders from disk, so the
output is identical everywhere. Here's the whole workflow.

## 1. Declare your fonts

Edit `fonts/fonts.txt` — one font per line, pipe-separated:

```
family | weight | style | source
```

- **family** — the CSS name you'll use (e.g. `Work Sans`)
- **weight** — `400`, `700`, or a variable range like `100 900`
- **style** — `normal` or `italic`
- **source** — an `https` URL to a redistributable font file, **or** a local path
  (relative to the project root, or absolute) to copy in

```
Work Sans | 100 900 | normal | https://your-source/WorkSans[wght].woff2
Work Sans | 100 900 | italic | https://your-source/WorkSans-Italic[wght].woff2
```

> Only self-host fonts you may redistribute. [OFL](https://openfontlicense.org)
> fonts qualify — keep each font's `OFL.txt` in `fonts/` next to the file.

## 2. Fetch them

```
./book fonts          # download/copy each source, write fonts/fonts.css
./book fonts --list   # just show what the manifest declares
```

This writes the font files and a generated `fonts/fonts.css` full of `@font-face`
rules pointing at them.

> Behind a corporate proxy, `./book fonts` honors `HTTPS_PROXY`; if TLS fails,
> point `SSL_CERT_FILE` at your CA bundle. Or download the files by hand and use
> local paths in the manifest.

## 3. Use them

In `src/master-header.html`, delete the three Google Fonts `<link>`s and uncomment:

```html
<link rel="stylesheet" href="fonts/fonts.css">
```

Then set the family in `src/styles/design.css`:

```css
body { font-family: 'Work Sans', Helvetica, Arial, sans-serif; }
```

## 4. Commit the fonts

Commit the files in `fonts/` (the binaries, their license, and `fonts.css`) so
every collaborator and CI renders with the exact same faces. `./book doctor` and
CI don't require fonts, but committing them is what makes renders byte-stable.

---

**Tip:** variable fonts (one file, a weight range) keep `fonts/` small. If you
only use a couple of weights, static files are fine too — list each as its own
manifest line.
