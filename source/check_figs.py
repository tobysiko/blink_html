# -*- coding: utf-8 -*-
"""Verify every figure: nothing clipped, nothing overflowing its column.

Run after build_figs.py. Catches the two failure modes that bit v0.18/v0.19:
  1. content drawn outside the viewBox (e.g. inside a <g transform="translate">
     that the auto-fit didn't account for) — silently clipped in the PDF;
  2. a figure whose scaled width exceeds the print column or its grid cell.
"""
import json, re, sys
from figs import fig_bounds
from build_html import SCALE, COMPARE

FULL = 178 / 25.4 * 96          # A4 minus 16mm side margins, at 96px/in
GRID = (FULL - 26) / 2          # one cell of the two-column meld grid

F = json.load(open("figs.json"))
fails = []
print(f"{'figure':16}{'tier':>10}{'width':>8}{'limit':>8}   status")
for k, v in sorted(F.items()):
    m = re.search(r'viewBox="(-?[\d.]+) (-?[\d.]+) ([\d.]+) ([\d.]+)"', v)
    if not m:
        continue
    body = v[v.index('role="img">') + len('role="img">'):v.rindex('</svg>')]
    vx, vy, vw, vh = map(float, m.groups())
    problems = []

    bb = fig_bounds(body)
    if bb:
        x0, y0, x1, y1 = bb
        if x0 < vx - .5:        problems.append(f"clipped left {vx-x0:.0f}")
        if y0 < vy - .5:        problems.append(f"clipped top {vy-y0:.0f}")
        if x1 > vx + vw + .5:   problems.append(f"clipped right {x1-(vx+vw):.0f}")
        if y1 > vy + vh + .5:   problems.append(f"clipped bottom {y1-(vy+vh):.0f}")

    sc = SCALE.get(k, COMPARE)
    # v0.22: the two-column meld grid is gone with the old taxonomy, so every
    # figure is full width. GRID is kept only so the constant still documents
    # what a two-up cell was.
    limit = FULL
    w = vw * sc
    if k != "hero" and w > limit + 1:
        problems.append(f"overflows column by {w-limit:.0f}px")

    tier = {1.60: "detail", 1.22: "component"}.get(sc, "compare")
    print(f"{k:16}{tier:>10}{w:8.0f}{limit:8.0f}   {'ok' if not problems else '; '.join(problems)}")
    if problems:
        fails.append(k)

print()
if fails:
    print("FAIL:", ", ".join(fails)); sys.exit(1)
print(f"all {len(F)} figures pass")
