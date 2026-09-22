# -*- coding: utf-8 -*-
"""Blink -- the player aid. One card each, four to a page.

WHAT IT IS FOR. The app tells you what you may do because it can only offer
legal things; at a table nobody does. Everything a turn contains is in the
rulebook, spread over four sections, and a player who has to look up "can I
still fortify?" has stopped playing. So: one card, in front of each player, with
the whole turn on it.

IT IS A FOLD-OVER, for the reason the perk tokens are. Duplex registration is
the thing print-and-play does worst, and a two-sided card whose faces are two
millimetres out looks broken. Both faces print on one side of the sheet, side by
side; fold backwards along the middle and the card is double thickness with the
turn on one face and the numbers on the other. Nothing needs rotating.

LANDSCAPE, 88x63mm -- a poker card turned on its side, so it belongs in the same
box as the deck, and four fit on one A4 page: one page is a whole table's worth.

WHAT IS ON IT. The front is the turn as a MENU, in the order you meet it: the
four things a card can be, then everything that is free. The back is every
number you would otherwise interrupt somebody to ask for. What is deliberately
NOT on it: any explanation. This is a reminder for a player who has been taught,
not a second rulebook -- the moment it starts teaching it stops being scannable,
and Your First Game already teaches.

    python3 build_aid.py           ->  Blink-player-aid.html
    python3 build_aid.py --bw      ->  Blink-player-aid-bw.html
"""
import pathlib
import sys

from version import VTAG

BW = "--bw" in sys.argv

# ---- palette, matching the player board and the perk tokens --------------
if BW:
    INK, SOFT, FAINT = "#000000", "#3A3A3A", "#9A9A9A"
    PAPER, PANEL, LINE = "#FFFFFF", "#F0F0F0", "#000000"
    GOLD, FOREST, OCEAN, STONE = "#000000", "#000000", "#000000", "#000000"
else:
    INK, SOFT, FAINT = "#2A2E2B", "#6B6F68", "#B9B4A8"
    PAPER, PANEL, LINE = "#FBFAF6", "#EFECE3", "#CDC7B8"
    GOLD, FOREST, OCEAN, STONE = "#C9992B", "#37704A", "#256A8C", "#8A837A"

# ---- geometry ------------------------------------------------------------
W, H = 88.0, 63.0                 # finished card, mm -- a poker card sideways
PER_PAGE = 4                      # 4 x 63mm = 252mm, inside an A4 text height

# ---- the turn, as the table meets it -------------------------------------
# THE TABLES LIVE IN aid_data.py, because the A4 pictorial sheet renders the
# same facts and two copies of them would drift. This file decides how they
# LOOK on a folded card; it does not decide what they say.
from aid_data import FREE, TIERS, card_uses, terrain      # noqa: E402

CARD_USES = card_uses(GOLD, FOREST, "#C0392B", STONE)
TERRAIN = terrain(GOLD, FOREST, OCEAN, STONE)

CSS = f"""
@page {{ size: A4; margin: 9mm 8mm; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: {PAPER}; color: {INK};
       font-family: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
       -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.sheet {{ width: {2 * W}mm; font-size: 0; }}

/* One aid = two faces side by side with the fold between them. */
.aid {{ display: block; width: {2 * W}mm; height: {H}mm; position: relative;
       border: .25mm dashed {FAINT}; }}
.face {{ position: absolute; top: 0; height: {H}mm; width: {W}mm;
        padding: 2.4mm 2.8mm 1.4mm; overflow: hidden; }}
.face.front {{ left: 0; }}
.face.back  {{ left: {W}mm; background: {PANEL}; }}
/* The fold, marked at both ends so it cannot be taken for a cut line. */
.fold {{ position: absolute; left: {W}mm; top: 0; height: {H}mm;
        border-left: .3mm dotted {SOFT}; }}
.fold::before, .fold::after {{ content: ""; position: absolute; left: -1.4mm;
        border-left: 1.4mm solid transparent; border-right: 1.4mm solid transparent; }}
.fold::before {{ top: 0; border-top: 1.8mm solid {SOFT}; }}
.fold::after {{ bottom: 0; border-bottom: 1.8mm solid {SOFT}; }}

.hd {{ font-size: 6.4pt; letter-spacing: .16em; font-weight: 600;
      text-transform: uppercase; color: {SOFT}; }}
.hd b {{ color: {INK}; }}
.rule {{ border-top: .35mm solid {INK}; margin: 1mm 0 1.4mm; }}
.lead {{ font-size: 5.4pt; letter-spacing: .12em; text-transform: uppercase;
        color: {SOFT}; margin: 0 0 1mm; }}
.use {{ display: flex; gap: 1.8mm; align-items: baseline; margin: 0 0 .95mm; }}
.use .k {{ font-size: 7.2pt; font-weight: 600; letter-spacing: .03em;
          width: 14mm; flex: none; }}
.use .d {{ font-size: 5.8pt; line-height: 1.25; color: {INK}; }}
.both {{ font-size: 5.4pt; line-height: 1.3; color: {INK};
        background: {PANEL}; border-radius: .8mm; padding: 1mm 1.4mm;
        margin: 1.2mm 0 0; }}
.both b {{ font-weight: 600; }}
.freebox {{ background: {PANEL}; border-radius: .8mm; padding: 1mm 1.3mm .3mm;
           margin: 1.2mm 0 0; }}
.freebox .lead {{ margin: 0 0 .9mm; }}
.free {{ display: flex; gap: 1.8mm; align-items: baseline; margin: 0 0 .7mm; }}
.free .k {{ font-size: 6pt; font-weight: 600; width: 14mm; flex: none;
           line-height: 1.1; }}
.free .k em {{ display: block; font-style: normal; font-size: 4.8pt;
              font-weight: 400; color: {SOFT}; letter-spacing: .02em; }}
.free .d {{ font-size: 5.5pt; line-height: 1.24; }}
table {{ border-collapse: collapse; width: 100%; font-size: 5.7pt; }}
th {{ font-weight: 600; font-size: 4.8pt; letter-spacing: .07em;
     text-transform: uppercase; color: {SOFT}; text-align: right;
     padding: 0 0 .6mm .8mm; }}
th.n, td.n {{ text-align: left; }}
td {{ padding: .5mm 0 .5mm .8mm; text-align: right; border-top: .2mm solid {LINE}; }}
td.n {{ font-weight: 600; }}
tr:nth-child(even) td {{ background: {PANEL}; }}
.note {{ font-size: 5.2pt; line-height: 1.3; color: {INK}; margin: .7mm 0 0;
        padding-top: .6mm; border-top: .2mm solid {LINE}; }}
/* the footer is absolutely placed, so the last note has to keep clear of it */
.note:last-of-type {{ margin-bottom: 2.6mm; }}
.note b {{ font-weight: 600; }}
.note.first {{ border-top: 0; padding-top: 0; }}
.ter {{ display: flex; flex-wrap: wrap; gap: .8mm 2.4mm; font-size: 5.2pt;
       margin: 1.2mm 0 0; }}
.ter span {{ white-space: nowrap; }}
.ter i {{ display: inline-block; width: 1.8mm; height: 1.8mm; border-radius: .3mm;
         margin-right: .7mm; }}
.foot {{ position: absolute; left: 2.8mm; right: 2.8mm; bottom: 1.6mm;
        font-size: 4.6pt; color: {FAINT}; display: flex;
        justify-content: space-between; }}
"""


