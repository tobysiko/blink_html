from figs import *

F = {}

# ---------------------------------------------------------------- hero map
def hero():
    b = ""
    layout = [
        (0, 0, "plains"), (1, 0, "plains"), (2, 0, "forest"), (3, 0, "mountain"),
        (-1, 1, "ocean"), (0, 1, "plains"), (1, 1, "forest"), (2, 1, "forest"), (3, 1, "mountain"),
        (-1, 2, "ocean"), (0, 2, "ocean"), (1, 2, "plains"), (2, 2, "plains"), (3, 2, "forest"),
        (0, 3, "ocean"), (1, 3, "ocean"), (2, 3, "plains"),
    ]
    layout.sort(key=lambda t: (t[1], t[0]))
    units = {(0, 1): ("you", 2), (1, 1): ("you", 1), (1, 2): ("you", 3),
             (2, 2): ("you", 1), (2, 1): ("rival", 2), (3, 1): ("rival", 1),
             (0, 2): ("you", 1), (1, 3): ("rival", 1)}
    for col, row, ter in layout:
        x, y = axial(col, row)
        b += prism(x, y, ter)
        if (col, row) in units:
            who, n = units[(col, row)]
            b += unit(x, y - TER[ter]["h"] * 0 , who, n)
    x, y = axial(4, 1)
    b += prism(x, y, None, empty=True, dashed=True)
    return svg(0, 0, b, vb="auto")

F["hero"] = hero()

# ------------------------------------------------------- meld panels
def meld_rule():
    """The unified meld rule: an unbroken run of ranks, duplicates free.

    Four legal examples and one illegal one, each as a row of cards with the
    ranks that make it work called out beneath. Suits are deliberately mixed
    so the eye is not tempted to read them as meaningful."""
    rows = [
        ([(2, "plains")], "one card is always a run", True),
        ([(2, "forest"), (2, "ocean")], "one rank, doubled", True),
        ([(2, "plains"), (3, "mountain")], "2 then 3", True),
        ([(2, "ocean"), (3, "plains"), (3, "forest"), (4, "mountain"), (4, "plains")],
         "2, 3, 4 all present \u2014 doubles are free", True),
        ([(2, "plains"), (2, "forest"), (4, "ocean"), (4, "mountain")],
         "nothing at rank 3 \u2014 the run is broken", False),
    ]
    cw, gap, rowgap = 40, 6, 26
    b, y = "", 0
    label_x = 5 * (cw + gap) + 16
    for cards, why, ok in rows:
        for i, (rank, suit) in enumerate(cards):
            b += card(i * (cw + gap), y, rank, suit, w=cw, h=54)
        mark = "\u2713" if ok else "\u2717"
        col = "#37704A" if ok else "#C0392B"
        b += (f'<text x="{label_x}" y="{y+26:.0f}" font-family="IBM Plex Sans" '
              f'font-size="19" font-weight="600" fill="{col}">{mark}</text>')
        b += (f'<text x="{label_x+24}" y="{y+26:.0f}" font-family="IBM Plex Sans" '
              f'font-size="12" fill="#5A5F59">{why}</text>')
        y += 54 + rowgap
    # explicit viewBox: the auto-fitter measures shapes, not text, so the
    # right-hand explanations would be clipped. Width is the widest label.
    total_h = y - rowgap
    return svg(0, 0, b, vb=f"-6 -6 528 {total_h + 12}")


F["meld_rule"] = meld_rule()


