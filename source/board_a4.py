# -*- coding: utf-8 -*-
"""Blink player board, print-exact on A4 landscape.
All coordinates are millimetres; the SVG declares width/height in mm so the
PDF prints 1:1. Unit slots are 15 mm; feeding coin slots sit beside each band.
"""

from version import VTAG

# ---- page ----------------------------------------------------------------
PW, PH = 297.0, 210.0            # A4 landscape, mm
M = 14.0                         # outer margin

# ---- palette (muted, printer-friendly) ----------------------------------
INK   = "#2A2E2B"
SOFT  = "#6B6F68"
FAINT = "#B9B4A8"
PAPER = "#FBFAF6"
PANEL = "#EFECE3"
RED   = "#C0392B"
REDdk = "#7B2018"
GOLD  = "#C9992B"
GOLDl = "#EBD9A6"
GOLDd = "#8A6A18"                # readable gold for small text
LINE  = "#CDC7B8"

# ---- unit slot geometry --------------------------------------------------
D = 13.0                         # unit diameter, mm (was 15; five tiers need the room)
R = D / 2
GAP = 4.0                        # gap between unit slots
CD = 9.0                         # coin slot diameter
CR = CD / 2

BANDS = [
    # (label, meld_limit, n_units, feed_coins, free_moves, ascension, rank_cap)
    # Units are 2/3/5/5/5 as of v0.23 — still twenty, redistributed. The v0.22
    # board was 2/4/6/4/4 and is kept as a layout option in the app.
    ("Tribe",        2, 2, 0, 1, 0, "11"),
    ("Settlement",   3, 3, 1, 2, 1, "13"),
    ("Kingdom",      4, 5, 2, 3, 2, "15"),
    ("Empire",       5, 5, 3, 4, 3, "17"),
    ("Civilization", 6, 5, 4, 5, 4, "20"),
]


def T(x, y, s, size=4.2, anchor="middle", col=INK, weight="400", mono=False,
      spacing="0", style=""):
    fam = "IBM Plex Mono" if mono else "IBM Plex Sans"
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="{fam}" '
            f'font-size="{size}" fill="{col}" text-anchor="{anchor}" '
            f'font-weight="{weight}" letter-spacing="{spacing}" '
            f'style="{style}">{s}</text>')


def unit_slot(x, y, filled=False):
    if filled:
        return (f'<circle cx="{x:.2f}" cy="{y+1:.2f}" r="{R:.2f}" fill="{REDdk}"/>'
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{R:.2f}" fill="{RED}" '
                f'stroke="{REDdk}" stroke-width="0.5"/>')
    return (f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{R:.2f}" fill="none" '
            f'stroke="{FAINT}" stroke-width="0.6" stroke-dasharray="1.6 1.6"/>')


def coin_slot(x, y):
    return (f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{CR:.2f}" fill="{PAPER}" '
            f'stroke="{GOLD}" stroke-width="0.7"/>'
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{CR-2:.2f}" fill="none" '
            f'stroke="{GOLDl}" stroke-width="0.6"/>')


