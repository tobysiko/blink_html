# -*- coding: utf-8 -*-
"""Blink — the player aid, in the civ-ladder skin. Icon-led.

Same object as build_aid.py: a fold-over, 88 x 63 mm finished, both faces
printed side by side on one side of the sheet, four aids to an A4 page. Fold
backwards along the middle and the card is double thickness with the turn on
one face and the numbers on the other. Nothing needs rotating, and duplex
registration — the thing print-and-play does worst — never comes into it.

WHAT IS DIFFERENT. The deck no longer prints A/B/C as letters. It prints three
marks, in the order C, B, A down the card, so that a card turned around in the
victory row shows A first. That was the right call for the card and it puts a
debt on the aid: **the aid is now the only place the three marks are named.**
So the marks legend is the back's headline, not a footnote, and every mark on it
is imported from marks.py rather than redrawn — the aid and the deck cannot
drift apart, because they are the same code.

LEAN. The tier table has no food and no ascension columns, matching
board_concept.py. That is a rules decision that has not been taken: the rulebook
and check_rules.py still describe the full economy. This aid is a concept piece
and belongs with the concept board, not in a box with the printed rules.

    python3 build_skin_aid.py         ->  Blink-skin-aid.html
"""
import pathlib
from urllib.parse import quote

import marks
from marks import COLOUR, CY, _colony, _hex, _rampart, _unit, hex_points

HERE = pathlib.Path(__file__).resolve().parent

INK, SOFT, FAINT = "#222A26", "#666A63", "#A8A49A"
PAPER, PANEL, LINE = "#FCFBF7", "#F0EDE4", "#D6D1C4"
GOLD, GOLDd, RED = "#C9992B", "#8A6A18", "#B4432F"

W, H, PER_PAGE = 88.0, 63.0, 4

# tier, units, meld, moves, cap, wall
TIERS = [("Tribe", 2, 2, 1, 12, 10), ("Settlement", 3, 3, 2, 14, 12),
         ("Kingdom", 5, 4, 3, 16, 14), ("Empire", 5, 5, 4, 18, 16),
         ("Civilization", 5, 6, 5, 20, 18)]

TERRAIN = [("plains", 3, 0), ("forest", 2, 1), ("ocean", 1, 0), ("mountain", 1, 2)]

GLYPH = {
    "mountain": '<path d="M2 20 L9 6.5 L13 13 L15.5 9.5 L22 20 Z" fill="#fff"/>',
    "forest": ('<path d="M12 2.6 L18.2 12 L14.8 12 L19.6 19 L4.4 19 L9.2 12'
               ' L5.8 12 Z" fill="#fff"/>'
               '<rect x="11" y="18" width="2" height="3.6" fill="#fff"/>'),
    "plains": ('<path d="M2.6 19.6 h18.8" stroke="#fff" stroke-width="1.8"'
               ' fill="none" stroke-linecap="round"/>'
               '<path d="M6 19.6 q0 -6 2.4 -8 M11.2 19.6 q-.6 -7.4 1.6 -10'
               ' M16.6 19.6 q0 -6 2.2 -7.6" stroke="#fff" stroke-width="1.6"'
               ' fill="none" stroke-linecap="round"/>'),
    "ocean": ('<path d="M2.4 8 q3 -3 6 0 t6 0 t5.4 0 M2.4 13.8 q3 -3 6 0 t6 0 t5.4 0'
              ' M2.4 19.6 q3 -3 6 0 t6 0 t5.4 0" fill="none" stroke="#fff"'
              ' stroke-width="1.8" stroke-linecap="round"/>'),
}


def lattice(col="#DFDACB", op=".85"):
    r, w, h = 4.0, 6.928, 12.0
    cells = [(3.464, 2), (0, 8), (6.928, 8), (3.464, 14), (0, -4), (6.928, -4)]
    body = "".join(f'<polygon points="{hex_points(cx, cy, r)}"/>' for cx, cy in cells)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}"><g fill="none" stroke="{col}" '
           f'stroke-width=".55" opacity="{op}">{body}</g></svg>')
    return "url('data:image/svg+xml," + quote(svg, safe="") + "')"