# ------------------------------------------------------- terrain heights
def terrains():
    b = ""
    order = [("ocean", "Ocean", "1"), ("plains", "Plains", "3"),
             ("forest", "Forest", "2"), ("mountain", "Mountain", "1")]
    for i, (key, name, cap) in enumerate(order):
        x = 60 + i * 108
        y = 96
        b += prism(x, y, key)
        b += label(x, y + TER[key]["h"] + 34, name, 14, cls="fig-strong")
        b += label(x, y + TER[key]["h"] + 52, f"holds {cap}", 12)
        b += label(x, y + TER[key]["h"] + 68, ["free","free","costs 1 gold","costs 2 gold"][i], 11, cls="fig-step")
    b += label(60, 30, "flat", 11, cls="fig-step")
    b += label(168, 30, "flat", 11, cls="fig-step")
    b += label(276, 30, "2 layers", 11, cls="fig-step")
    b += label(384, 30, "3 layers", 11, cls="fig-step")
    return svg(0, 0, b, vb="auto")

F["terrain"] = terrains()

# ------------------------------------------------------- explore
def explore():
    b = ""
    layout = [(0, 0, "plains"), (1, 0, "forest")]
    for c, r, t in layout:
        x, y = axial(c, r)
        b += prism(x, y, t)
    x, y = axial(0, 0); b += unit(x, y, "you", 1)
    x, y = axial(1, 0)
    b += unit(x, y, "you", 1)
    x, y = axial(2, 0)
    b += prism(x, y, None, empty=True, dashed=True)
    b += label(x, y + 4, "?", 22, cls="fig-strong")
    b += label(x, y + 48, "no tile here yet", 11)
    b += ('<path d="M{:.0f} {:.0f} l26 0 M{:.0f} {:.0f} l-8 -6 M{:.0f} {:.0f} l-8 6"'
          ' fill="none" stroke="#C0392B" stroke-width="2" stroke-linecap="round"/>'
          .format(axial(1, 0)[0] + 28, 0, axial(1, 0)[0] + 54, 0, axial(1, 0)[0] + 54, 0))
    b += card(178, -32, 6, "ocean", w=40, h=56)
    b += label(198, 44, "play 6 of Ocean", 11, anchor="middle")
    b += label(198, 59, "\u2192 place a tile", 11, anchor="middle")
    return svg(0, 0, b, vb="auto")

F["explore"] = explore()

# ------------------------------------------------------- combat
def combat():
    """v0.21: no pattern, no movement. A single card spent on an adjacent
    rival tile removes one defender — the attacker's unit never leaves the
    reserve. Drawn in the same grammar as the other panels: card, arrow,
    cells."""
    cw, ch = 46, 62
    x_you, _ = axial(0, 0)
    x_riv, _ = axial(1, 0)
    b = ""
    # the card is spent on the rival cell, so it hangs over that tile
    b += card(x_riv - cw / 2, 0, 6, "forest", w=cw, h=ch)
    ay = ch + 10
    b += (f'<path d="M{x_riv:.1f} {ay} l0 16 M{x_riv-5:.1f} {ay+10} l5 6 l5 -6" '
          f'fill="none" stroke="#C0392B" stroke-width="2.2" stroke-linecap="round" '
          f'stroke-linejoin="round"/>')
    tile_y = ay + 34 + R
    maxh = max(TER["plains"]["h"], TER["forest"]["h"])
    b += prism(x_you, tile_y, "plains")
    b += unit(x_you, tile_y, "you", 1)
    b += prism(x_riv, tile_y, "forest")
    b += unit(x_riv, tile_y, "rival", 2)
    # the attack pays Forest's price: one gold beside the struck tile
    b += gold(x_riv + 19, tile_y - R - 3)
    b += label(x_you, tile_y + R + maxh + 17, "yours", 10, cls="fig-step")
    b += label(x_riv, tile_y + R + maxh + 17, "attack", 10, cls="fig-attack")
    centre = (x_you + x_riv) / 2
    b += label(centre, tile_y + R + maxh + 38,
               "One defender removed — your unit stays in reserve.",
               11, cls="fig-strong")
    return svg(0, 0, b, vb="auto")


F["combat"] = combat()

