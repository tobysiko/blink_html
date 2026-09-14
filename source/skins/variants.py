# -*- coding: utf-8 -*-
"""Four treatments of the same card face.

The skeleton does not move: 16 mm of index, a 23.5 mm panel, a 9 mm band, a
23.5 mm panel, 16 mm of index; four corners; C, B, A. What changes is how much
ink the two panels carry, which is the one dial worth having on a print-and-play
card — it decides how the card reads across a table and what it costs to print.
"""

from urllib.parse import quote

import marks

SQ = 0.8660254


def _mix(a, b, t):
    a, b = a.lstrip("#"), b.lstrip("#")
    v = [round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t)
         for i in (0, 2, 4)]
    return "#%02X%02X%02X" % tuple(v)


def mid(suit):
    """Between the pale plate and the ink: enough colour to read across a
    table, still light enough to draw a line over."""
    c = marks.COLOUR[suit]
    return _mix(c["pale"], c["ink"], .30)


def weave(suit):
    """A hex tessellation at the tint of the suit, as a CSS background. The
    card's ground becomes the map it acts on."""
    col = _mix(marks.COLOUR[suit]["pale"], marks.COLOUR[suit]["ink"], .20)
    r, w, h = 4.0, 6.928, 12.0
    cells = [(3.464, 2), (0, 8), (6.928, 8), (3.464, 14), (0, -4), (6.928, -4)]
    body = "".join(
        f'<polygon points="{marks.hex_points(cx, cy, r)}"/>' for cx, cy in cells)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}"><g fill="none" stroke="{col}" '
           f'stroke-width=".38">{body}</g></svg>')
    return "url('data:image/svg+xml," + quote(svg, safe="") + "')"


def deep(suit):
    """The bleed ground, pulled back slightly from Full bleed's 30% so the
    lattice has somewhere to sit."""
    c = marks.COLOUR[suit]
    return _mix(c["pale"], c["ink"], .26)


def weave_light(suit):
    """On a mid ground the lattice has to go LIGHTER, not darker. A darker line
    adds weight exactly where the illustration is already losing contrast; a
    lighter one reads as weave in the paper and stays behind everything."""
    col = _mix(deep(suit), "#FFFFFF", .42)
    r, w, h = 4.0, 6.928, 12.0
    cells = [(3.464, 2), (0, 8), (6.928, 8), (3.464, 14), (0, -4), (6.928, -4)]
    body = "".join(
        f'<polygon points="{marks.hex_points(cx, cy, r)}"/>' for cx, cy in cells)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}"><g fill="none" stroke="{col}" '
           f'stroke-width=".5">{body}</g></svg>')
    return "url('data:image/svg+xml," + quote(svg, safe="") + "')"


def deepink(suit):
    """The illustration stroke, darkened for a tinted ground. This is the fix
    for the contrast loss Full bleed showed on its own — plains worst."""
    return _mix(marks.COLOUR[suit]["ink"], "#000000", .40)


def card_vars(suit):
    return (f'--mid:{mid(suit)};--weave:{weave(suit)};--deep:{deep(suit)};'
            f'--weavelight:{weave_light(suit)};--deepink:{deepink(suit)}')


TREATMENTS = [
    ("plate", "Plate",
     "Two pale panels on white &mdash; where the proof landed. Quiet, modern, "
     "and the illustration is unmistakably the loudest thing on the card. Least "
     "risk, least presence across a table."),
    ("keyline", "Keyline",
     "No fills at all: each panel is bounded by a fine rule in the suit&rsquo;s "
     "ink. The lightest possible print &mdash; a home printer barely notices it "
     "&mdash; and the most engraved-looking of the four. The cost is that suit "
     "colour now lives only in the corners and the line work."),
    ("bleed", "Full bleed",
     "The panels run edge to edge in a deeper tint, leaving the four corner "
     "zones as white bands. The strongest colour of the four and the easiest to "
     "read across a four-player table; also the most toner, and the least "
     "forgiving of a millimetre of trim error."),
    ("deep", "Deep weave",
     "Full bleed and Weave together, with the two corrections each one needed "
     "on its own: the lattice goes <em>lighter</em> than the ground rather than "
     "darker, so it reads as weave in the paper instead of adding weight, and "
     "the illustration stroke is darkened to hold against the tint. The most "
     "finished of the five &mdash; and the only one that needs bleed, trim and "
     "a second set of art values."),
    ("weave", "Weave",
     "A fine hex lattice at suit tint fills both panels &mdash; the card&rsquo;s "
     "ground becomes the map it acts on. Texture rather than weight, so it holds "
     "the illustration; watch that it does not fight the B mark, which is hexes "
     "too."),
]

CSS = """
/* ---- treatment: keyline --------------------------------------------------
   Rules instead of fills. The panel boundary is still exactly where it was. */
.v-keyline .plate, .v-keyline .fx{background:none; border-radius:0;
  border-top:.35mm solid var(--ink); border-bottom:.35mm solid var(--ink);}
.v-keyline .fxr + .fxr{border-top-color:rgba(25,23,19,.14);}
.v-keyline .fxr:last-child{border-top-color:rgba(25,23,19,.26);}

/* ---- treatment: full bleed ---------------------------------------------- */
.v-bleed .plate, .v-bleed .fx{left:0; right:0; border-radius:0;
  background:var(--mid);}
.v-bleed .fxr + .fxr{border-top-color:rgba(255,255,255,.26);}
.v-bleed .fxr:last-child{border-top-color:rgba(255,255,255,.5);}

/* ---- treatment: deep weave ----------------------------------------------
   Full bleed's ground with Weave's lattice on top, lighter than the ground, and
   a darker illustration stroke so the line art survives the tint. */
.v-deep .plate, .v-deep .fx{left:0; right:0; border-radius:0;
  background-color:var(--deep); background-image:var(--weavelight);
  background-size:3.3mm 5.72mm;}
.v-deep .plate .tech{stroke:var(--deepink); color:var(--deepink);}
.v-deep .fxr + .fxr{border-top-color:rgba(255,255,255,.30);}
.v-deep .fxr:last-child{border-top-color:rgba(255,255,255,.55);}

/* ---- treatment: weave --------------------------------------------------- */
.v-weave .plate, .v-weave .fx{background-color:#fff; background-image:var(--weave);
  background-size:3.3mm 5.72mm;}
"""
