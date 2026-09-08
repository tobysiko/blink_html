# -*- coding: utf-8 -*-
"""One card face, and the CSS that draws it.

Shared by the proof sheet (build_skin.py) and the print-and-play deck
(build_skin_deck.py) so a card can never look one way on screen and another way
on paper — the same failure the rest of this repo generates its documents to
avoid.

Geometry, measured down a 63 x 88 mm card:

    0.0 – 16.0   corner index          (two corners)
   16.0 – 39.5   illustration panel
   39.5 – 48.5   name and age pips
   48.5 – 72.0   effects panel
   72.0 – 88.0   corner index          (two corners, rotated)

16↔72 and 39.5↔48.5 are mirror pairs about the 44 mm centre line, so a half turn
maps every box onto its opposite number.
"""

import art
import marks
from marks import COLOUR

SUITS = ("plains", "forest", "ocean", "mountain")
GOLD = (2, 3, 4, 5)

# Terrain glyphs, lifted verbatim from source/cardstock.py so the skin cannot
# invent a different suit shape from the one the rest of the game prints.
GLYPH = {
    "mountain": ('<path d="M2 20 L9 6.5 L13 13 L15.5 9.5 L22 20 Z" fill="{ink}"/>'
                 '<path d="M9 6.5 L6.2 11.9 L9 10.7 L11.3 12.1 Z" fill="{page}"/>'),
    "forest":   ('<path d="M12 2.6 L18.2 12 L14.8 12 L19.6 19 L4.4 19 L9.2 12'
                 ' L5.8 12 Z" fill="{ink}"/>'
                 '<rect x="11" y="18" width="2" height="3.6" fill="{ink}"/>'),
    "plains":   ('<path d="M2.6 19.6 h18.8" stroke="{ink}" stroke-width="1.8"'
                 ' fill="none" stroke-linecap="round"/>'
                 '<path d="M6 19.6 q0 -6 2.4 -8 M11.2 19.6 q-.6 -7.4 1.6 -10'
                 ' M16.6 19.6 q0 -6 2.2 -7.6" stroke="{ink}" stroke-width="1.6"'
                 ' fill="none" stroke-linecap="round"/>'),
    "ocean":    ('<path d="M2.4 8 q3 -3 6 0 t6 0 t5.4 0 M2.4 13.8 q3 -3 6 0 t6 0 t5.4 0'
                 ' M2.4 19.6 q3 -3 6 0 t6 0 t5.4 0" fill="none" stroke="{ink}"'
                 ' stroke-width="1.8" stroke-linecap="round"/>'),
}


def glyph(suit, ink, page="#fff"):
    return (f'<svg class="gl" viewBox="0 0 24 24" aria-hidden="true">'
            f'{GLYPH[suit].format(ink=ink, page=page)}</svg>')


def chip(suit):
    """The corner suit mark: a solid pointy-top hex in the suit colour with the
    terrain glyph knocked out of it. Same shape as the tiles on the table, so
    the corner says terrain, not just colour."""
    ink = COLOUR[suit]["ink"]
    return (f'<svg class="chip" viewBox="0 0 28 32" aria-hidden="true">'
            f'<polygon points="{marks.hex_points(14, 16, 15)}" fill="{ink}"/>'
            f'<svg x="5.5" y="6" width="17" height="17" viewBox="0 0 24 24">'
            f'{GLYPH[suit].format(ink="#fff", page=ink)}</svg></svg>')


def age_pips(n, colour):
    """The age as pips rather than a numeral. Latin text rotated 180° reads as a
    typo, not as symmetry — a row of diamonds reads the same either way up, and
    it echoes the coins on effect C."""
    step, w = 7.0, (n - 1) * 7.0 + 6.0
    body = "".join(
        f'<path d="M{3 + i * step} 2.4 L{5.6 + i * step} 5 L{3 + i * step} 7.6 '
        f'L{0.4 + i * step} 5 Z" fill="{colour}"/>' for i in range(n))
    return (f'<svg class="pips" viewBox="0 0 {w:.1f} 10" aria-hidden="true">'
            f'{body}</svg>')


