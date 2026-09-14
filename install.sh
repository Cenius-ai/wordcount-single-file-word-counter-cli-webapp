#!/usr/bin/env bash
# One-shot setup for wordcount-cli.
#
# The tool itself has zero runtime dependencies (standard library only), so this
# script installs nothing the tool needs to run; it verifies the Python version
# and makes the optional dev-only test runner available. It EXITS when done --
# running the tool is a separate command:
#
#     python3 wordcount.py FILE
#
# Safe to re-run. Run it as an unprivileged user: no sudo, no system packages.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    printf 'error: %s not found on PATH; install Python 3.8+ first\n' "$PYTHON" >&2
    exit 1
fi

if ! "$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)'; then
    printf 'error: %s is too old; wordcount-cli needs Python 3.8+\n' \
        "$("$PYTHON" -c 'import sys; print(sys.version.split()[0])')" >&2
    exit 1
fi

# Dev-only convenience: pytest is NOT required. The suite is stdlib unittest and
# runs without it, so a failure here is a warning, never a broken install.
if "$PYTHON" -c 'import pytest' >/dev/null 2>&1; then
    printf 'note: pytest already available; leaving the environment untouched\n'
else
    "$PYTHON" -m pip install --upgrade pip setuptools wheel >/dev/null 2>&1 \
        || printf 'note: could not upgrade pip/setuptools/wheel; continuing\n' >&2
    if "$PYTHON" -m pip install -r requirements.txt; then
        printf 'note: installed the optional dev-only test runner (pytest)\n'
    else
        printf 'warning: could not install the optional dev-only test runner; continuing\n' >&2
        printf '         the tool and its suite need no packages:\n' >&2
        printf '         %s -m unittest discover -s tests -v\n' "$PYTHON" >&2
    fi
fi

# Cheap import self-check so a broken environment fails here, not at first use.
"$PYTHON" -c 'import wordcount; assert wordcount.count_words("one two three") == 3'

printf 'Setup complete (no runtime dependencies).\n'
printf 'Run it : %s wordcount.py FILE\n' "$PYTHON"
printf 'Demo   : sh demo.sh\n'
printf 'Tests  : %s -m unittest discover -s tests -v\n' "$PYTHON"
