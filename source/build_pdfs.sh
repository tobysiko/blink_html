#!/bin/sh
# Canonical Blink PDF build.
#
# This used to call wkhtmltopdf and describe it as the reference renderer. That
# stopped being true twice over: the project was archived in January 2023 and
# Homebrew disabled the cask in December 2024, so `brew install wkhtmltopdf`
# now fails outright — and more to the point its QtWebKit engine predates
# flexbox, grid and CSS custom properties, all three of which these documents
# use heavily (the rulebook alone has 50 custom properties). It could not have
# rendered them correctly even when it was installable.
#
# So the renderer is now whatever modern engine is on the machine, preferred in
# this order:
#
#   1. headless Chrome — renders exactly what you see when you open the file in
#      the browser, which is where these documents are designed and proofread.
#   2. WeasyPrint — a good print engine and the one the earlier shipped PDFs
#      were made with; paginates slightly differently from a browser.
#
# No page geometry is passed on the command line any more, because every
# document already declares its own `@page { size: A4; margin: ... }` — the
# rulebook 18/16/16/16, the card sheets 9/8. A renderer that honours CSS needs
# no help, and two sources of truth for the margins is one too many.
set -e
cd "$(dirname "$0")"
HERE=$(pwd)
# the version lives in version.py; the rules filename follows it
RULES=$(python3 -c "import version; print(version.VTAG)")

python3 build_figs.py
python3 check_figs.py
python3 build_html.py
python3 build_tutorial.py
python3 build_effects.py
python3 build_module.py
python3 build_playtest.py
python3 build_variants.py
python3 build_perks.py          # proposal: victory row perk tokens
python3 board_a4.py
python3 board_blank.py

# the printed numbers must still be the numbers the game is played with
python3 check_rules.py

# print-and-play card decks
python3 build_cards.py
python3 build_cards.py --bw
python3 build_objcards.py
python3 build_objcards.py --bw

# black-and-white booklets, derived from the HTML just built, so they can never
# lag behind the colour ones
python3 build_bw.py

# ---- pick a renderer ------------------------------------------------------
CHROME=""
for c in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
  "$(command -v google-chrome || true)" \
  "$(command -v chromium || true)" \
  "$(command -v chromium-browser || true)"
do
  if [ -n "$c" ] && [ -x "$c" ]; then CHROME="$c"; break; fi
done

if [ -n "$CHROME" ]; then
  RENDERER="chrome"
  echo "renderer: $CHROME"
elif command -v weasyprint >/dev/null 2>&1; then
  RENDERER="weasyprint"
  echo "renderer: weasyprint (pagination differs slightly from a browser)"
else
  echo "No PDF renderer found." >&2
  echo "Install one of:" >&2
  echo "  Google Chrome   https://www.google.com/chrome/   (best fidelity)" >&2
  echo "  WeasyPrint      pip install weasyprint" >&2
  echo "wkhtmltopdf is NOT an option: archived in 2023, and it cannot render" >&2
  echo "the flexbox, grid and custom properties these documents use." >&2
  exit 1
fi

# topdf <input.html> <output.pdf-relative-to-parent>
topdf() {
  IN="$HERE/$1"
  OUT="$HERE/../$2"
  if [ "$RENDERER" = "chrome" ]; then
    # --no-pdf-header-footer is the current flag; --print-to-pdf-no-header is
    # the older spelling. Chrome ignores switches it does not know, so passing
    # both keeps this working across versions rather than silently stamping a
    # URL and a date onto every page.
    "$CHROME" --headless --disable-gpu --no-sandbox \
      --no-pdf-header-footer --print-to-pdf-no-header \
      --virtual-time-budget=20000 \
      --print-to-pdf="$OUT" "file://$IN" 2>/dev/null
  else
    weasyprint "$IN" "$OUT"
  fi
  echo "  $2"
}

topdf "Blink-rules-$RULES.html"          "Blink-rules-$RULES.pdf"
topdf "Blink-first-game.html"            "Blink-first-game.pdf"
topdf "Blink-card-effects.html"          "Blink-card-effects.pdf"
topdf "Blink-map-objectives.html"        "Blink-map-objectives.pdf"
topdf "Blink-playtest-sheet.html"        "Blink-playtest-sheet.pdf"
topdf "Blink-variants.html"              "Blink-variants.pdf"
# A proposal, not a component — see VROW-PERKS.md. Printed so it can be cut
# out and played with, which is the only way to find out if it is any good.
topdf "Blink-perk-tokens.html"           "Blink-perk-tokens.pdf"
topdf "Blink-rules-$RULES-bw.html"       "Blink-rules-$RULES-bw.pdf"
topdf "Blink-first-game-bw.html"         "Blink-first-game-bw.pdf"
topdf "Blink-card-effects-bw.html"       "Blink-card-effects-bw.pdf"
topdf "Blink-map-objectives-bw.html"     "Blink-map-objectives-bw.pdf"

# The card sheets set their own tighter page box (9mm/8mm); nothing extra here.
topdf "Blink-deck-colour.html"           "Blink-deck-colour.pdf"
topdf "Blink-deck-bw.html"               "Blink-deck-bw.pdf"
topdf "Blink-objectives-colour.html"     "Blink-objectives-colour.pdf"
topdf "Blink-objectives-bw.html"         "Blink-objectives-bw.pdf"

# The player boards are SVG. They used to go through cairosvg, which needs the
# native Cairo library under it — fiddly on macOS, and in practice not installed,
# so the boards were the one thing this script could not produce. A browser
# renders SVG to vector PDF perfectly well, so they go through the same renderer
# as everything else; wrap_svg.py only supplies the page geometry.
board() {
  python3 wrap_svg.py "$1" "_board_tmp.html"
  topdf "_board_tmp.html" "$2"
  rm -f "_board_tmp.html"
}
board board_a4.svg        Blink-player-board-A4.pdf
board board_a4-bw.svg     Blink-player-board-A4-bw.pdf
board board_blank.svg     Blink-player-board-blank.pdf

# A PDF that is a single blank page is what a renderer produces when it failed
# quietly — worth catching here rather than at the printer.
python3 - "$HERE/.." <<'PY'
import pathlib, sys
bad = []
for p in sorted(pathlib.Path(sys.argv[1]).glob("Blink-*.pdf")):
    n = p.stat().st_size
    # A renderer that fails quietly still writes a valid one-page PDF, and that
    # comes out at a couple of kB. Anything this small never contains a booklet
    # or a board.
    if n < 8000:
        bad.append(f"{p.name} is only {n // 1024} kB — probably a blank page")
print("\n".join("  suspicious: " + b for b in bad) if bad
      else "every PDF looks a plausible size")
PY
echo "done - PDFs written to the parent folder"