def chip(suit, r=9):
    ink = COLOUR[suit]["ink"]
    s = r * 1.24
    return (f'<svg class="chip" viewBox="0 0 {2*r+2} {2*r+2}">'
            f'<polygon points="{hex_points(r+1, r+1, r)}" fill="{ink}"/>'
            f'<svg x="{r+1-s/2:.1f}" y="{r+1-s/2:.1f}" width="{s:.1f}" '
            f'height="{s:.1f}" viewBox="0 0 24 24">{GLYPH[suit]}</svg></svg>')


def ic(body, w=24, cls="ic"):
    return f'<svg class="{cls}" viewBox="0 0 {w} 22">{body}</svg>'


def unit(cx, cy, ink, r=4.2):
    """marks._unit is fixed at r=3, which is right on a card where the disc sits
    beside a hex. In a legend the disc IS the subject, so it gets its own size."""
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{ink}" '
            f'stroke="#fff" stroke-width="1.1"/>')


def coin(cx, cy=11, r=4.5, ink=GOLDd):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#EFD489" stroke="{ink}" '
            f'stroke-width="1.1"/><circle cx="{cx}" cy="{cy}" r="{r-1.7}" '
            f'fill="none" stroke="{ink}" stroke-width=".6" opacity=".55"/>')


# ---- the four things a card can be ---------------------------------------
def i_settle():
    c = COLOUR["plains"]
    return ic(_hex(11, CY, c["ink"], c["pale"]) + unit(11, CY, c["ink"]), 22)


def i_explore():
    c = COLOUR["ocean"]
    return ic(f'<circle cx="4" cy="6" r="2" fill="{SOFT}"/>'
              f'<circle cx="4" cy="16" r="2" fill="{SOFT}"/>'
              f'<path d="M6 6.5L13 10M6 15.5L13 12" stroke="{SOFT}" '
              f'stroke-width="1.1" stroke-dasharray="1.2 1.8" fill="none"/>'
              + _hex(23, CY, c["ink"], c["pale"]), 34)


def i_attack():
    c = COLOUR["mountain"]
    return ic(unit(7, CY, c["ink"], 4.6)
              + f'<path d="M14 5l6 12M20 5l-6 12" stroke="{RED}" '
                f'stroke-width="1.8" stroke-linecap="round" fill="none"/>'
              + f'<rect x="24" y="1" width="11" height="20" rx="1.8" fill="none" '
                f'stroke="{INK}" stroke-width="1.4"/>', 37)


def i_cash():
    return ic(coin(6), 13)


def i_move(n=3):
    p = "".join(f'<path d="M{3+i*6} 5l5 6-5 6"/>' for i in range(n))
    return ic(f'<g fill="none" stroke="{INK}" stroke-width="1.7" '
              f'stroke-linecap="round" stroke-linejoin="round">{p}</g>', 3+n*6+4)


def i_water():
    c = COLOUR["ocean"]
    return ic(f'<path d="M1 16q3-3 6 0t6 0" fill="none" stroke="{c["ink"]}" '
              f'stroke-width="1.6" stroke-linecap="round"/>'
              + marks._hex_any(24, CY, r=7.4), 34)


def i_research():
    return ic(f'<rect x="1" y="4" width="11" height="17" rx="1.6" fill="none" '
              f'stroke="{INK}" stroke-width="1.4"/>'
              f'<path d="M20 20V4M15.5 8.5L20 4l4.5 4.5" fill="none" '
              f'stroke="{INK}" stroke-width="1.8" stroke-linecap="round" '
              f'stroke-linejoin="round"/>', 27)


