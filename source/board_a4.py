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
# The row is drawn CENTRED on its baseline y. It used to start at y - R - 3
# while standing only D + 2.5 tall, which put the rectangle's middle 1.75 mm
# above the middle of the circles it was meant to contain — so the unit slots
# and the meld chip, both a full D across, broke through the bottom edge of
# their own row. Anything drawn at y is now centred in the band by definition.
BAND_H = D + 2.5

BANDS = [
    # (label, meld_limit, n_units, feed_coins, free_moves, ascension, rank_cap)
    # Units are 2/3/5/5/5 as of v0.23 — still twenty, redistributed. The v0.22
    # board was 2/4/6/4/4 and is kept as a layout option in the app.
    ("Tribe",        2, 2, 0, 1, 0, "12"),
    ("Settlement",   3, 3, 1, 2, 1, "14"),
    ("Kingdom",      4, 5, 2, 3, 2, "16"),
    ("Empire",       5, 5, 3, 4, 3, "18"),
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

    # The reserve column used to reserve room for SIX unit slots — a leftover
    # from the v0.22 board, whose widest tier was 6. Since 2/3/5/5/5 the widest
    # is five, so every row carried a dead slot's width (D + GAP = 17 mm) of
    # nothing between the last circle and FOOD. Derive it from the table so the
    # next layout change cannot reintroduce the gap.
    maxu = max(b[2] for b in BANDS)
    slots_w = maxu*D + (maxu-1)*GAP

    # MELD and CAP both answer "which cards may I use" — one the count, one the
    # rank ceiling — so they sit together at the left instead of at opposite
    # ends of the sheet with 200 mm between them. What is left of the row is
    # then all one thing: the units you hold and what this tier costs to run.
    meld_x0  = band_x
    cap_x0   = band_x + 15
    name_x0  = band_x + 28
    label_col_w = 58
    slots_x0 = band_x + label_col_w
    food_x0  = slots_x0 + slots_w + 12
    food_w   = 4*(CD+3)
    moves_x0 = food_x0 + food_w + 8
    asc_x0   = moves_x0 + 15
    asc_w    = 4*(CD+1.5)
    sep_x    = slots_x0 + slots_w + 5       # units | upkeep

    s.append(T(meld_x0+6, top, "MELD", 3.6, col=SOFT, mono=True, spacing="0.4"))
    s.append(T(cap_x0+5.5, top, "CAP", 3.6, col=SOFT, mono=True, spacing="0.4"))
    # just the label: the rule about emptying top-down ran into FOOD, and it
    # belongs with the other standing rules under the track anyway
    s.append(T(slots_x0, top, "RESERVE", 4.2,
               anchor="start", col=SOFT, mono=True, spacing="0.4"))
    s.append(T(food_x0, top, "FOOD", 4.2, anchor="start",
               col=GOLDd, mono=True, spacing="0.6", weight="600"))
    s.append(T(moves_x0, top, "MV", 4.2, anchor="start",
               col=SOFT, mono=True, spacing="0.6"))
    s.append(T(asc_x0, top, "ASCEND", 3.8, anchor="start",
               col=SOFT, mono=True, spacing="0.6"))

    y = row_y
    for i, (name, limit, n, coins, moves, asc, cap) in enumerate(BANDS):
        band_h = BAND_H
        band_top = y - band_h/2
        # band background
        active = False      # a blank board: nothing pre-filled
        s.append(f'<rect x="{band_x-2}" y="{band_top:.2f}" '
                 f'width="{PW-M-(band_x-2)-2}" '
                 f'height="{band_h}" rx="2.4" fill="{PANEL if i%2==0 else PAPER}" '
                 f'stroke="{LINE}" stroke-width="0.4"/>')
        # FOOD is the number that ambushes people — it comes due on a recycle,
        # in the middle of somebody else's excitement — so the column is tinted
        # the colour of the coins it asks for, all the way down.
        s.append(f'<rect x="{food_x0-4}" y="{band_top:.2f}" width="{food_w+7}" '
                 f'height="{band_h}" fill="{GOLDl}" fill-opacity="0.3"/>')
        # meld-limit chip
        s.append(f'<rect x="{meld_x0}" y="{y-R}" width="12" height="{D}" rx="2" '
                 f'fill="{GOLD if active else PAPER}" stroke="{INK}" stroke-width="0.6"/>')
        s.append(T(meld_x0+6, y+2.4, str(limit), 8, weight="600"))
        # rank cap, beside the meld limit: how high, next to how many
        s.append(T(cap_x0+5.5, y+2.4, cap, 7, weight="600", col=INK))
        # band name
        s.append(T(name_x0, y-1.3, name, 4.0, anchor="start", weight="600"))
        s.append(T(name_x0, y+3.6, f"{n} units", 3.3, anchor="start",
                   col=SOFT, mono=True))
        # unit slots, centred: the column is sized for the widest tier, so a
        # left-aligned Tribe row left its two circles stranded against the
        # label with a hand's width of nothing after them
        row_w = n*D + (n-1)*GAP
        off = (slots_w - row_w) / 2
        for k in range(n):
            cx = slots_x0 + off + R + k*(D+GAP)
            s.append(unit_slot(cx, y, filled=False))
        # feed coin slots (this band's own coins)
        if coins:
            for c in range(coins):
                cx = food_x0 + CR + c*(CD+3)
                s.append(coin_slot(cx, y))
        else:
            s.append(T(food_x0 + 6, y+1.5, "free", 3.3, anchor="start",
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
        y += band_h + 1.5

    # One rule down the row: to its left is what you hold, to its right what
    # holding it costs you every recycle.
    s.append(f'<line x1="{sep_x}" y1="{row_y-BAND_H/2:.2f}" x2="{sep_x}" '
             f'y2="{y-1.5-BAND_H/2:.2f}" '
             f'stroke="{LINE}" stroke-width="0.4"/>')

    # upkeep note under the whole track, full width
    # Every column named, in the order they are read. MELD and MV had no
    # gloss at all, so the two numbers a player uses every single round were
    # the two the board never explained.
    s.append(T(band_x-2, y+3.0,
               "MELD = most cards you may play in a round \u00b7 "
               "CAP = highest rank you may buy, +2 a tier \u00b7 "
               "MV = your free moves", 3.3,
               anchor="start", col=SOFT, mono=True, spacing="0.15"))
    s.append(T(band_x-2, y+7.4,
               "FOOD is NOT cumulative: each recycle you pay your CURRENT tier \u00b7 "
               "ASCEND taken once, on arrival \u00b7 RESERVE empties top down", 3.3,
               anchor="start", col=SOFT, mono=True, spacing="0.15"))

    # ================= lower zone: GOLD, then the victory row ============
    low = y + 15
    s.append(f'<line x1="{M}" y1="{low-6}" x2="{PW-M}" y2="{low-6}" '
             f'stroke="{LINE}" stroke-width="0.4"/>')

    # --- GOLD STORAGE (left) ---
    gx = M
    s.append(T(gx, low, "GOLD", 4.6, anchor="start", weight="600"))
    s.append(T(gx, low+5, "1 per cashed card \u00b7 research, fortify, attacks, food", 3.2, anchor="start", col=SOFT, mono=True))
    gv_y = low + 9
    gvw, gvh = 92, 19
    s.append(f'<rect x="{gx}" y="{gv_y}" width="{gvw}" height="{gvh}" rx="3" '
             f'fill="{PAPER}" stroke="{GOLD}" stroke-width="0.8"/>')
    # Twelve printed circles read as twelve slots, and a player who filled
    # them would reasonably think that was the ceiling. It is not — gold is
    # unbounded. So: one coin with a couple behind it, which reads as a pile.
    ccx, ccy = gx + 15, gv_y + gvh/2
    s.append(f'<circle cx="{ccx-3.5:.2f}" cy="{ccy-2:.2f}" r="6" fill="{PAPER}" '
             f'stroke="{GOLDl}" stroke-width="0.6"/>')
    s.append(f'<circle cx="{ccx+3.5:.2f}" cy="{ccy+2:.2f}" r="6" fill="{PAPER}" '
             f'stroke="{GOLDl}" stroke-width="0.6"/>')
    s.append(f'<circle cx="{ccx:.2f}" cy="{ccy:.2f}" r="6" fill="{PAPER}" '
             f'stroke="{GOLD}" stroke-width="0.9"/>')
    s.append(f'<circle cx="{ccx:.2f}" cy="{ccy:.2f}" r="4" fill="none" '
             f'stroke="{GOLDl}" stroke-width="0.6"/>')
    s.append(T(gx + 28, ccy - 0.8, "keep your coins here", 3.4, anchor="start",
               col=INK, mono=True))
    s.append(T(gx + 28, ccy + 4.0, "no limit \u2014 pile them up", 3.1,
               anchor="start", col=SOFT, mono=True))

    # --- scoring reminder, to the right of the gold box ---
    sx = gx + gvw + 14
    # The victory row scores TWICE: a point for every card in it, and then the
    # rank of its centre card on top (engine: vrowScore = length + centre).
    # The board printed only the second half, so a full row of five looked
    # worth its centre rank when it is worth that plus five. One line per
    # source, because three addends in a sentence is where it got lost.
    s.append(T(sx, low, "SCORING", 4.6, anchor="start", weight="600"))
    for j, line in enumerate([
            "1  per unit you have on the map",
            "1  per card in your victory row \u2014 however many you hold",
            "+  the RANK of the card in the centre slot (3 cards or more)",
            "3  per terrain majority"]):
        s.append(T(sx, low+6.2+j*4.6, line, 3.4, anchor="start", col=INK,
                   mono=True, spacing="0.15"))
    score_last = low + 26.5
    s.append(T(sx, score_last, "gold breaks ties \u00b7 a row of 1 or 2 cards scores "
               "those cards only", 3.2, anchor="start", col=SOFT, mono=True))

    # --- VICTORY ROW: real cards, tucked under the bottom edge ---
    # Five standard 63.5 mm cards side by side need 317 mm; the printable width
    # is 269 mm. So they overlap left-to-right, each showing its top-left index,
    # and hang off the bottom of the board.
    # Five poker cards need 317.5 mm and the sheet is 297, so they cannot all
    # sit whole INSIDE the margins — but they can sit whole on the row and let
    # the sheet cut the outer two. The first and last slots run off the left
    # and right edges and serve as position indicators; the cards themselves
    # overhang the board, which is what they would do on a table anyway.
    #
    # Centring five 63.5 mm slots on a 297 mm sheet puts the scoring slot dead
    # centre at 148.5 mm, and costs slots 1 and 5 exactly 10.25 mm each.
    CARD_W, CARD_H = 63.5, 88.9        # poker: 2.5 x 3.5 in
    vrow_x0 = (PW - 5*CARD_W) / 2      # negative: the row is wider than the sheet
    vy = PH - 26                       # only the top 26 mm sits on the board
    vlabel_y = vy - 4.5
    s.append(T(M, vlabel_y, "VICTORY ROW", 4.6, anchor="start", weight="600"))
    s.append(T(M + 58, vlabel_y, "\u2014 slide cards in from below; the centre "
               "slot scores", 3.2, anchor="start", col=SOFT, mono=True))

    # Rank order, stated as a direction rather than left to the caption.
    ax0, ax1 = M + 150, PW - M
    s.append(f'<line x1="{ax0}" y1="{vlabel_y-1.3:.1f}" x2="{ax1-3.4:.1f}" '
             f'y2="{vlabel_y-1.3:.1f}" stroke="{SOFT}" stroke-width="0.5"/>')
    s.append(f'<path d="M{ax1-3.6:.1f} {vlabel_y-3.3:.1f} L{ax1:.1f} '
             f'{vlabel_y-1.3:.1f} L{ax1-3.6:.1f} {vlabel_y+0.7:.1f} Z" fill="{SOFT}"/>')
    s.append(T(ax0 + 2, vlabel_y - 2.6, "LOWEST RANK", 2.9, anchor="start",
               col=SOFT, mono=True, spacing="0.3"))
    s.append(T(ax1 - 5, vlabel_y - 2.6, "HIGHEST", 2.9, anchor="end",
               col=SOFT, mono=True, spacing="0.3"))

    s.append(f'<clipPath id="sheet"><rect x="0" y="0" width="{PW}" '
             f'height="{PH}"/></clipPath>')
    s.append(f'<g clip-path="url(#sheet)">')
    for k in range(5):
        cx = vrow_x0 + k*CARD_W
        mid = (k == 2)
        s.append(f'<rect x="{cx:.2f}" y="{vy}" width="{CARD_W}" height="{CARD_H}" '
                 f'rx="3" fill="{GOLDl if mid else PAPER}" '
                 f'{"fill-opacity=" + chr(34) + "0.55" + chr(34) + " " if mid else ""}'
                 f'stroke="{GOLD if mid else FAINT}" '
                 f'stroke-width="{1.4 if mid else 0.7}"'
                 f'{"" if mid else " stroke-dasharray=" + chr(34) + "2.5 2" + chr(34)}/>')
        # slot 1's index would fall off the left edge with the rest of its box
        lx = max(cx + 5.5, 4.5)
        s.append(T(lx, vy + 7.5, f"{k+1}", 5.5, anchor="start",
                   col=INK if mid else FAINT, weight="600" if mid else "400"))
    cx = vrow_x0 + 2*CARD_W
    s.append(T(cx + 11, vy + 7.2, "SCORES", 3.8, anchor="start", col=GOLDd,
               mono=True, spacing="0.5", weight="600"))
    mx = cx + 16
    s.append(f'<path d="M{mx-3.2:.1f} {vy-3.4} L{mx:.1f} {vy-0.5} '
             f'L{mx+3.2:.1f} {vy-3.4} Z" fill="{GOLD}"/>')
    s.append('</g>')
    # The bottom crop marks are drawn before all this and the card fills are
    # the paper colour, so without redrawing them here the trim guides for two
    # corners of the sheet simply vanish under slots 1 and 5.
    for ccx, ccy in [(M, PH-M), (PW-M, PH-M)]:
        s.append(f'<path d="M{ccx-4} {ccy} h8 M{ccx} {ccy-4} v8" stroke="{SOFT}" '
                 f'stroke-width="0.3"/>')
    by = vlabel_y - 6
    s.append(f'<line x1="{M}" y1="{by}" x2="{PW-M}" y2="{by}" '
             f'stroke="{LINE}" stroke-width="0.4"/>')

    # hard check: nothing may spill past the RIGHT margin either
    right_edge = asc_x0 + asc_w
    if right_edge > PW - M:
        raise SystemExit(f"board_a4: columns overflow the right margin by "
                         f"{right_edge - (PW - M):.1f} mm")

    # hard check: nothing may spill past the bottom margin
    overflow = (gv_y + gvh + 2) - by
    if overflow > 0:
        raise SystemExit(f"board_a4: gold box collides with the victory row "
                         f"by {overflow:.1f} mm")

    # ...and the scoring column, which sits beside the gold box and grew past
    # it once already: its last line landed exactly on the divider rule.
    if score_last > by - 2:
        raise SystemExit(f"board_a4: the scoring block's last line at "
                         f"{score_last:.1f} mm runs into the victory row "
                         f"divider at {by:.1f} mm")

    s.append('</svg>')
    return "\n".join(s)


if __name__ == "__main__":
    import pathlib
    svg = build()
    pathlib.Path("board_a4.svg").write_text(svg)
    print("wrote board_a4.svg", len(svg), "bytes")
