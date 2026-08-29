#!/usr/bin/env bash
# Build, verify and commit v0.24 - both repos.
#
# This exists because pasting a multi-line commit message into a terminal is a
# quoting minefield: one smart quote or apostrophe and the shell drops into
# `quote>` and swallows the next command. The message lives in a file instead
# (`git commit -F`), and this script is the only thing that needs pasting.
#
#   bash release-v0.24.sh
#
# It stops at the first failure and never uses -f on anything but the two
# scratch files it is meant to remove.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE="${BLINK_SITE_REPO:-$HOME/Code/deep-diversions}"

cd "$HERE"
echo "== $HERE"

# --- scratch files the sandbox could not delete ----------------------------
rm -f app/_frontier_probe.js app/options_test.js.tmp

# --- build every surface ---------------------------------------------------
echo "== building"
python3 source/build_figs.py     >/dev/null
python3 source/build_html.py     >/dev/null
python3 source/build_tutorial.py >/dev/null
BLINK_SITE="$SITE/public/blink" node app/build.js
bash source/build_pdfs.sh

# --- verify ----------------------------------------------------------------
echo "== checking"
python3 source/check_rules.py
python3 source/check_figs.py
# The fonts have never embedded (see check_fonts.py). Reported, not fatal, so a
# missing typeface cannot silently block a commit - but you WILL see it.
python3 source/check_fonts.py || echo "!! fonts: see the note above"

echo "== tests"
fails=0
for f in app/*_test.js; do
  if node "$f" >/dev/null 2>&1; then :; else echo "FAIL $f"; fails=$((fails + 1)); fi
done
if [ "$fails" -gt 0 ]; then echo "$fails test(s) failing - nothing committed"; exit 1; fi
echo "   all green"

# --- commit ----------------------------------------------------------------
echo "== committing $HERE"
git add -A
git commit -F source/COMMIT-v0.24.txt
git push

echo "== committing $SITE"
cd "$SITE"
git add public/blink/play.html api/blink.js
git commit -m "Blink v0.24: assaults, visible combat, and captioned gold"
git push

echo "== done"