def build():
    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'width="{PW}mm" height="{PH}mm" viewBox="0 0 {PW} {PH}">')
    s.append(f'<rect x="0" y="0" width="{PW}" height="{PH}" fill="{PAPER}"/>')
    # crop marks
    for cx, cy in [(M, M), (PW-M, M), (M, PH-M), (PW-M, PH-M)]:
        s.append(f'<path d="M{cx-4} {cy} h8 M{cx} {cy-4} v8" stroke="{FAINT}" '
                 f'stroke-width="0.3"/>')

    # ---- masthead -------------------------------------------------------
    s.append(T(M, M+7, "BLINK", 9, anchor="start", weight="600"))
    s.append(T(M+34, M+7, "player board", 5, anchor="start", col=SOFT,
               style="font-style:italic"))
    s.append(T(PW-M, M+6, f"playtest \u00b7 {VTAG} \u00b7 units 13 mm", 3.4,
               anchor="end", col=SOFT, mono=True, spacing="0.3"))
    s.append(f'<line x1="{M}" y1="{M+11}" x2="{PW-M}" y2="{M+11}" '
             f'stroke="{INK}" stroke-width="0.5"/>')

    top = M + 16

    # ================= RESERVE / PROGRESS TRACK =========================
    # one continuous track, split into the four bands, laid as stacked rows.
    band_x = M + 2
    row_y = top + 12
    label_col_w = 36
    slots_x0 = band_x + label_col_w
    coin_x0 = slots_x0 + 6*D + 5*GAP + 8    # right of the widest (6) tier

    moves_x0 = coin_x0 + 4*(CD+2) + 6       # right of the widest food row
    asc_x0   = moves_x0 + 14
    cap_x0   = asc_x0 + 4*(CD+1.5) + 4
    # header over the meld/feed/moves columns
    s.append(T(coin_x0, top, "FOOD", 4.2, anchor="start",
               col=SOFT, mono=True, spacing="0.6"))
    s.append(T(moves_x0, top, "MV", 4.2, anchor="start",
               col=SOFT, mono=True, spacing="0.6"))
    s.append(T(asc_x0, top, "ASCEND", 3.8, anchor="start",
               col=SOFT, mono=True, spacing="0.6"))
    s.append(T(cap_x0, top, "CAP", 4.2, anchor="start",
               col=SOFT, mono=True, spacing="0.6"))
    s.append(T(band_x, top, "MELD", 4.2, anchor="start",
               col=SOFT, mono=True, spacing="0.6"))
    s.append(T(slots_x0, top, "RESERVE  \u2192  empty from the top tier down", 4.2,
               anchor="start", col=SOFT, mono=True, spacing="0.4"))

    y = row_y
    for i, (name, limit, n, coins, moves, asc, cap) in enumerate(BANDS):
        band_h = D + 2.5
        # band background
        active = False      # a blank board: nothing pre-filled
        s.append(f'<rect x="{band_x-2}" y="{y-R-3}" width="{PW-M-(band_x-2)-2}" '
                 f'height="{band_h}" rx="2.4" fill="{PANEL if i%2==0 else PAPER}" '
                 f'stroke="{LINE}" stroke-width="0.4"/>')
        # meld-limit chip
        s.append(f'<rect x="{band_x}" y="{y-R}" width="12" height="{D}" rx="2" '
                 f'fill="{GOLD if active else PAPER}" stroke="{INK}" stroke-width="0.6"/>')
        s.append(T(band_x+6, y+2.4, str(limit), 8, weight="600"))
        # band name
        s.append(T(band_x+16, y-1.3, name, 4.2, anchor="start", weight="600"))
        s.append(T(band_x+16, y+3.6, f"{n} units", 3.3, anchor="start",
                   col=SOFT, mono=True))
        # unit slots
        for k in range(n):
            cx = slots_x0 + R + k*(D+GAP)
            s.append(unit_slot(cx, y, filled=False))
        # feed coin slots (this band's own coins)
        if coins:
            for c in range(coins):
                cx = coin_x0 + CR + c*(CD+3)
                s.append(coin_slot(cx, y))
        else:
            s.append(T(coin_x0 + 6, y+1.5, "free", 3.3, anchor="start",
                       col=SOFT, mono=True, style="font-style:italic"))
        # free-move chip
        s.append(f'<rect x="{moves_x0}" y="{y-R+1.5}" width="10" height="{D-3}" rx="2" '
                 f'fill="{PAPER}" stroke="{SOFT}" stroke-width="0.5"/>')
        s.append(T(moves_x0+5, y+2.2, str(moves), 6.5, weight="600"))
        # ascension coin spots — printed, taken once on first arrival
        if asc:
            for k in range(asc):
                s.append(coin_slot(asc_x0 + CR + k*(CD+1.5), y))
        else:
            s.append(T(asc_x0 + 6, y+1.5, "\u2014", 3.3, anchor="start",
                       col=SOFT, mono=True))
        s.append(T(cap_x0 + 6, y+2.0, cap, 5.5, anchor="start", weight="600"))
        y += band_h + 1.5

    # upkeep note under the whole track, full width
    s.append(T(band_x-2, y+2.5,
               "FOOD is NOT cumulative \u2014 each recycle your people eat your current "
               "tier's coins.", 3.3, anchor="start", col=SOFT, mono=True, spacing="0.2"))
    s.append(T(band_x-2, y+6.6,
               "ASCEND coins are taken once, the first time you reach that tier. "
               "CAP is the highest rank you may buy.", 3.3,
               anchor="start", col=SOFT, mono=True, spacing="0.2"))

    # ================= lower zone: GOLD, then the victory row ============
    low = y + 13
    s.append(f'<line x1="{M}" y1="{low-6}" x2="{PW-M}" y2="{low-6}" '
             f'stroke="{LINE}" stroke-width="0.4"/>')

    # --- GOLD STORAGE (left) ---
    gx = M
    s.append(T(gx, low, "GOLD", 4.6, anchor="start", weight="600"))
    s.append(T(gx, low+5, "1 per cashed card \u00b7 research, fortify, attacks, food", 3.2, anchor="start", col=SOFT, mono=True))
    gv_y = low + 9
    gvw, gvh = 92, 20
    s.append(f'<rect x="{gx}" y="{gv_y}" width="{gvw}" height="{gvh}" rx="3" '
             f'fill="{PAPER}" stroke="{GOLD}" stroke-width="0.8"/>')
    for rr in range(2):
        for cc in range(6):
            s.append(f'<circle cx="{gx + 9 + cc*12.5:.2f}" '
                     f'cy="{gv_y + 7 + rr*10:.2f}" r="4.3" fill="none" '
                     f'stroke="{GOLDl}" stroke-width="0.5"/>')

    # --- scoring reminder, to the right of the gold box ---
    sx = gx + gvw + 14
    s.append(T(sx, low, "SCORING", 4.6, anchor="start", weight="600"))
    s.append(T(sx, low+6, "units on map  +  centre rank of your victory row  +  "
               "3 per terrain majority", 3.4, anchor="start", col=INK, mono=True,
               spacing="0.15"))
    s.append(T(sx, low+11.5, "gold breaks ties \u00b7 fewer than 3 cards in the row "
               "score 1 each", 3.2, anchor="start", col=SOFT, mono=True))
    s.append(T(sx, low+20, "The row scores the card in the CENTRE slot, so fill it "
               "\u2014 and mind what lands in the middle.", 3.2, anchor="start",
               col=SOFT, mono=True, style="font-style:italic"))

    # --- VICTORY ROW: real cards, tucked under the bottom edge ---
    # Five standard 63.5 mm cards side by side need 317 mm; the printable width
    # is 269 mm. So they overlap left-to-right, each showing its top-left index,
    # and hang off the bottom of the board.
    CARD_W, CARD_H = 63.5, 88.9
    vy = PH - 26                       # only the top 26 mm sits on the board
    vlabel_y = vy - 4.5
    s.append(T(M, vlabel_y, "VICTORY ROW", 4.6, anchor="start", weight="600"))
    s.append(T(M + 58, vlabel_y, "\u2014 slide cards in from below, ranks ascending "
               "left to right; the centre slot scores", 3.2, anchor="start",
               col=SOFT, mono=True))
    avail = (PW - M) - M
    pitch = (avail - CARD_W) / 4
    s.append(f'<clipPath id="sheet"><rect x="0" y="0" width="{PW}" '
             f'height="{PH}"/></clipPath>')
    s.append(f'<g clip-path="url(#sheet)">')
    # the four ordinary slots first, then the centre one on top so that its
    # highlight and label are never covered by the slot that overlaps it
    for k in (0, 1, 3, 4):
        cx = M + k*pitch
        s.append(f'<rect x="{cx:.2f}" y="{vy}" width="{CARD_W}" height="{CARD_H}" '
                 f'rx="3" fill="{PAPER}" stroke="{FAINT}" stroke-width="0.7" '
                 f'stroke-dasharray="2.5 2"/>')
        s.append(T(cx + 5.5, vy + 7.5, f"{k+1}", 5.5, anchor="start", col=FAINT))

    cx = M + 2*pitch
    s.append(f'<rect x="{cx:.2f}" y="{vy}" width="{CARD_W}" height="{CARD_H}" '
             f'rx="3" fill="{GOLDl}" fill-opacity="0.55" stroke="{GOLD}" '
             f'stroke-width="1.4"/>')
    s.append(T(cx + 5.5, vy + 7.5, "3", 5.5, anchor="start", col=INK, weight="600"))
    s.append(T(cx + 11, vy + 7.2, "SCORES", 3.8, anchor="start", col=GOLDd,
               mono=True, spacing="0.5", weight="600"))
    mx = cx + 16
    s.append(f'<path d="M{mx-3.2:.1f} {vy-3.4} L{mx:.1f} {vy-0.5} '
             f'L{mx+3.2:.1f} {vy-3.4} Z" fill="{GOLD}"/>')
    s.append('</g>')
    by = vlabel_y - 6
    s.append(f'<line x1="{M}" y1="{by}" x2="{PW-M}" y2="{by}" '
             f'stroke="{LINE}" stroke-width="0.4"/>')

    # hard check: nothing may spill past the RIGHT margin either
    right_edge = cap_x0 + 12
    if right_edge > PW - M:
        raise SystemExit(f"board_a4: columns overflow the right margin by "
                         f"{right_edge - (PW - M):.1f} mm")

    # hard check: nothing may spill past the bottom margin
    overflow = (gv_y + gvh + 2) - by
    if overflow > 0:
        raise SystemExit(f"board_a4: gold box collides with the victory row "
                         f"by {overflow:.1f} mm")

    s.append('</svg>')
    return "\n".join(s)


if __name__ == "__main__":
    import pathlib
    svg = build()
    pathlib.Path("board_a4.svg").write_text(svg)
    print("wrote board_a4.svg", len(svg), "bytes")