def i_fortify():
    c = COLOUR["mountain"]
    return ic(coin(5.5, 11, 4)
              + _rampart(23, CY, c["ink"], 7.4)
              + _hex(23, CY, c["ink"], c["pale"], 7.4)
              + _unit(23, CY, c["ink"]), 35)


def i_gold():
    return ic(coin(5.5) + coin(28.5)
              + f'<path d="M12 8h10M22 8l-2.5-2M22 8l-2.5 2'
                f'M22 14H12M12 14l2.5-2M12 14l2.5 2" fill="none" stroke="{SOFT}" '
                f'stroke-width="1.2" stroke-linecap="round" '
                f'stroke-linejoin="round"/>', 35)


def i_colony():
    c = COLOUR["forest"]
    return ic(f'<rect x="1" y="2" width="11" height="18" rx="1.6" fill="none" '
              f'stroke="{INK}" stroke-width="1.4"/>'
              f'<path d="M14 11h4" stroke="{SOFT}" stroke-width="1.2"/>'
              + _colony(28, c["ink"], c["pale"]), 38)


CARD_USES = [
    ("SETTLE", i_settle(), "a unit from your top tier"),
    ("EXPLORE", i_explore(), "a new tile &middot; must touch <b>two</b> &middot; "
     "rank 10 or under pays 1"),
    ("ATTACK", i_attack(), "your rank vs their card <b>+ the ground</b>"),
    ("CASH", i_cash(), "one gold"),
]

FREE = [
    ("MOVE", i_move(), "your tier &middot; land across your own, sea across empty ocean"),
    ("WATER", i_water(), "first sea move: one free tile, <b>any</b> terrain, anywhere"),
    ("RESEARCH", i_research(), "twice &middot; 1 then 2 &middot; draw high, retire low"),
    ("FORTIFY", i_fortify(), "1 gold &middot; it defends at your <b>wall</b>"),
    ("GOLD", i_gold(), "free &middot; shift coins between reserve and walls"),
    ("COLONY", i_colony(), "one a turn &middot; spend a victory card on its <b>B</b>"),
]

MARKS = [
    ("A", marks.mark_a("#3E4540", True), "card phase",
     "add this card&rsquo;s rank to your meld total. <b>=</b> also takes ties."),
    ("B", marks.mark_b(1, "forest"), "map phase",
     "found a colony &mdash; and how far out the band lets you reach."),
    ("C", marks.mark_c(3, GOLDd), "map phase",
     "take that many gold. count the coins."),
]

PIECES = [
    ("a tile", f'<svg class="pc" viewBox="0 0 17 19">'
     f'{_hex(8.5, 9.5, "#6B6660", "#EDEAE3", 8)}</svg>'),
    ("a unit", f'<svg class="pc" viewBox="0 0 11 11">'
     f'{unit(5.5, 5.5, "#3C3833", 4.6)}</svg>'),
    ("fortified", f'<svg class="pc" viewBox="0 0 19 21">'
     f'{_rampart(9.5, 10.5, "#6B6660", 7.6)}'
     f'{_hex(9.5, 10.5, "#6B6660", "#EDEAE3", 7.6)}</svg>'),
    ("reach", f'<svg class="pc" viewBox="0 0 18 8">'
     f'<path d="M2 4h14" stroke="#6B6660" stroke-width="1.5" fill="none" '
     f'stroke-linecap="round" stroke-dasharray="1.3 2.8"/>'
     f'<circle cx="3.4" cy="4" r="2" fill="#6B6660"/>'
     f'<circle cx="9" cy="4" r="2" fill="#6B6660"/></svg>'),
    ("gold", f'<svg class="pc" viewBox="0 0 11 11">{coin(5.5, 5.5, 4.6)}</svg>'),
    ("a card", f'<svg class="pc" viewBox="0 0 14 20">'
     f'<rect x="1" y="1" width="12" height="18" rx="1.8" fill="none" '
     f'stroke="#3C3833" stroke-width="1.6"/></svg>'),
]


