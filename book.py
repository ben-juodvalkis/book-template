#!/usr/bin/env python3
"""
book — one entry point for the whole print-book pipeline.

Run it directly (`python book.py <command>`), or via the thin wrappers `./book`
(macOS/Linux) and `book.cmd` (Windows) so you don't have to type `python`.

Commands
  build [--no-trim] [--html-only]     Build the whole book -> builds/<slug>/
  section <name> [opts]               Build one section -> .temp/  (iteration)
  page <name> --page N[-M] [opts]     Build one page (or range) -> .temp/
  trimmed | preview [--no-draft]      Trim-crop the master to an 8x10 preview
  draft [--in P] [--dpi N] [...]      Rasterize a build PDF to a small, emailable draft
  spread-photo <img> [opts]           Crop a photo to the cross-gutter spread ratio
  doctor                              Check the toolchain (Python libs + optional tools)
  help                                Show this message

Every command except `doctor`/`help` forwards its options straight to the
underlying script in scripts/, so all the flags documented there still work
(e.g. `./book section 01-title --first-page 7`, `./book page 01-title --page 2`).

Which Python runs the build (first that exists wins):
  1. $BOOK_PYTHON            — explicit override (e.g. a Homebrew WeasyPrint interp)
  2. ./.venv                 — the project virtualenv (the recommended setup)
  3. the interpreter running this file
The chosen interpreter's directory is put on PATH for the child, so an activated
venv is never required.
"""

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "scripts")

# Subcommand -> script filename in scripts/. Aliases point at the same script.
COMMANDS = {
    "build":        "master-build.py",
    "section":      "master-build-section.py",
    "page":         "master-build-page.py",
    "trimmed":      "master-build-trimmed.py",
    "preview":      "master-build-trimmed.py",   # alias for `trimmed`
    "draft":        "master-build-draft.py",
    "spread-photo": "spread-photo.py",
}


def venv_python():
    """Path to the project virtualenv interpreter if ./.venv exists, else None."""
    win = os.path.join(HERE, ".venv", "Scripts", "python.exe")
    nix = os.path.join(HERE, ".venv", "bin", "python")
    for p in (nix, win):
        if os.path.exists(p):
            return p
    return None


def resolve_python():
    """Pick the interpreter that will run the build scripts (see module docstring)."""
    override = os.environ.get("BOOK_PYTHON")
    if override:
        return override
    return venv_python() or sys.executable


def child_env(python):
    """Environment for the child process, with the interpreter's dir on PATH.

    This lets a non-activated venv still find its console tools, and keeps the
    scripts' own subprocess calls (mutool, pdftotext) resolving predictably.
    """
    env = dict(os.environ)
    bindir = os.path.dirname(os.path.abspath(python))
    env["PATH"] = bindir + os.pathsep + env.get("PATH", "")
    return env


def run_script(script, args):
    python = resolve_python()
    cmd = [python, os.path.join(SCRIPTS, script), *args]
    return subprocess.run(cmd, env=child_env(python)).returncode


def doctor():
    """Report on the toolchain the build actually needs."""
    python = resolve_python()
    print(f"Interpreter: {python}")
    if os.environ.get("BOOK_PYTHON"):
        print("  (from $BOOK_PYTHON)")
    elif venv_python():
        print("  (from ./.venv)")
    else:
        print("  (this interpreter — no ./.venv found; `python3 -m venv .venv` to make one)")
    print()

    # Required Python libraries — probed in the resolved interpreter so the report
    # reflects exactly what a build would see.
    probe = (
        "import importlib, json\n"
        "out = {}\n"
        "for m, attr in (('weasyprint','__version__'),('pikepdf','__version__'),('PIL','__version__')):\n"
        "    try:\n"
        "        mod = importlib.import_module(m)\n"
        "        out[m] = getattr(mod, attr, '?')\n"
        "    except Exception as e:\n"
        "        out[m] = 'MISSING'\n"
        "print(json.dumps(out))\n"
    )
    import json
    try:
        res = subprocess.run([python, "-c", probe], capture_output=True, text=True,
                             env=child_env(python))
        libs = json.loads(res.stdout or "{}")
    except Exception:
        libs = {}

    labels = {
        "weasyprint": "WeasyPrint  (HTML/CSS -> PDF renderer)",
        "pikepdf":    "pikepdf     (PDF merge + bleed geometry)",
        "PIL":        "Pillow      (image prep + draft rasterizer)",
    }
    ok = True
    print("Required Python libraries:")
    for m, label in labels.items():
        v = libs.get(m, "MISSING")
        mark = "MISSING  <- pip install -r requirements.txt" if v == "MISSING" else v
        if v == "MISSING":
            ok = False
        print(f"  [{'x' if v != 'MISSING' else ' '}] {label}: {mark}")

    print("\nOptional command-line tools:")
    opt = [
        ("pdftotext", "safe-margin guard (poppler-utils) — build still runs without it"),
        ("mutool",    "shareable-draft rasterizer (mupdf-tools) — only needed for drafts"),
    ]
    env = child_env(python)
    for tool, why in opt:
        found = shutil.which(tool, path=env["PATH"])
        print(f"  [{'x' if found else ' '}] {tool}: {'found' if found else 'not found'} — {why}")

    print()
    if ok:
        print("Ready to build:  ./book build")
    else:
        print("Not ready — install the Python libraries above, then re-run `./book doctor`.")
        print("See the README \"Install the toolchain\" section for the system libraries")
        print("WeasyPrint needs (Pango, etc.), which pip cannot install.")
    return 0 if ok else 1


def usage(exit_code=0):
    print(__doc__.strip())
    return exit_code


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("help", "-h", "--help"):
        sys.exit(usage(0))

    cmd, rest = argv[0], argv[1:]
    if cmd == "doctor":
        sys.exit(doctor())
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd!r}\n")
        sys.exit(usage(2))
    sys.exit(run_script(COMMANDS[cmd], rest))


if __name__ == "__main__":
    main()
