#!/bin/sh
# Canonical Blink PDF build. wkhtmltopdf is the reference renderer; the PDFs
# shipped from the sandbox were made with WeasyPrint and paginate differently.
set -e
cd "$(dirname "$0")"
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

OPTS="--page-size A4 --margin-top 18mm --margin-bottom 16mm --margin-left 16mm --margin-right 16mm --enable-local-file-access --print-media-type"
wkhtmltopdf $OPTS Blink-rules-$RULES.html      ../Blink-rules-$RULES.pdf
wkhtmltopdf $OPTS Blink-first-game.html         ../Blink-first-game.pdf
wkhtmltopdf $OPTS Blink-card-effects.html       ../Blink-card-effects.pdf
wkhtmltopdf $OPTS Blink-map-objectives.html     ../Blink-map-objectives.pdf
wkhtmltopdf $OPTS Blink-playtest-sheet.html     ../Blink-playtest-sheet.pdf
wkhtmltopdf $OPTS Blink-variants.html           ../Blink-variants.pdf
wkhtmltopdf $OPTS Blink-rules-$RULES-bw.html   ../Blink-rules-$RULES-bw.pdf
wkhtmltopdf $OPTS Blink-first-game-bw.html      ../Blink-first-game-bw.pdf
wkhtmltopdf $OPTS Blink-card-effects-bw.html    ../Blink-card-effects-bw.pdf
wkhtmltopdf $OPTS Blink-map-objectives-bw.html  ../Blink-map-objectives-bw.pdf

# the card sheets set their own A4 page box, so no wkhtmltopdf margins
CARDOPTS="--page-size A4 --margin-top 0 --margin-bottom 0 --margin-left 0 --margin-right 0 --enable-local-file-access --print-media-type"
wkhtmltopdf $CARDOPTS Blink-deck-colour.html       ../Blink-deck-colour.pdf
wkhtmltopdf $CARDOPTS Blink-deck-bw.html           ../Blink-deck-bw.pdf
wkhtmltopdf $CARDOPTS Blink-objectives-colour.html ../Blink-objectives-colour.pdf
wkhtmltopdf $CARDOPTS Blink-objectives-bw.html     ../Blink-objectives-bw.pdf

# the player boards are SVG, so they go through a vector converter, not wkhtmltopdf
python3 -c "import cairosvg; cairosvg.svg2pdf(url='board_a4.svg',    write_to='../Blink-player-board-A4.pdf')"
python3 -c "import cairosvg; cairosvg.svg2pdf(url='board_a4-bw.svg', write_to='../Blink-player-board-A4-bw.pdf')"
python3 -c "import cairosvg; cairosvg.svg2pdf(url='board_blank.svg',  write_to='../Blink-player-board-blank.pdf')"
echo "done - PDFs written to the parent folder"
