# -*- coding: utf-8 -*-
# SUPERSEDED - not part of the build.
#
# board_a4.py now produces a blank board (the demo units and the highlighted
# band were removed in v0.20), so this file duplicates it. Its lower zone was
# never updated for the full-size victory row and currently collides with the
# gold box. Kept only for reference; delete it once you are sure you do not
# want a second board variant.
"""Blink player board - blank, print-exact A4 landscape (mm units)."""

PW, PH = 297.0, 210.0
M = 14.0

INK, SOFT, FAINT = "#2A2E2B", "#6B6F68", "#B9B4A8"
PAPER, PANEL, LINE = "#FBFAF6", "#EFECE3", "#CDC7B8"
RED, REDdk = "#C0392B", "#7B2018"
GOLD, GOLDl = "#C9992B", "#EBD9A6"

D = 13.0            # unit slot diameter (spec)
R = D / 2
GAP = 4.0
CD = 9.0
CR = CD / 2

BANDS = [
    ("Tribe",        2, 2, 0, 1),
    ("Settlement",   3, 4, 1, 2),
    ("Kingdom",      4, 5, 2, 3),
    ("Empire",       5, 5, 3, 4),
    ("Civilization", 6, 4, 4, 5),
]


def T(x, y, s, size=4.2, anchor="middle", col=INK, weight="400",
      mono=False, spacing="0", style=""):
    fam = "IBM Plex Mono" if mono else "IBM Plex Sans"
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="{fam}" font-size="{size}" '
            f'fill="{col}" text-anchor="{anchor}" font-weight="{weight}" '
            f'letter-spacing="{spacing}" style="{style}">{s}</text>')


def unit_slot(x, y):
    return (f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{R:.2f}" fill="none" '
            f'stroke="{FAINT}" stroke-width="0.7" stroke-dasharray="1.8 1.8"/>')


def coin_slot(x, y):
    return (f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{CR:.2f}" fill="{PAPER}" '
            f'stroke="{GOLD}" stroke-width="0.8"/>')


