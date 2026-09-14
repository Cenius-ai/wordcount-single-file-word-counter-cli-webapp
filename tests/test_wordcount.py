"""Dev-only tests for wordcount.py.

Run with the standard library:

    python3 -m unittest discover -s tests -v

The suite uses only stdlib unittest (pytest is an optional convenience and
will happily collect the same cases). Nothing in this directory is needed to
use the tool.

How the CLI is exercised
------------------------
Each case executes ``wordcount.py`` through its real entry point -- the
``if __name__ == "__main__": sys.exit(main(sys.argv[1:]))`` block -- with
``sys.argv`` wired exactly as a shell would pass it, and asserts on the three
things the tool promises at the process boundary: the exit status (the
``SystemExit`` code), stdout, and stderr. The script is run as ``__main__``
with ``runpy``, so no process is spawned and no shell is involved anywhere in
this suite. ``sh demo.sh`` exercises the same contract across a real OS
process boundary if you want that second proof.
"""

import contextlib
import io
import runpy
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "wordcount.py"
SAMPLE = REPO_ROOT / "sample.txt"
USAGE_LINE = "usage: wordcount.py FILE"
TRACEBACK_MARKER = "Traceback (most recent call last)"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import wordcount  # noqa: E402  (imported after the sys.path tweak on purpose)


class CliResult:
    """What one CLI run looks like from the outside: status, stdout, stderr."""

    __slots__ = ("returncode", "stdout", "stderr")

    def __init__(self, returncode: int, stdout: str, stderr: str) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _exit_status(signal: SystemExit) -> int:
    """Read the status out of the SystemExit the script raises from sys.exit()."""
    code = signal.code
    if code is None:
        return 0
    return code if isinstance(code, int) else 1


def run_cli(*args: str, as_module: bool = False) -> CliResult:
    """Run the CLI with *args* and capture its exit status, stdout and stderr.

    ``as_module=True`` executes it the way ``python3 -m wordcount`` would
    (``runpy.run_module``); the default runs the script file itself
    (``runpy.run_path``). Both go through the script's real ``__main__`` block.
    """
    stdout, stderr = io.StringIO(), io.StringIO()
    saved_argv = sys.argv
    status = 0
    try:
        sys.argv = [str(SCRIPT), *args]
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            if as_module:
                runpy.run_module("wordcount", run_name="__main__")
            else:
                runpy.run_path(str(SCRIPT), run_name="__main__")
    except SystemExit as signal:
        status = _exit_status(signal)
    finally:
        sys.argv = saved_argv
    return CliResult(status, stdout.getvalue(), stderr.getvalue())


