#!/usr/bin/env bash
# Non-interactive demo for wordcount-cli.
#
# Runs the tool end to end against the bundled sample files and prints every
# command, its output, and its exit code. Nothing here is required to use the
# tool; it is a showcase for a terminal session.
#
#   sh demo.sh
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

banner() {
    printf '\n=== %s ===\n' "$1"
}

# run_expect EXPECTED_EXIT COMMAND...  -- run a command, printing output + exit code
run_expect() {
    expected="$1"
    shift
    set +e
    output="$("$@" 2>&1)"
    status=$?
    set -e
    printf '$ %s\n' "$*"
    printf '%s\n' "$output"
    printf 'exit %s (expected %s)\n' "$status" "$expected"
    if [ "$status" -ne "$expected" ]; then
        printf 'FAIL: expected exit %s, got %s\n' "$expected" "$status" >&2
        exit 1
    fi
}

banner "1. Count the words in the bundled sample (sample.txt: 'the quick brown fox')"
run_expect 0 "$PYTHON" wordcount.py sample.txt

banner "2. Count a longer text file"
printf 'examples/article.txt is a paragraph of prose:\n\n'
cat examples/article.txt
printf '\nwords: '
"$PYTHON" wordcount.py examples/article.txt

banner "3. A 0-byte file counts as 0"
: > "$WORK/empty.txt"
run_expect 0 "$PYTHON" wordcount.py "$WORK/empty.txt"

banner "4. A file of nothing but spaces, tabs and newlines counts as 0"
printf ' \t\n  \n\t \n' > "$WORK/blanks.txt"
run_expect 0 "$PYTHON" wordcount.py "$WORK/blanks.txt"

banner "5. No FILE argument is a usage error (exit 2, stdout empty)"
run_expect 2 "$PYTHON" wordcount.py

banner "6. Two FILE arguments are a usage error too (exit 2)"
run_expect 2 "$PYTHON" wordcount.py sample.txt sample.txt

banner "7. A path that does not exist is a file error (exit 1)"
run_expect 1 "$PYTHON" wordcount.py "$WORK/does-not-exist.txt"

banner "8. A directory is a file error (exit 1)"
run_expect 1 "$PYTHON" wordcount.py .

banner "9. Bytes that are not valid UTF-8 are a file error (exit 1)"
printf 'caf\351 \377\376\n' > "$WORK/latin1.txt"
run_expect 1 "$PYTHON" wordcount.py "$WORK/latin1.txt"

banner "10. Scriptable: the integer on stdout pipes straight into other tools"
total=0
for file in sample.txt examples/article.txt; do
    count="$("$PYTHON" wordcount.py "$file")"
    printf '%-24s %s words\n' "$file" "$count"
    total=$((total + count))
done
printf '%-24s %s words\n' "total" "$total"

printf '\nAll demo checks passed.\n'
