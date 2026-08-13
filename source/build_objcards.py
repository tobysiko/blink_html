# -*- coding: utf-8 -*-
"""Blink -- printable secret map-objective deck, with card backs.

Twelve cards. Each carries the hex diagram of its terrain pattern, taken from
pattern_figs.py -- the same drawing the objectives booklet prints, so the card
and the booklet can never show different shapes.

  python3 build_objcards.py         -> Blink-objectives-colour.html
  python3 build_objcards.py --bw    -> Blink-objectives-bw.html
"""
import sys, pathlib, re
import cardstock as CS
from version import VTAG
import pattern_figs as PF_MOD
from build_module import DECK

BW = "--bw" in sys.argv
PF = PF_MOD.PF


def art(key):
    """Card art for one objective.

    Size stripping happens on the opening <svg> tag ONLY and *before* mono_svg
    injects the hatch <defs> -- a blanket re.sub would otherwise delete the first
    <pattern>'s own width attribute, and an unsized pattern silently renders as
    nothing.
    """
    svg = PF[key]
    head, rest = svg.split(">", 1)
    head = re.sub(r'\s(?:width|height)="[^"]*"', "", head)
    head += ' class="pat" preserveAspectRatio="xMidYMid meet"'
    svg = head + ">" + rest
    return CS.mono_svg(svg) if BW else svg


def card(key, name, pts, tagline, req):
    return f"""
<div class="card">
  <div class="top"><span class="eyebrow">Map objective</span>
       <span class="pts">{pts}</span></div>
  <h2>{name}</h2>
  <p class="tag">{tagline}</p>
  <div class="artbox">{art(key)}</div>
  <p class="req">{req}</p>
  <p class="foot">Keep hidden. Reveal when the victory rows are scored.<br>
     Scores once, in full, or not at all.</p>
</div>"""


def back():
    return f"""
<div class="card back">
  <div class="bmark">{CS.glyph("mountain", BW, 26)}{CS.glyph("forest", BW, 26)}
       {CS.glyph("plains", BW, 26)}{CS.glyph("ocean", BW, 26)}</div>
  <div class="bname">BLINK</div>
  <div class="bsub">map objective &middot; {VTAG}</div>
</div>"""


CSS = CS.PAGE_CSS + """
.card { padding: 4mm 4.2mm 3mm; }
.top { display: flex; justify-content: space-between; align-items: center; }
.eyebrow { font-size: 6.2pt; letter-spacing: .2em; text-transform: uppercase;
           color: #8a8a8a; }
.pts { font-family: "Fraunces", Georgia, serif; font-size: 17pt; font-weight: 600;
       line-height: 1; border: .4mm solid #333; border-radius: 50%;
       width: 8.4mm; height: 8.4mm; display: flex; align-items: center;
       justify-content: center; }
h2 { font-family: "Fraunces", Georgia, serif; font-size: 14pt; font-weight: 600;
     margin: 2.2mm 0 0; line-height: 1.1; }
.tag { font-size: 7.6pt; font-style: italic; color: #777; margin: 1mm 0 0;
       line-height: 1.3; }
.artbox { flex: 1; display: flex; align-items: center; justify-content: center;
          padding: 2mm 0; min-height: 0; }
.pat { max-width: 100%; max-height: 33mm; }
.req { font-size: 8.4pt; line-height: 1.32; margin: 0 0 1.6mm;
       border-top: .2mm solid #ccc; padding-top: 2mm; }
.foot { font-size: 6.3pt; color: #999; line-height: 1.35; margin: 0; }

.back { align-items: center; justify-content: center; text-align: center; }
.bmark { display: flex; gap: 2mm; opacity: .55; margin-bottom: 4mm; }
.bname { font-family: "Fraunces", Georgia, serif; font-size: 20pt;
         font-weight: 600; letter-spacing: .22em; }
.bsub { font-size: 7pt; letter-spacing: .22em; text-transform: uppercase;
        color: #999; margin-top: 1.5mm; }
"""

fronts = [card(k, n, p, t, r) for k, n, p, t, r in DECK]
backs = [back() for _ in DECK]

pages = ""
chunks = [fronts[i:i + 9] for i in range(0, len(fronts), 9)]
bchunks = [backs[i:i + 9] for i in range(0, len(backs), 9)]
for i, ch in enumerate(chunks):
    pages += "<div class='sheet'>" + "".join(ch) + "</div><div class='pagebreak'></div>"
    # backs mirrored left-right so they line up when printed duplex on long edge
    row = [ch_ for ch_ in bchunks[i]]
    mirrored = []
    for r in range(0, len(row), 3):
        mirrored += list(reversed(row[r:r + 3]))
    pages += "<div class='sheet'>" + "".join(mirrored) + "</div>"
    if i + 1 < len(chunks):
        pages += "<div class='pagebreak'></div>"

HTML = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Blink map objectives</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>{pages}</body></html>"""

out = pathlib.Path("Blink-objectives-bw.html" if BW else "Blink-objectives-colour.html")
out.write_text(HTML, encoding="utf-8")
print(f"{out}  {len(fronts)} cards + backs")
