@echo off
rem Thin wrapper so you can type `book <command>` instead of `python book.py ...`.
rem The real logic (and interpreter selection) lives in book.py.
python "%~dp0book.py" %*
