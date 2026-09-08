# -*- coding: utf-8 -*-
"""Blink — print-and-play deck for the civ-ladder skin. 80 cards, nine to an A4
sheet, plus a sheet of backs.

    python3 build_skin_deck.py            -> Blink-skin-deck.html
    python3 build_skin_deck.py --backs    -> also a sheet of nine backs

Then render it the same way as every other document in this repo:

    ./build_pdfs.sh                       (the whole set), or, for this file only
    python3 embed_fonts.py skins/Blink-skin-deck.html /tmp/deck.html
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \\
        --headless --disable-gpu --no-pdf-header-footer \\
        --print-to-pdf=Blink-skin-deck.pdf file:///tmp/deck.html

The fonts step is not optional. Every builder here links Fraunces and IBM Plex
from Google Fonts; embed_fonts.py inlines them so the printed typography does not
depend on a network fetch succeeding at the moment of rendering.

The card face comes from face.py, the same module the on-screen proof uses.
"""

import json
import pathlib
import sys

import back
import face
from face import SUITS

HERE = pathlib.Path(__file__).resolve().parent
SKIN = json.loads((HERE / "civ-ladder.json").read_text(encoding="utf-8"))
WITH_BACKS = "--backs" in sys.argv

# 63 x 3 = 189 mm across, 88 x 3 = 264 mm down: nine cards inside an A4 page box
# of 9 mm / 8 mm, the same geometry build_cards.py uses.
PAGE_CSS = """
@page { size: A4; margin: 9mm 8mm; }
* { box-sizing: border-box; }
body { margin: 0; font-family: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
       -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.sheet { width: 189mm; font-size: 0; }
.card, .cardback { display: inline-block; vertical-align: top;
                   border: .2mm dashed #b8b8b8; }
.cardback { width: 63mm; height: 88mm; }
.pagebreak { page-break-after: always; }
"""


def sheets(items):
    out = ""
    for i in range(0, len(items), 9):
        out += "<div class='sheet'>" + "".join(items[i:i + 9]) + "</div>"
        out += "<div class='pagebreak'></div>"
    return out


cards = [face.card(t, r, SKIN) for r in range(1, 21) for t in SUITS]
pages = sheets(cards)
if WITH_BACKS:
    pages += "<div class='sheet'>" + "".join(
        back.back(f"b{i}") for i in range(9)) + "</div>"

HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Blink — civ-ladder deck</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{PAGE_CSS}{face.CARD_CSS}</style>
</head>
<body>{pages}</body>
</html>
"""

out = HERE / "Blink-skin-deck.html"
out.write_text(HTML, encoding="utf-8")
drawn = sum(1 for r in range(1, 21) for t in SUITS if f"{t}-{r}" in __import__("art").TECH)
print(f"{out}  {len(cards)} cards, {(len(cards) + 8) // 9} sheets"
      f"{' + 1 sheet of backs' if WITH_BACKS else ''}")
print(f"  {drawn} of {len(cards)} illustrations drawn; the rest print a dashed "
      f"placeholder and are otherwise complete and playable")
