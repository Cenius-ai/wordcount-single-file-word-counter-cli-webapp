#!/usr/bin/env python3
"""Count the whitespace-separated words in one text file.

Usage:
    python3 wordcount.py FILE

The count is printed to stdout as a single integer on its own line; every
diagnostic goes to stderr. Exit codes: 0 success, 1 file/IO/decode error,
2 usage error. No traceback is ever printed for a handled error.

Standard library only, one runtime file.
"""

from __future__ import annotations

import sys
from typing import List, Optional, Sequence

PROG = "wordcount.py"
USAGE = f"usage: {PROG} FILE"

EXIT_SUCCESS = 0
EXIT_FILE_ERROR = 1
EXIT_USAGE_ERROR = 2

USAGE_MESSAGE = USAGE


def count_words(text: str) -> int:
    """Return the number of whitespace-separated tokens in *text*.

    Any run of whitespace (spaces, tabs, newlines, form feeds, ...) delimits
    one token, exactly like ``len(text.split())``. Empty text and text made
    only of whitespace therefore both yield 0 with no special case.
    """
    return len(text.split())


def read_text(path: str) -> str:
    """Read *path* as UTF-8 text.

    Raises the usual ``OSError`` subclasses for I/O problems and
    ``UnicodeDecodeError`` when the bytes are not valid UTF-8.
    """
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _io_message(error: OSError) -> str:
    """Turn an I/O error into a short, human-readable reason."""
    if isinstance(error, FileNotFoundError):
        return "no such file or directory"
    if isinstance(error, IsADirectoryError):
        return "is a directory"
    if isinstance(error, PermissionError):
        return "permission denied"
    return error.strerror or error.__class__.__name__


def _file_error(path: str, reason: str) -> int:
    """Print a one-line file error on stderr and return the file exit code."""
    print(f"{PROG}: cannot read {path!r}: {reason}", file=sys.stderr)
    return EXIT_FILE_ERROR


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the CLI for *argv* (defaults to ``sys.argv[1:]``); return an exit code."""
    args: List[str] = list(sys.argv[1:] if argv is None else argv)

    if len(args) != 1:
        print(USAGE_MESSAGE, file=sys.stderr)
        return EXIT_USAGE_ERROR

    path = args[0]
    try:
        text = read_text(path)
    except UnicodeDecodeError:
        return _file_error(path, "not valid UTF-8 text")
    except OSError as error:
        return _file_error(path, _io_message(error))

    print(count_words(text))
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