def front():
    uses = "".join(
        f'<div class="use"><span class="k" style="color:{c}">{k}</span>'
        f'<span class="d">{d}</span></div>' for k, c, d in CARD_USES)
    free = "".join(
        f'<div class="free"><span class="k">{k}<em>{w}</em></span>'
        f'<span class="d">{d}</span></div>' for k, w, d in FREE)
    return f"""<div class="face front">
  <div class="hd"><b>Your turn</b> · each card of your meld does ONE of</div>
  <div class="rule"></div>
  {uses}
  <div class="both">Every card: <b>in reach</b> \u2014 a tile you hold or one beside it \u2014
    and its <b>suit matches the terrain</b>.</div>
  <p class="lead" style="margin-top:1.2mm">Free · no card · any order</p>
  {free}
</div>"""


def back():
    rows = "".join(
        f'<tr><td class="n">{n}</td><td>{u}</td><td>{m}</td>'
        f'<td>{c}</td><td>{w}</td></tr>'
        for n, u, m, c, w in TIERS)
    ter = "".join(f'<span><i style="background:{c}"></i>{n} {d}</span>'
                  for n, c, d in TERRAIN)
    return f"""<div class="face back">
  <div class="hd"><b>The numbers</b></div>
  <div class="rule"></div>
  <table>
    <tr><th class="n">Tier</th><th>Units</th><th>Meld</th>
        <th>Cap</th><th>Wall</th></tr>
    {rows}
  </table>
  <p class="note first">Read your top tier that still holds units, and nothing is
    cumulative. Growing costs you nothing.</p>
  <div class="ter">{ter}</div>
  <p class="note"><b>Round.</b> Melds face down · turn over together · Declare A, leader
    first · highest total wins · winner's die
    = meld size, and leads; others 2/3/4 · spend in that order. Matched the winner and
    lost: set a card aside, +1 gold. Last: +1 gold.</p>
  <p class="note"><b>Recycle.</b> Hand empty — at once, mid-turn. Take your discard
    back, draw to ten, carry on. <i>Modules only:</i> collect income, and arm ONE perk
    (from what your row reaches now; it runs till the next recycle even if you spend the
    card).</p>
  <p class="note"><b>Meld.</b> Any unbroken run; duplicates free, suits irrelevant.
    2-3-3-4-4 yes · 2-2-4-4 no (no 3).</p>
  <p class="note"><b>Duel.</b> Your spent card vs their hand card + the ground. Higher
    wins; level goes to the card matching the ground, else the defender. Clear the last
    unit and the tile is yours.</p>
  <p class="note"><b>End.</b> Last unit placed: finish the round, then one more. Score 1/unit · 1/row card + its centre rank (3+) ·
    your objectives.</p>
  <div class="foot"><span>Blink {VTAG}</span><span>deep-diversions.com/blink</span></div>
</div>"""


def main():
    aid = f'<div class="aid">{front()}<div class="fold"></div>{back()}</div>'
    sheet = "".join(aid for _ in range(PER_PAGE))
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Blink — player aid</title>
<style>{CSS}</style></head>
<body><div class="sheet">{sheet}</div></body></html>"""
    name = "Blink-player-aid-bw.html" if BW else "Blink-player-aid.html"
    # BESIDE THIS SCRIPT, not in whatever directory it was run from. Every
    # other builder here resolves its output from __file__; this one wrote to
    # the cwd, so running it from the repo root and running it from source/
    # produced two files of the same name in two places, and check_rules.py
    # reads the one in source/. A rebuild from the root therefore looked
    # successful, printed the right filename, and left the checked copy a day
    # stale - which is this project's signature failure with a third instance.
    out = pathlib.Path(__file__).resolve().parent / name
    out.write_text(html, encoding="utf-8")
    print(f"  {name}  ({PER_PAGE} aids, {W:.0f}x{H:.0f}mm folded)")


if __name__ == "__main__":
    main()
