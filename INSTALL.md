# Installing and running wordcount-cli

wordcount-cli is a single standard-library Python file. Using it requires **no
installation at all** — no package manager, no virtualenv, no compile step, no
network access.

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python      | 3.8 or newer | any system interpreter works; `python3 --version` |

Nothing else. There is no package manager step the tool needs: `wordcount.py`
imports only `sys` and `typing` from the standard library.

## 1. Get the code

Unpack or clone the project and change into its root directory (the one
containing `wordcount.py`).

## 2. Optional: run the setup script

```console
$ sh install.sh
```

It checks the Python version, then installs the *dev-only* test runner
(`pytest`, pinned in `requirements.txt`). The tool itself does not use pytest —
the suite is written with stdlib `unittest` and runs with no packages installed.
The script is safe to re-run, needs no privileges (never `sudo`, never a system
package manager), and **exits** when it is done. It never starts anything in the
foreground.

If you would rather not run it, skip to step 3 — the tool works immediately.

## 3. Run the tool

```console
$ python3 wordcount.py sample.txt
4
```

```console
python3 wordcount.py FILE
```

Exactly one `FILE` argument. The word count is printed to stdout as a bare
integer; usage errors exit `2`, file/IO/decode errors exit `1`, success exits `0`.
See [README.md](README.md) for the full contract, the word rule and the
out-of-scope list.

Equivalent invocation:

```console
$ python3 -m wordcount sample.txt
4
```

## 4. Try the demo

```console
$ sh demo.sh
```

Runs every happy path and every error path, printing each command with its
output and exit code. No input is required and no server or service is started.

## 5. Run the tests (dev only)

```console
$ python3 -m unittest discover -s tests -v     # standard library only
$ pytest -q                                    # same suite, if pytest is installed
```

## Uninstalling

Delete the directory. The tool writes nothing anywhere else — no config file, no
cache, no state.