def front():
    uses = "".join(
        f'<div class="r"><span class="k">{k}</span>{icon}'
        f'<span class="d">{d}</span></div>' for k, icon, d in CARD_USES)
    free = "".join(
        f'<div class="r"><span class="k">{k}</span>{icon}'
        f'<span class="d">{d}</span></div>' for k, icon, d in FREE)
    return f'''<div class="face">
  <div class="hd"><b>BLINK</b><span>your turn</span><i>lean</i></div>
  <div class="sec"><span class="lbl">a card does one of four things</span>{uses}</div>
  <div class="sec last"><span class="lbl">and these are always free</span>{free}</div>
</div>'''


def back():
    rows = "".join(
        f'<tr><td class="n">{n}</td><td>{u}</td><td>{m}</td><td>{mv}</td>'
        f'<td class="b">{c}</td><td class="b">{w}</td></tr>'
        for n, u, m, mv, c, w in TIERS)
    ter = "".join(
        f'<span class="t">{chip(s)}<i>{h}</i><em>{"+" + str(d) if d else "&middot;"}</em>'
        f'</span>' for s, h, d in TERRAIN)
    mk = "".join(
        f'<div class="m"><span class="ml">{L}</span>{svg}'
        f'<span class="mp">{ph}</span><span class="md">{d}</span></div>'
        for L, svg, ph, d in MARKS)
    pc = "".join(f'<span class="p">{svg}<i>{name}</i></span>' for name, svg in PIECES)
    return f'''<div class="face">
  <div class="hd"><b>THE MARKS</b><span>cards print C &middot; B &middot; A downward</span></div>
  <div class="marks">{mk}</div>
  <div class="pieces">{pc}</div>
  <table>
    <tr><th class="n">tier</th><th>units</th><th>meld</th><th>moves</th>
        <th>buy</th><th>wall</th></tr>
    {rows}
  </table>
  <div class="ter">{ter}<span class="tk">holds &middot; defends</span></div>
  <p class="note"><b>meld</b> any unbroken run; duplicates free, suits irrelevant.
     &nbsp;<b>duel</b> higher wins; level goes to the ground-matching card,
     else the defender.</p>
</div>'''


