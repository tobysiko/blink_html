# -*- coding: utf-8 -*-
"""Figures for the advanced map-objective patterns.
Each draws the terrain shape being counted, with a unit on each required tile.
Reuses hex/prism helpers from figs.py.
"""
from figs import axial, prism, unit, label, svg, SQ, TER, R

PF = {}


def pattern_panel(cells, anchor_cells=None, w_pad=28):
    """cells: list of (col,row,terrain). anchor_cells: indices drawn as 'reusable'."""
    anchor_cells = anchor_cells or set()
    xs = [axial(c, r)[0] for c, r, _ in cells]
    ys = [axial(c, r)[1] for c, r, _ in cells]
    max_h = max(TER[t]["h"] for _, _, t in cells)
    ox = w_pad / 2 - min(xs) + SQ
    oy = 26 + 12 - min(ys)
    b = f'<g transform="translate({ox:.1f},{oy:.1f})">'
    for i, (c, r, ter) in enumerate(cells):
        x, y = axial(c, r)
        b += prism(x, y, ter)
        b += unit(x, y, "you", 1)
    b += '</g>'
    # explicit viewBox with generous padding so tiles never touch the edge
    PAD = 16
    left = ox + (min(xs) - SQ) - PAD
    right = ox + (max(xs) + SQ) + PAD
    top = oy + (min(ys) - R) - PAD
    bot = oy + (max(ys) + R + max_h) + PAD
    vb = f"{left:.0f} {top:.0f} {right-left:.0f} {bot-top:.0f}"
    return svg(0, 0, b, vb=vb)


# ---- the deck ----------------------------------------------------------
# clusters & lines use offset-hex coords (col,row). row%2 shifts right.

# Six mixed-terrain chains. Bent where the pattern allows a bend, straight
# where the two ends share a terrain, so the art reads as the shape it asks for.
PF["highland_rivers"] = pattern_panel(
    [(0, 0, "mountain"), (1, 0, "forest"), (1, 1, "ocean")])

PF["river_delta"] = pattern_panel(
    [(0, 0, "ocean"), (1, 0, "plains"), (1, 1, "forest")])

PF["coastal_chain"] = pattern_panel(
    [(0, 0, "plains"), (1, 0, "ocean"), (2, 0, "plains")])

PF["mountain_pass"] = pattern_panel(
    [(0, 0, "plains"), (1, 0, "mountain"), (2, 0, "plains")])

PF["foothills"] = pattern_panel(
    [(0, 0, "mountain"), (1, 0, "forest"), (1, 1, "plains")])

PF["fjord"] = pattern_panel(
    [(0, 0, "mountain"), (1, 0, "ocean"), (1, 1, "mountain")])

PF["mountain_lookout"] = pattern_panel(
    [(0, 0, "ocean"), (1, 0, "mountain"), (2, 0, "ocean")])

PF["sheltered_water"] = pattern_panel(
    [(0, 0, "forest"), (1, 0, "ocean"), (2, 0, "forest")])

PF["timberline"] = pattern_panel(
    [(0, 0, "forest"), (1, 0, "mountain"), (1, 1, "forest")])

PF["clearing"] = pattern_panel(
    [(0, 0, "forest"), (1, 0, "plains"), (1, 1, "forest")])

PF["riverbank"] = pattern_panel(
    [(0, 0, "plains"), (1, 0, "forest"), (1, 1, "ocean")])

PF["watershed"] = pattern_panel(
    [(0, 0, "mountain"), (1, 0, "plains"), (1, 1, "ocean")])
