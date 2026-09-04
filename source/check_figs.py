# -*- coding: utf-8 -*-
"""Verify every figure: nothing clipped, nothing overflowing its column.

Run after build_figs.py. Catches the two failure modes that bit v0.18/v0.19:
  1. content drawn outside the viewBox (e.g. inside a <g transform="translate">
     that the auto-fit didn't account for) — silently clipped in the PDF;
  2. a figure whose scaled width exceeds the print column or its grid cell.
"""
import json, re, sys
from pathlib import Path
from figs import fig_bounds
from build_html import SCALE, COMPARE

# Anchored to this file rather than to the shell's working directory. The
# builders are always run from source/ by build_pdfs.sh, but the CHECKERS get
# run by hand from wherever somebody happens to be standing — and a checker
# that crashes on a FileNotFoundError instead of reporting on the figures is
# worse than no checker, because the exit code looks the same as a real fail.
HERE = Path(__file__).resolve().parent

FULL = 178 / 25.4 * 96          # A4 minus 16mm side margins, at 96px/in
GRID = (FULL - 26) / 2          # one cell of the two-column meld grid

F = json.load(open(HERE / "figs.json"))
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

# ---- and is it big enough to READ on paper? -------------------------------
# A figure that fits the column can still be illegible. Every figure is drawn
# at some viewBox width and printed across the A4 text block, so the scale is
# known exactly and so is the printed size of every piece of text in it.
#
# A4 is 210 mm and the rulebook's @page margins are 16 mm each side, so the
# text block is 178 mm. Body copy prints at 10.3 pt. SEVEN POINT is the floor
# here: below that a caption stops being something a player reads at a table
# and becomes something they decide not to bother with.
#
# Checked 4 Sep 2026 and three figures were under it — `table` at 5.9 pt,
# `board` at 6.2, `terrain` at 6.6 — which is the sort of thing that survives
# every other check in this folder and is only ever caught by looking.
TEXT_MM = 178.0
FLOOR_PT = 7.0
small = []
for k, svg in F.items():
    m = re.search(r'viewBox="([^"]+)"', svg)
    sizes = [float(x) for x in re.findall(r'font-size[:=]"?\s*([0-9.]+)', svg)]
    if not m or not sizes:
        continue
    vw = float(m.group(1).split()[2])
    pt = min(sizes) * (TEXT_MM / vw) * 72 / 25.4
    if pt < FLOOR_PT:
        small.append(f"{k}: smallest text prints at {pt:.1f} pt")
if small:
    print("TEXT TOO SMALL TO READ ON PAPER (floor is %.0f pt):" % FLOOR_PT)
    for line in small:
        print("  " + line)
    fails.extend(s.split(":")[0] for s in small)
    print()

if fails:
    print("FAIL:", ", ".join(sorted(set(fails)))); sys.exit(1)
print(f"all {len(F)} figures pass, none printing text under {FLOOR_PT:.0f} pt")