CSS = f"""
@page {{ size: A4; margin: 9mm 8mm; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:#fff; -webkit-print-color-adjust:exact;
        print-color-adjust:exact;
        font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif; }}
.sheet {{ width:{2*W}mm; font-size:0; }}
.aid {{ display:flex; width:{2*W}mm; height:{H}mm;
        border:.25mm dashed {FAINT}; }}
.fold {{ width:0; border-left:.25mm dotted {FAINT}; }}
.face {{ width:{W}mm; height:{H}mm; padding:2.4mm 3mm 1.8mm; background:{PAPER};
         background-image:{lattice()}; background-size:3.3mm 5.72mm;
         color:{INK}; font-size:0; position:relative; overflow:hidden; }}

.hd {{ display:flex; align-items:baseline; gap:2mm; border-bottom:.35mm solid {INK};
       padding-bottom:.9mm; margin-bottom:1.4mm; }}
.hd b {{ font-family:"Fraunces",Georgia,serif; font-size:8pt; letter-spacing:.06em; }}
.hd span {{ font-size:5.4pt; color:{SOFT}; font-style:italic; }}
.hd i {{ margin-left:auto; font-family:"IBM Plex Mono",monospace; font-size:4.4pt;
         letter-spacing:.16em; text-transform:uppercase; color:{FAINT};
         font-style:normal; }}

.lbl {{ display:block; margin-top:0; font-family:"IBM Plex Mono",monospace; font-size:4.3pt;
        letter-spacing:.14em; text-transform:uppercase; color:{FAINT};
        margin:0 0 .8mm; }}
.sec {{ margin-bottom:1.2mm; }}
.sec.last {{ margin-bottom:0; }}
.r {{ display:flex; align-items:center; gap:1.4mm; padding:.22mm 0; }}
.k {{ font-family:"IBM Plex Mono",monospace; font-size:5pt; font-weight:600;
      letter-spacing:.07em; width:13.5mm; flex:none; }}
.ic {{ height:4.1mm; width:auto; flex:none; }}
.d {{ font-size:5pt; line-height:1.15; color:{SOFT}; }}
.d b {{ color:{INK}; font-weight:600; }}

.marks {{ border:.3mm solid {LINE}; background:rgba(255,255,255,.72);
          padding:.8mm 1.3mm; margin-bottom:1mm; }}
.m {{ display:flex; align-items:center; gap:1.4mm; padding:.34mm 0; }}
.m + .m {{ border-top:.2mm solid {LINE}; }}
.ml {{ font-family:"Fraunces",Georgia,serif; font-size:8pt; font-weight:600;
       width:4mm; flex:none; }}
.mk {{ height:5.1mm; width:auto; flex:none; }}
.mp {{ font-family:"IBM Plex Mono",monospace; font-size:4.2pt; color:{FAINT};
       letter-spacing:.1em; text-transform:uppercase; width:12mm; flex:none; }}
.md {{ font-size:4.8pt; line-height:1.15; color:{SOFT}; }}
.md b {{ color:{INK}; }}

.pieces {{ display:flex; gap:2mm; align-items:center; margin-bottom:.9mm;
           flex-wrap:nowrap; }}
.p {{ display:flex; align-items:center; gap:.5mm; }}
.pc {{ height:4.1mm; width:auto; }}
.p i {{ font-family:"IBM Plex Mono",monospace; font-size:4.1pt; color:{SOFT};
        font-style:normal; }}

table {{ width:100%; border-collapse:collapse; margin-bottom:.8mm; }}
th, td {{ font-size:4.7pt; text-align:center; padding:.18mm 0; }}
th {{ font-family:"IBM Plex Mono",monospace; font-size:4pt; color:{FAINT};
      letter-spacing:.08em; text-transform:uppercase;
      border-bottom:.25mm solid {LINE}; }}
td.n, th.n {{ text-align:left; }}
td.n {{ font-weight:600; }}
td.b {{ font-family:"Fraunces",Georgia,serif; font-size:5.6pt; font-weight:600; }}
tr + tr td {{ border-top:.18mm solid {PANEL}; }}

.ter {{ display:flex; align-items:center; gap:1.4mm; margin-bottom:.7mm; }}
.t {{ display:flex; align-items:center; gap:.5mm; }}
.chip {{ height:3.6mm; width:auto; }}
.t i {{ font-size:5pt; font-style:normal; font-weight:600; }}
.t em {{ font-size:4.6pt; font-style:normal; color:{SOFT}; }}
.tk {{ margin-left:auto; font-family:"IBM Plex Mono",monospace; font-size:4pt;
       color:{FAINT}; letter-spacing:.08em; }}

.note {{ margin:0; font-size:4.35pt; line-height:1.2; color:{SOFT}; }}
.note b {{ font-family:"IBM Plex Mono",monospace; font-size:4.2pt; color:{INK};
           letter-spacing:.08em; text-transform:uppercase; }}
"""

HTML = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Blink — player aid, civ-ladder</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{CSS}</style></head>
<body><div class="sheet">
{"".join(f'<div class="aid">{front()}<div class="fold"></div>{back()}</div>' for _ in range(PER_PAGE))}
</div></body></html>
"""

AID = f'<div class="aid">{front()}<div class="fold"></div>{back()}</div>'

if __name__ == "__main__":
    out = HERE / "Blink-skin-aid.html"
    out.write_text(HTML, encoding="utf-8")
    print(f"{out}  {PER_PAGE} aids, {W:.0f}x{H:.0f}mm folded")