class CliTestCase(unittest.TestCase):
    """Shared helpers: one temp dir per test plus the CLI runner."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def write_text(self, name: str, text: str) -> Path:
        path = self.tmp / name
        path.write_text(text, encoding="utf-8")
        return path

    def write_bytes(self, name: str, data: bytes) -> Path:
        path = self.tmp / name
        path.write_bytes(data)
        return path

    def run_cli(self, *args: str, as_module: bool = False) -> CliResult:
        return run_cli(*args, as_module=as_module)

    def assert_no_traceback(self, stderr: str) -> None:
        self.assertNotIn(TRACEBACK_MARKER, stderr)

    def assert_single_error_line(self, stderr: str, expected_text: str) -> None:
        self.assertTrue(stderr.endswith("\n"), f"stderr not newline-terminated: {stderr!r}")
        self.assertEqual(stderr.count("\n"), 1, f"stderr is not one line: {stderr!r}")
        self.assertIn(expected_text, stderr)
        self.assert_no_traceback(stderr)


class TestCountingRule(unittest.TestCase):
    """The pure rule from D4, exercised without running the CLI."""

    def test_one_two_three_counts_three(self) -> None:
        self.assertEqual(wordcount.count_words("one two three"), 3)

    def test_any_run_of_whitespace_delimits_one_token(self) -> None:
        self.assertEqual(wordcount.count_words("alpha\nbeta\t gamma  delta"), 4)
        self.assertEqual(wordcount.count_words("  leading and trailing   "), 3)

    def test_empty_and_whitespace_only_text_count_zero(self) -> None:
        for text in ("", " ", "\n", "\t", "   \n\t  \n \t "):
            with self.subTest(text=repr(text)):
                self.assertEqual(wordcount.count_words(text), 0)

    def test_punctuation_stays_attached_to_its_token(self) -> None:
        self.assertEqual(wordcount.count_words("hi, there"), 2)
        self.assertEqual(wordcount.count_words("well — that depends"), 4)


class TestHappyPaths(CliTestCase):
    """T1 / T2: counts, stdout discipline, exit code 0."""

    def test_sample_file_prints_four(self) -> None:
        result = self.run_cli(str(SAMPLE))
        self.assertEqual(result.stdout, "4\n")
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.returncode, 0)

    def test_single_word_file_prints_one(self) -> None:
        path = self.write_text("one.txt", "hello\n")
        result = self.run_cli(str(path))
        self.assertEqual(result.stdout, "1\n")
        self.assertEqual(result.returncode, 0)

    def test_empty_file_prints_zero(self) -> None:
        path = self.write_bytes("empty.txt", b"")
        result = self.run_cli(str(path))
        self.assertEqual(result.stdout, "0\n")
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.returncode, 0)

    def test_whitespace_only_file_prints_zero(self) -> None:
        path = self.write_text("blanks.txt", "  \t\n\t  \n \n")
        result = self.run_cli(str(path))
        self.assertEqual(result.stdout, "0\n")
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.returncode, 0)

    def test_punctuation_tokens_count_two(self) -> None:
        path = self.write_text("punct.txt", "hi, there\n")
        result = self.run_cli(str(path))
        self.assertEqual(result.stdout, "2\n")
        self.assertEqual(result.returncode, 0)

    def test_non_ascii_utf8_text_counts_tokens(self) -> None:
        path = self.write_text("utf8.txt", "café déjà vu\n")
        result = self.run_cli(str(path))
        self.assertEqual(result.stdout, "3\n")
        self.assertEqual(result.returncode, 0)

    def test_stdout_carries_only_the_integer(self) -> None:
        path = self.write_text("mixed.txt", "alpha beta\ngamma\n")
        result = self.run_cli(str(path))
        self.assertEqual(result.stdout, "3\n")

    def test_module_entry_point_works_too(self) -> None:
        result = self.run_cli(str(SAMPLE), as_module=True)
        self.assertEqual(result.stdout, "4\n")
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.returncode, 0)


class TestUsageErrors(CliTestCase):
    """T3: missing or extra arguments exit 2 with the usage line and no stdout."""

    def assert_usage_failure(self, *args: str) -> None:
        result = self.run_cli(*args)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, USAGE_LINE + "\n")

    def test_no_argument_exits_two(self) -> None:
        self.assert_usage_failure()

    def test_two_arguments_exit_two(self) -> None:
        self.assert_usage_failure("a.txt", "b.txt")

    def test_three_arguments_exit_two(self) -> None:
        self.assert_usage_failure("a.txt", "b.txt", "c.txt")


class TestFileErrors(CliTestCase):
    """T3: missing, directory and undecodable paths exit 1 with a one-line error."""

    def test_nonexistent_path_exits_one_and_names_it(self) -> None:
        missing = self.tmp / "nope.txt"
        result = self.run_cli(str(missing))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assert_single_error_line(result.stderr, str(missing))

    def test_directory_exits_one(self) -> None:
        result = self.run_cli(str(self.tmp))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assert_single_error_line(result.stderr, str(self.tmp))

    def test_invalid_utf8_file_exits_one(self) -> None:
        path = self.write_bytes("latin1.txt", b"na\xefve caf\xe9 \xff\xfe\n")
        result = self.run_cli(str(path))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assert_single_error_line(result.stderr, str(path))

    def test_an_empty_path_argument_is_a_file_error(self) -> None:
        result = self.run_cli("")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr.count("\n"), 1)
        self.assert_no_traceback(result.stderr)

    def test_no_error_path_prints_a_traceback(self) -> None:
        bad_bytes = self.write_bytes("bad.bin", b"\xff\xfe\x00word\n")
        cases = [
            (),
            ("one.txt", "two.txt"),
            (str(self.tmp / "ghost.txt"),),
            (str(self.tmp),),
            (str(bad_bytes),),
        ]
        for args in cases:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assert_no_traceback(result.stderr)
                self.assertNotEqual(result.stderr.strip(), "")


class TestMainFunction(CliTestCase):
    """main(argv) -> int is the CLI contract, observable without running the CLI."""

    def call_main(self, *args: str):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = wordcount.main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_main_returns_two_for_a_missing_argument(self) -> None:
        code, out, err = self.call_main()
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertEqual(err, USAGE_LINE + "\n")

    def test_main_prints_the_count_and_returns_zero(self) -> None:
        code, out, err = self.call_main(str(SAMPLE))
        self.assertEqual(code, 0)
        self.assertEqual(out, "4\n")
        self.assertEqual(err, "")

    def test_main_returns_one_for_a_missing_file(self) -> None:
        code, out, err = self.call_main(str(self.tmp / "gone.txt"))
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assert_no_traceback(err)


if __name__ == "__main__":
    unittest.main()