def build():
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{PW}mm" '
         f'height="{PH}mm" viewBox="0 0 {PW} {PH}">']
    s.append(f'<rect width="{PW}" height="{PH}" fill="{PAPER}"/>')
    for cx, cy in [(M, M), (PW-M, M), (M, PH-M), (PW-M, PH-M)]:
        s.append(f'<path d="M{cx-4} {cy} h8 M{cx} {cy-4} v8" '
                 f'stroke="{FAINT}" stroke-width="0.3"/>')

    # masthead
    s.append(T(M, M+7, "BLINK", 9, "start", weight="600"))
    s.append(T(M+30, M+7, "player board", 5, "start", SOFT, style="font-style:italic"))
    s.append(T(PW-M, M+6, "playtest \u00b7 v0.17 \u00b7 units 15 mm", 3.4, "end",
               SOFT, mono=True, spacing="0.3"))
    s.append(f'<line x1="{M}" y1="{M+11}" x2="{PW-M}" y2="{M+11}" '
             f'stroke="{INK}" stroke-width="0.5"/>')

    top = M + 20
    band_x = M + 2
    slots_x0 = band_x + 42
    # widest band is 8 slots; compute its right edge, then place FEED column
    widest_right = slots_x0 + 8*D + 7*GAP
    coin_x0 = widest_right + 10
    # ensure 3 coin slots + margin fit before page edge
    coins_right = coin_x0 + 3*CD + 2*3
    assert coins_right < PW - M, f"coins overflow: {coins_right:.1f}"

    s.append(T(band_x-2, top, "RESERVE", 4.4, "start", SOFT, mono=True, spacing="0.6"))
    s.append(T(slots_x0, top, "empty from the top band down as units reach the map",
               3.4, "start", SOFT, mono=True))
    moves_x0 = coin_x0 + 3*(CD+3) + 10
    s.append(T(coin_x0, top, "FOOD", 4.4, "start", SOFT, mono=True, spacing="0.6"))
    s.append(T(moves_x0, top, "MOVES", 4.4, "start", SOFT, mono=True, spacing="0.6"))

    y = top + 12
    band_h = D + 7
    for i, (name, limit, n, coins, moves) in enumerate(BANDS):
        s.append(f'<rect x="{band_x-2}" y="{y-R-3}" width="{PW-M-(band_x-2)-2}" '
                 f'height="{band_h}" rx="2.4" fill="{PANEL if i%2 else PAPER}" '
                 f'stroke="{LINE}" stroke-width="0.4"/>')
        # meld-limit chip
        s.append(f'<rect x="{band_x}" y="{y-R}" width="12" height="{D}" rx="2" '
                 f'fill="{PAPER}" stroke="{INK}" stroke-width="0.6"/>')
        s.append(T(band_x+6, y+2.4, str(limit), 8, weight="600"))
        s.append(T(band_x+6, y+R+4.2, "cards", 2.6, col=SOFT, mono=True))
        s.append(T(band_x+16, y-1.3, name, 4.2, "start", weight="600"))
        s.append(T(band_x+16, y+3.6, f"{n} units", 3.3, "start", SOFT, mono=True))
        for k in range(n):
            s.append(unit_slot(slots_x0 + R + k*(D+GAP), y))
        if coins:
            for c in range(coins):
                s.append(coin_slot(coin_x0 + CR + c*(CD+3), y))
        else:
            s.append(T(coin_x0 + 2, y+1.5, "free", 3.3, "start", SOFT,
                       mono=True, style="font-style:italic"))
        s.append(f'<rect x="{moves_x0}" y="{y-R+1.5}" width="10" height="{D-3}" rx="2" '
                 f'fill="{PAPER}" stroke="{SOFT}" stroke-width="0.5"/>')
        s.append(T(moves_x0+5, y+2.2, str(moves), 6.5, weight="600"))
        y += band_h + 2.5

    # upkeep note, wrapped to two centred lines under the track
    ny = y + 3
    s.append(T(band_x-2, ny,
               "FOOD (not cumulative) \u2014 each time your hand recycles, your people "
               "eat the coins on your current band's slots.", 3.4, "start",
               SOFT, mono=True, spacing="0.15"))
    s.append(T(band_x-2, ny+5,
               "Short a coin? Return units from the map until the remaining "
               "empty slots are covered.", 3.4, "start", SOFT, mono=True,
               spacing="0.15"))

    # ---- lower zone ----
    low = ny + 16
    s.append(f'<line x1="{M}" y1="{low-6}" x2="{PW-M}" y2="{low-6}" '
             f'stroke="{LINE}" stroke-width="0.4"/>')

    gx = M + 2
    s.append(T(gx, low, "GOLD", 4.6, "start", weight="600"))
    s.append(T(gx, low+5, "1 per unused meld card", 3.3, "start", SOFT, mono=True))
    gvw, gvh = 96, 30
    gv_y = low + 9
    s.append(f'<rect x="{gx}" y="{gv_y}" width="{gvw}" height="{gvh}" rx="3" '
             f'fill="{PAPER}" stroke="{GOLD}" stroke-width="0.8"/>')
    for rr in range(2):
        for cc in range(6):
            s.append(f'<circle cx="{gx+9+cc*13:.2f}" cy="{gv_y+9+rr*12:.2f}" '
                     f'r="4.2" fill="none" stroke="{GOLDl}" stroke-width="0.5"/>')

    sx = gx + gvw + 14
    s.append(T(sx, low, "SCORING", 4.6, "start", weight="600"))
    s.append(T(sx, low+6, "units on map  +  centre rank of your victory row  +  "
              "3 per terrain: biggest connected stretch", 3.4, "start", INK, mono=True, spacing="0.15"))
    s.append(T(sx, low+11.5, "gold breaks ties \u00b7 fewer than 3 cards in the row "
              "score 1 each", 3.2, "start", SOFT, mono=True))

    # Victory row: five standard 63.5 mm cards need 317 mm and the printable
    # width is 269 mm, so they overlap and hang off the bottom of the board.
    CARD_W, CARD_H = 63.5, 88.9
    vy = PH - 26
    vlabel_y = vy - 4.5
    s.append(T(M, vlabel_y, "VICTORY ROW", 4.6, "start", weight="600"))
    s.append(T(M+58, vlabel_y, "\u2014 slide cards in from below, ranks ascending "
              "left to right; the centre slot scores", 3.2, "start", SOFT, mono=True))
    pitch = ((PW - M) - M - CARD_W) / 4
    s.append(f'<clipPath id="sheet"><rect x="0" y="0" width="{PW}" height="{PH}"/></clipPath>')
    s.append('<g clip-path="url(#sheet)">')
    for k in range(5):
        cx = M + k*pitch
        s.append(f'<rect x="{cx:.2f}" y="{vy}" width="{CARD_W}" height="{CARD_H}" '
                 f'rx="3" fill="{PAPER}" stroke="{FAINT}" stroke-width="0.7" '
                 f'stroke-dasharray="2.5 2"/>')
        s.append(T(cx+5.5, vy+7.5, f"{k+1}", 5.5, "start", FAINT))
    s.append('</g>')
    by = vlabel_y - 6
    s.append(f'<line x1="{M}" y1="{by}" x2="{PW-M}" y2="{by}" '
             f'stroke="{LINE}" stroke-width="0.4"/>')

    s.append('</svg>')
    return "\n".join(s)


if __name__ == "__main__":
    import pathlib
    pathlib.Path("board_blank.svg").write_text(build())
    print("wrote board_blank.svg")
