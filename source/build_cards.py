# -*- coding: utf-8 -*-
"""Blink -- printable main deck. 80 cards: ranks 1-20 in four suits.

Generated, so a card face can never disagree with the rules. The effect text is
imported from build_effects.py, which is itself derived from the rulebook's rank
bands, so all three documents move together.

  python3 build_cards.py            -> Blink-deck-colour.html
  python3 build_cards.py --bw       -> Blink-deck-bw.html
"""
import sys, pathlib, importlib.util
import cardstock as CS
from version import VTAG

BW = "--bw" in sys.argv

# --- effect text, pulled from the effects document so it cannot drift --------
spec = importlib.util.spec_from_file_location("_eff", "build_effects.py")
# build_effects.py writes a file on import; read its source for the tables only.
src = pathlib.Path("build_effects.py").read_text(encoding="utf-8")
ns = {}
exec(src.split("HTML = f\"\"\"", 1)[0].replace(
    'src = pathlib.Path("build_html.py").read_text(encoding="utf-8")',
    'src = ""').replace(
    "CSS = src.split('CSS = \"\"\"', 1)[1].split('\"\"\"', 1)[0]", "CSS = ''"), ns)
SHORT = ns["SHORT"]          # [(A, B, C)] per band of five ranks
BANDS = ns["BANDS"]

# Which ranks are used at which player count (from sim/engine.py _deal).
IN_PLAY = {2: range(6, 16), 3: range(3, 19), 4: range(1, 21)}


def counts_line(rank):
    ns_ = [n for n in (2, 3, 4) if rank in IN_PLAY[n]]
    return " ".join(f"{n}p" for n in ns_)


def card(rank, ter):
    pal = CS.COLOUR[ter]
    a, b, c = SHORT[(rank - 1) // 5]
    band = BANDS[(rank - 1) // 5][0]
    ink = "#111" if BW else pal["side"]
    art_ink = "#000" if BW else pal["side"]
    strip_bg = "#fff" if BW else pal["side"]
    strip_fg = "#111" if BW else "#fff"
    starting = "starting" if rank <= 10 else "advanced"
    # The corner index is rank directly over suit, tight, so a fanned hand can
    # be read and sorted from the top-left corner alone -- and repeated rotated
    # in the opposite corner so the card works either way up.
    idx = (f'<span class="r" style="color:{ink}">{rank}</span>'
           f'<span class="g">{CS.glyph(ter, BW, 14)}</span>')
    return f"""
<div class="card">
  <span class="idx tl">{idx}</span>
  <span class="idx br">{idx}</span>

  <div class="head">
    <span class="nm" style="color:{ink}">{ter.upper()}</span>
    <span class="st">holds {CS.HOLDS[ter]} &middot; attack {CS.ATTACK[ter]}</span>
  </div>
  <div class="bar" style="background:{strip_bg}">{
      CS.swatch(ter, BW, h=3) if BW else ""}</div>

  <div class="art">{CS.glyph(ter, BW, 66, ink=art_ink)}</div>

  <div class="eff">
    <div class="row"><span class="k">A</span><span class="v">{a}</span></div>
    <div class="row"><span class="k">B</span><span class="v">{b}</span></div>
    <div class="row"><span class="k">C</span><span class="v">{c}</span></div>
  </div>

  <div class="foot">ranks {band} &middot; {starting} &middot; {counts_line(rank)}</div>
</div>"""


CSS = CS.PAGE_CSS + """
/* Corner index: rank over suit, hugging the corner, repeated rotated. */
.idx { position: absolute; display: flex; flex-direction: column;
       align-items: center; line-height: 1; z-index: 2; }
.idx.tl { top: 2.0mm; left: 3.0mm; }
.idx.br { bottom: 2.0mm; right: 3.0mm; transform: rotate(180deg); }
.idx .r { font-family: "Fraunces", Georgia, serif; font-size: 15pt;
          font-weight: 600; line-height: .84; }
.idx .g { margin-top: .5mm; }

.head { padding: 3.0mm 3.4mm 2.2mm 14.5mm; min-height: 15mm; }
.nm { display: block; font-size: 9.5pt; font-weight: 600; letter-spacing: .15em; }
.st { display: block; font-size: 6.8pt; letter-spacing: .04em; color: #777;
      margin-top: .8mm; }
.bar { height: 3mm; flex: none; }
.art { flex: 1; display: flex; align-items: center; justify-content: center;
       opacity: .93; }
.eff { padding: 0 3.4mm 13mm; }
.eff .row { display: flex; gap: 2mm; align-items: baseline;
            padding: 2.1mm 0; border-top: .18mm solid #ddd; }
.k { font-family: "IBM Plex Mono", monospace; font-size: 8pt; font-weight: 600;
     width: 3.6mm; flex: none; color: #555; }
.v { font-size: 8.4pt; line-height: 1.25; }
.foot { position: absolute; bottom: 3.2mm; left: 3.4mm; right: 14.5mm;
        font-size: 6.3pt; color: #999; letter-spacing: .05em; }
.back { align-items: center; justify-content: center; }
.bmark { display: flex; gap: 2mm; opacity: .55; margin-bottom: 4mm; }
.bname { font-family: "Fraunces", Georgia, serif; font-size: 21pt;
         font-weight: 600; letter-spacing: .24em; }
.bver { font-size: 6.5pt; letter-spacing: .2em; color: #aaa;
        margin-top: 2mm; }
"""

def back():
    return f"""
<div class="card back">
  <div class="bmark">{CS.glyph("mountain", BW, 24)}{CS.glyph("forest", BW, 24)}
       {CS.glyph("plains", BW, 24)}{CS.glyph("ocean", BW, 24)}</div>
  <div class="bname">BLINK</div>
  <div class="bver">{VTAG}</div>
</div>"""


cards = [card(r, t) for r in range(1, 21) for t in CS.TER_ORDER]
pages = ""
for i in range(0, len(cards), 9):
    pages += "<div class='sheet'>" + "".join(cards[i:i + 9]) + "</div>"
    pages += "<div class='pagebreak'></div>"
# One sheet of nine backs. Print it as many times as you need, or skip it and
# sleeve the cards in front of an ordinary deck.
pages += "<div class='sheet'>" + "".join(back() for _ in range(9)) + "</div>"

HTML = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Blink deck</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>{pages}</body></html>"""

out = pathlib.Path("Blink-deck-bw.html" if BW else "Blink-deck-colour.html")
out.write_text(HTML, encoding="utf-8")
print(f"{out}  {len(cards)} cards, {(len(cards)+8)//9} pages")