def card(suit, rank, skin):
    band = (rank - 1) // 5
    ink, pale = COLOUR[suit]["ink"], COLOUR[suit]["pale"]
    name = skin["cards"][suit][rank - 1]
    idx = f'<span class="rk">{rank}</span>{chip(suit)}'
    pips = age_pips(band + 1, COLOUR[suit]["strong"])
    # Printed C, B, A from the top. A card turned around in the victory row —
    # which is where its effects are spent — then shows A first, and A is the
    # one that decides a trick.
    fx = "".join(f'<div class="fxr">{mk}</div>' for mk in (
        marks.mark_c(GOLD[band], ink),
        marks.mark_b(band, suit),
        marks.mark_a(ink, band in (1, 3))))
    return f"""
<div class="card" style="--ink:{ink};--pale:{pale};--strong:{COLOUR[suit]["strong"]}">
  <span class="idx idx-tl">{idx}</span>
  <span class="idx idx-tr">{idx}</span>
  <span class="idx idx-bl">{idx}</span>
  <span class="idx idx-br">{idx}</span>
  <div class="plate">{art.tech(suit, rank)}</div>
  <div class="band">{pips}<span class="nm">{name}</span>{pips}</div>
  <div class="fx">{fx}</div>
</div>"""


CARD_CSS = """
.card{position:relative; width:63mm; height:88mm; background:#fff;
  overflow:hidden; color:#191713;}
.flip{transform:rotate(180deg);}

.idx{position:absolute; display:flex; flex-direction:column; align-items:center;
  line-height:1; z-index:2;}
.idx-tl{top:3.4mm; left:4.3mm;}
.idx-tr{top:3.4mm; right:4.3mm;}
.idx-bl{bottom:3.4mm; left:4.3mm; transform:rotate(180deg);}
.idx-br{bottom:3.4mm; right:4.3mm; transform:rotate(180deg);}
.idx .rk{font-family:"Fraunces",Georgia,serif; font-weight:600; font-size:16.5pt;
  line-height:.8; color:var(--strong);}
.idx .chip{width:5mm; height:5.72mm; margin-top:1.1mm; display:block;}

.plate,.fx{position:absolute; left:4.5mm; right:4.5mm; height:23.5mm;
  border-radius:1.8mm; background:var(--pale);}
.plate{top:16mm; display:flex; align-items:center; justify-content:center;}
.plate .tech{width:20mm; height:20mm; fill:none; stroke:var(--ink);
  stroke-width:1.85; stroke-linecap:round; stroke-linejoin:round;}
.plate .ghost{opacity:.3;}

.band{position:absolute; left:4.5mm; right:4.5mm; top:39.5mm; height:9mm;
  display:flex; align-items:center; justify-content:center; gap:2.8mm;
  text-align:center;}
.nm{font-family:"Fraunces",Georgia,serif; font-weight:600; font-size:11pt;
  line-height:1.02; color:#17150F;}
.pips{height:2.1mm; width:auto; display:block; flex:none;}

/* No A/B/C letters on the face. They are text, they cannot be read upside-down,
   and the three marks are distinct enough to carry themselves — the aid names
   them. Shape carries the phase instead: hexes act on the map, discs are coins,
   and A's badge is a little card. */
.fx{top:48.5mm; display:flex; flex-direction:column;}
.fxr{flex:1; display:flex; align-items:center; justify-content:center;}
.fxr + .fxr{border-top:.2mm solid rgba(25,23,19,.10);}
/* C and B are both map phase; A is the card phase. The firmer rule marks that
   seam. It travels with the rows, so a card turned around still shows it
   between A and B. */
.fxr:last-child{border-top:.32mm solid rgba(25,23,19,.20);}
.mk{height:6.8mm; width:auto; display:block;}
"""
