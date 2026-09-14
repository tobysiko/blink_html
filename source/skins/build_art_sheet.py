# -*- coding: utf-8 -*-
"""A contact sheet of every tech illustration, four suits across, by age.

    python3 build_art_sheet.py   ->  art-sheet.html

Drawn at the size the card prints them (20 mm) on the suit's pale plate, so a
drawing that only works at screen size is caught here rather than on paper.
Undrawn ranks show the dashed placeholder, which makes the gaps countable.
"""
import json
import pathlib

import art
from marks import COLOUR

HERE = pathlib.Path(__file__).resolve().parent
SKIN = json.loads((HERE / "civ-ladder.json").read_text(encoding="utf-8"))
SUITS = ("plains", "forest", "ocean", "mountain")


def cell(suit, rank):
    c = COLOUR[suit]
    drawn = f"{suit}-{rank}" in art.TECH
    return (f'<div class="c{"" if drawn else " todo"}" style="--ink:{c["ink"]};'
            f'--pale:{c["pale"]};--strong:{c["strong"]}">'
            f'<div class="plate">{art.tech(suit, rank)}</div>'
            f'<div class="lab"><b>{rank}</b> {SKIN["cards"][suit][rank - 1]}</div>'
            f'</div>')


def age_block(a):
    lo, hi = (int(v) for v in SKIN["ages"][a]["ranks"].split("-"))
    rows = "".join(
        '<div class="row">' + "".join(cell(s, r) for s in SUITS) + "</div>"
        for r in range(lo, hi + 1))
    return (f'<section class="age" id="age{a}">'
            f'<h2><i>{SKIN["ages"][a]["numeral"]}</i> {SKIN["ages"][a]["name"]}'
            f'<em>ranks {lo}&ndash;{hi}</em></h2>'
            f'<div class="head">' + "".join(f'<span>{s}</span>' for s in SUITS)
            + f'</div>{rows}</section>')


CSS = """
*{box-sizing:border-box}
body{margin:0;background:#F3F1EA;color:#1A1C19;
  font-family:"IBM Plex Sans",-apple-system,sans-serif;}
.wrap{width:1180px;margin:0 auto;padding:24px 24px 60px}
h1{font-family:"Fraunces",Georgia,serif;font-size:30px;margin:14px 0 4px}
.sub{color:#63655E;margin:0 0 10px;font-size:14px}
.age{margin-top:26px;background:#FBFAF6;border:1px solid #D8D5CB;padding:14px 16px 18px}
h2{font-family:"Fraunces",Georgia,serif;font-size:20px;margin:0 0 10px;
  display:flex;align-items:baseline;gap:10px}
h2 i{font-style:normal;font-family:"IBM Plex Mono",monospace;font-size:13px;
  color:#8C8A82;letter-spacing:.1em}
h2 em{font-style:normal;font-family:"IBM Plex Mono",monospace;font-size:11px;
  color:#A5A29A;letter-spacing:.12em;text-transform:uppercase}
.head,.row{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.head span{font-family:"IBM Plex Mono",monospace;font-size:10.5px;
  letter-spacing:.16em;text-transform:uppercase;color:#A5A29A;padding-bottom:4px}
.row{margin-bottom:10px}
.c{display:flex;align-items:center;gap:10px;background:#fff;border:1px solid #E2DFD6;
  padding:6px 8px}
.c.todo{background:repeating-linear-gradient(45deg,#fff,#fff 6px,#F6F4EE 6px,#F6F4EE 12px)}
.plate{width:26mm;height:26mm;flex:none;background:var(--pale);
  display:flex;align-items:center;justify-content:center;border-radius:1.8mm}
.tech{width:20mm;height:20mm;fill:none;stroke:var(--ink);stroke-width:1.85;
  stroke-linecap:round;stroke-linejoin:round;color:var(--ink)}
.ghost{opacity:.3}
.lab{font-size:13px;line-height:1.25}
.lab b{font-family:"Fraunces",Georgia,serif;color:var(--strong);
  font-size:15px;margin-right:3px}
"""

drawn = sum(1 for s in SUITS for r in range(1, 21) if f"{s}-{r}" in art.TECH)
HTML = f"""<title>Eighty Technologies</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{CSS}</style>
<div class="wrap">
<h1>The Civilisation Ladder &mdash; every drawing</h1>
<p class="sub">{drawn} of 80 drawn, at print size on the suit plate.</p>
{"".join(age_block(a) for a in range(4))}
</div>
"""
(HERE / "art-sheet.html").write_text(HTML, encoding="utf-8")
print(f"art-sheet.html — {drawn}/80 drawn, {80 - drawn} to go")