# ------------------------------------------------------- fortify
def fortify():
    b = ""
    x, y = axial(0, 0)
    b += prism(x, y, "plains")
    b += unit(x, y, "you", 1)
    b += gold(x, y - 9)
    b += label(x, y + 46, "fortified", 11, cls="fig-strong")
    b += ('<path d="M40 0 l30 0 M64 -6 l6 6 l-6 6" fill="none" stroke="#C0392B" '
          'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>')
    b += label(55, -24, "attacked", 11, cls="fig-step")
    g = '<g transform="translate(112,0)">'
    x, y = axial(0, 0)
    g += prism(x, y, "plains")
    g += unit(x, y, "you", 1)
    g += label(x, y + 46, "unit survives", 11, cls="fig-strong")
    g += label(x, y - 34, "gold spent", 11)
    g += '</g>'
    b += g
    return svg(0, 0, b, vb="auto")

F["fortify"] = fortify()

# ------------------------------------------------------- market 3x3 grid
def market():
    """One shuffled upgrade deck and a 3x3 grid of stacks (v0.22 §10).

    Replaces the v0.21 figure, which drew four per-suit ladders — a market that
    no longer exists. What the picture has to carry now is the three things
    players get wrong: the grid is ranks not suits, positions STACK when you
    draw onto them, and the RANK CAP hides the tall cards from a low tier.
    """
    b = ""
    cw, ch = 40, 56
    gx, gy = 16, 18
    CAP = 15                      # a Kingdom player is reading this figure
    # (rank, suit, how deep the stack is) — a fair spread of ranks 11-20
    grid = [(11, "plains", 1), (16, "forest", 2), (12, "ocean", 1),
            (18, "mountain", 3), (13, "plains", 1), (17, "ocean", 2),
            (15, "forest", 1), (14, "mountain", 2), (20, "plains", 1)]

    # the face-down upgrade deck, to the left
    dx, dy = -(cw + 46), ch + gy      # beside the middle row of three
    for d in range(4, 0, -1):
        b += (f'<rect x="{dx - d*2.0:.1f}" y="{dy - d*2.0:.1f}" width="{cw}" '
              f'height="{ch}" rx="4" fill="#E4E0D6" stroke="#8A837A" '
              f'stroke-width="1.1"/>')
    b += label(dx + cw / 2, dy + ch + 16, "one deck,", 11, cls="fig-step")
    b += label(dx + cw / 2, dy + ch + 30, "all suits shuffled", 11, cls="fig-step")
    # arrow: draw onto ANY position
    ax = dx + cw + 12
    b += (f'<path d="M{ax:.0f} {dy + ch/2:.0f} l24 0 M{ax + 19:.0f} '
          f'{dy + ch/2 - 5:.0f} l6 5 l-6 5" fill="none" stroke="#8A837A" '
          f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')

    for i, (rank, suit, depth) in enumerate(grid):
        col, row = i % 3, i // 3
        x, y = col * (cw + gx), row * (ch + gy + 14)
        # buried cards peek out behind the top one
        for d in range(depth - 1, 0, -1):
            b += (f'<rect x="{x + d*3.0:.1f}" y="{y - d*3.0:.1f}" width="{cw}" '
                  f'height="{ch}" rx="4" fill="#EDE9DF" stroke="#8A837A" '
                  f'stroke-width="1.1"/>')
        b += card(x, y, rank, suit, w=cw, h=ch, faded=rank > CAP)
        if rank > CAP:            # out of reach of this tier
            b += (f'<line x1="{x + 6:.1f}" y1="{y + 6:.1f}" '
                  f'x2="{x + cw - 6:.1f}" y2="{y + ch - 6:.1f}" '
                  f'stroke="#B0433A" stroke-width="2.2" stroke-linecap="round"/>')
        if depth > 1:
            b += label(x + cw / 2, y + ch + 13, f"{depth} deep", 10,
                       cls="fig-step")

    total_w = 3 * cw + 2 * gx
    total_h = 3 * ch + 2 * (gy + 14)
    b += label(total_w / 2, total_h + 30,
               f"your rank cap is {CAP}: the taller cards are visible, not buyable",
               11, cls="fig-step")
    b += label(total_w / 2, total_h + 46,
               "draw onto any position you like — burying what is under it",
               11, cls="fig-step")
    return svg(0, 0, b, vb="auto")

F["market"] = market()

# ------------------------------------------------------- player board
def board():
    b = ""
    PAD = 20
    W = 520
    # column anchors
    chip_x = PAD + 6
    name_x = chip_x + 34
    slots_x0 = name_x + 74          # unit slots start here
    feed_x = W - PAD - 116          # feed coin column
    moves_x = W - PAD - 52          # free-move column

    # ---- header ----
    y = PAD + 4
    b += label(PAD, y, "RESERVE", 12, anchor="start", cls="fig-step")
    b += label(feed_x, y, "FOOD", 11, anchor="start", cls="fig-step")
    b += label(moves_x, y, "MOVES", 11, anchor="start", cls="fig-step")
    b += label(slots_x0, y, "empty from the top band down",
               9.5, anchor="start", cls="fig-label")

    # (label, meld limit, units, food coins, free moves) — units are 2/3/5/5/5
    # as of v0.23. This figure had its own copy of the column and kept the v0.22
    # numbers when the table beside it changed, so the caption contradicted the
    # rulebook it illustrates. check_rules now reads the figure too.
    bands = [("Tribe", 2, 2, 0, 1),
             ("Settlement", 3, 3, 1, 2),
             ("Kingdom", 4, 5, 2, 3),
             ("Empire", 5, 5, 3, 4),
             ("Civilization", 6, 5, 4, 5)]
    # Tribe spent, Settlement half-emptied — the state the caption describes.
    filled_state = {0: 0, 1: 2, 2: 5, 3: 5, 4: 5}

    band_h = 46
    y = PAD + 18
    ur = 9                 # unit ellipse radius x
    ustep = 2 * ur + 6
    for i, (name, limit, n, coins, moves) in enumerate(bands):
        cy = y + band_h / 2
        b += (f'<rect x="{PAD}" y="{y}" width="{W-2*PAD}" height="{band_h-8}" rx="6" '
              f'fill="{"#F4F1E9" if i % 2 else "#E7E3D8"}" stroke="#CDC7B8" '
              f'stroke-width="1"/>')
        by = y + (band_h - 8) / 2
        # meld-limit chip
        b += (f'<rect x="{chip_x}" y="{by-14}" width="26" height="28" rx="3.5" '
              f'fill="#FBFAF6" stroke="#2A2E2B" stroke-width="1.4"/>')
        b += label(chip_x + 13, by + 2, str(limit), 15, cls="fig-strong")
        b += label(chip_x + 13, by + 12, "cards", 6.5, cls="fig-label")
        # name + unit count, stacked, left of the slots
        b += label(name_x, by - 3, name, 11, anchor="start", cls="fig-step")
        b += label(name_x, by + 9, f"{n} units", 8, anchor="start", cls="fig-label")
        # unit slots
        present = filled_state[i]
        for k in range(n):
            ux = slots_x0 + ur + k * ustep
            if k < present:
                b += (f'<ellipse cx="{ux}" cy="{by+2}" rx="{ur}" ry="{ur*0.5:.0f}" fill="#7B2018"/>'
                      f'<ellipse cx="{ux}" cy="{by}" rx="{ur}" ry="{ur*0.5:.0f}" fill="#C0392B" '
                      f'stroke="#7B2018" stroke-width="1.1"/>')
            else:
                b += (f'<ellipse cx="{ux}" cy="{by}" rx="{ur}" ry="{ur*0.5:.0f}" fill="none" '
                      f'stroke="#B4AFA3" stroke-width="1.3" stroke-dasharray="3 3"/>')
        # feed coins
        if coins:
            for c in range(coins):
                b += gold(feed_x + 8 + c * 17, by)
        else:
            b += label(feed_x + 8, by + 3, "free", 9, anchor="start", cls="fig-label")
        # free-move chip
        b += (f'<rect x="{moves_x + 4}" y="{by-11}" width="20" height="22" rx="3" '
              f'fill="#FBFAF6" stroke="#8A837A" stroke-width="1.2"/>')
        b += label(moves_x + 14, by + 3, str(moves), 12, cls="fig-strong")
        y += band_h

    # ---- upkeep note, its own full-width line ----
    y += 6
    b += label(PAD, y, "Each recycle your people eat your current tier's coins "
               "only \u2014 food is not cumulative.", 8.5, anchor="start",
               cls="fig-label")
    y += 13
    b += label(PAD, y, "Free moves refresh every turn.", 8.5, anchor="start",
               cls="fig-label")

    # ---- GOLD row ----
    y += 24
    b += label(PAD, y, "GOLD", 11, anchor="start", cls="fig-step")
    for k in range(6):
        b += gold(PAD + 58 + k * 18, y - 4)

    # ---- VP row, its own line ----
    y += 30
    b += label(PAD, y, "VICTORY ROW", 10, anchor="start", cls="fig-step")
    vpx = PAD + 92
    for k in range(5):
        b += (f'<rect x="{vpx + k*34}" y="{y-15}" width="30" height="22" rx="2.5" '
              f'fill="#FBFAF6" stroke="#8A837A" stroke-width="1.2"/>')

    # ---- outer frame drawn last, sized to content ----
    total_h = y + 16
    frame = (f'<rect x="{PAD-12}" y="{PAD-14}" width="{W-2*PAD+24}" '
             f'height="{total_h-PAD+14}" rx="12" fill="#EDEAE1" '
             f'stroke="#2A2E2B" stroke-width="2"/>')
    return svg(0, 0, frame + b, vb="auto")

def vprow():
    """Two right-aligned VP rows: 3 cards vs 5 cards, centre slot highlighted."""
    b = ""
    W = 460
    slot_w, slot_h, sgap = 42, 60, 6
    row_w = 5 * slot_w + 4 * sgap

    def draw_row(x0, y0, cards, title):
        nonlocal b
        n = len(cards)
        cards_sorted = sorted(cards)
        # right-align: empty slots on the left
        slots = [None] * (5 - n) + cards_sorted
        b_local = ""
        for i in range(5):
            sx = x0 + i * (slot_w + sgap)
            is_centre = (i == 2)
            # slot backing
            if is_centre:
                b_local += (f'<rect x="{sx-3}" y="{y0-3}" width="{slot_w+6}" '
                            f'height="{slot_h+6}" rx="6" fill="#D2A93A" opacity="0.30"/>')
            if slots[i] is None:
                b_local += (f'<rect x="{sx}" y="{y0}" width="{slot_w}" height="{slot_h}" '
                            f'rx="4" fill="none" stroke="#B4AFA3" stroke-width="1.3" '
                            f'stroke-dasharray="4 4"/>')
            else:
                rank, suit = slots[i]
                b_local += card(sx, y0, rank, suit, w=slot_w, h=slot_h)
                if is_centre:
                    b_local += (f'<circle cx="{sx+slot_w/2:.0f}" cy="{y0+slot_h+13:.0f}" '
                                f'r="11" fill="#7B2018"/>'
                                f'<text x="{sx+slot_w/2:.0f}" y="{y0+slot_h+17:.0f}" '
                                f'text-anchor="middle" fill="#FBFAF6" font-size="13" '
                                f'font-weight="700">{rank}</text>')
        # title + centre-slot label
        b_local += label(x0 + row_w/2, y0 - 12, title, 11, cls="fig-step")
        b += b_local

    # left: three cards -> centre slot is the LOW card
    draw_row(0, 30, [(3, "ocean"), (9, "forest"), (15, "plains")],
             "Three cards \u2014 3 + centre slot 3 = 6")
    # divider
    b += (f'<line x1="{row_w+24}" y1="18" x2="{row_w+24}" y2="{30+slot_h+30}" '
          f'stroke="#CDC7B8" stroke-width="1.2"/>')
    # right: five cards -> centre slot is the MEDIAN
    draw_row(row_w + 48, 30, [(3, "ocean"), (7, "mountain"), (11, "forest"),
                              (14, "plains"), (18, "ocean")],
             "Five cards \u2014 5 + centre slot 11 = 16")

    return svg(0, 0, b, vb="auto")

F["vprow"] = vprow()

F["board"] = board()

# ------------------------------------------------------- shift / amoeba
# ------------------------------------------- pattern freedom (v0.19)
def _panel(groups, gap=40, cap_pad=34):
    """groups: list of (title, [(col,row,terrain,badge,who|None)]).
    Lays panels left-to-right, captions on a shared baseline."""
    b = ""
    ox = 0.0
    heights = []
    for _, cells in groups:
        ys = [axial(c, r)[1] for c, r, t, _, _ in cells]
        hs = [TER[t]["h"] for _, _, t, _, _ in cells]
        heights.append(max(ys) - min(ys) + R + max(hs))
    base = max(heights) + cap_pad
    for (title, cells), _h in zip(groups, heights):
        xs = [axial(c, r)[0] for c, r, _, _, _ in cells]
        ys = [axial(c, r)[1] for c, r, _, _, _ in cells]
        w = (max(xs) - min(xs)) + 2 * SQ
        b += f'<g transform="translate({ox - min(xs) + SQ:.2f},{-min(ys):.2f})">'
        for c, r, ter, badge, who in sorted(cells, key=lambda t: (t[1], t[0])):
            x, y = axial(c, r)
            b += prism(x, y, ter)
            if who:
                b += unit(x, y, who, 1)
            if badge:
                b += (f'<circle cx="{x:.1f}" cy="{y-R-4:.1f}" r="8" fill="#FBFAF6" '
                      f'stroke="#8A837A" stroke-width="1.2"/>')
                b += label(x, y - R - 1, badge, 10, cls="fig-step")
        b += "</g>"
        b += label(ox + w / 2, base, title, 11, cls="fig-strong")
        ox += w + gap
    total = ox - gap
    vb = f"-6 {-R - 26:.0f} {total + 12:.0f} {base + R + 44:.0f}"
    return svg(0, 0, b, vb=vb)


# ------------------------------------------- starting maps (v0.20)
def setup_maps():
    """One Mountain per player in a block, one Plains per player around it.

    Every start is 3 hexes from every other, so an opening meld of two cannot
    reach a rival's homeland. Verified: min pairwise distance 3, every player
    bordering exactly one Mountain."""
    PLAYER["fourth"] = {"fill": "#7A4E9B", "edge": "#4C2F63"}
    M, P = "mountain", "plains"
    who = ["you", "rival", "third", "fourth"]
    LAYOUTS = [
        ("2 players", [(1, 0), (2, 0)], [(0, 0), (3, 0)]),
        ("3 players", [(1, 3), (2, 2), (2, 3)], [(0, 3), (2, 1), (3, 4)]),
        ("4 players", [(1, 2), (2, 2), (2, 3), (3, 3)],
                      [(0, 2), (2, 1), (2, 4), (4, 3)]),
    ]
    groups = []
    for title, mts, pls in LAYOUTS:
        cells = [(c, r, M, "", None) for c, r in mts]
        cells += [(c, r, P, "", who[i]) for i, (c, r) in enumerate(pls)]
        groups.append((title, cells))
    return _panel(groups, gap=16)


F["setup_maps"] = setup_maps()


if __name__ == "__main__":
    import json, pathlib
    pathlib.Path("figs.json").write_text(json.dumps(F))
    print("figures:", ", ".join(F))
