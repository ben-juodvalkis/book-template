# A known-good environment for building the book — identical on macOS, Linux, and
# Windows (via Docker Desktop / WSL). This is the reliable escape hatch when a
# native install is fussy (WeasyPrint's system libraries on Windows in particular).
#
#   docker build -t book-template .
#   docker run --rm -v "$PWD:/book" book-template ./book build
#
# The bind mount puts your working copy at /book, so builds land in ./builds on
# your host just like a local run.

FROM python:3.11-slim

# System libraries that WeasyPrint needs at runtime (pip cannot provide these),
# plus poppler-utils (pdftotext -> the safe-margin guard) and mupdf-tools
# (mutool -> the shareable-draft rasterizer). fonts-dejavu-core gives a
# predictable fallback face so text renders the same everywhere.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        poppler-utils \
        mupdf-tools \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /book

# Install Python deps first so the layer caches across content changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# The project itself is bind-mounted at run time (see the docker run line above),
# so we don't COPY it in. Default to a full build; override with any `book` args.
CMD ["./book", "build"]
