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


# ------------------------------------------------------- the whole table
def table():
    """What the table looks like, from YOUR seat.

    The first thing anyone opening a rulebook wants is a photograph of the game
    set up, and this book had every component drawn separately and none of them
    together — so a reader could learn what a player board is without ever
    learning where it sits.

    Drawn from one seat rather than from above, because that is the view a
    player actually has: your own board near, the shared middle at arm's
    length, rivals across the table with their hands hidden. It is schematic on
    purpose. Anything drawn to look like a photograph invites the reader to
    count pips and units, and every one of those numbers is a hostage.
    """
    b = ""
    INK, SOFT, LINE = "#2A2E2B", "#6B6F68", "#CDC7B8"

    def panel(x, y, w, h, title, sub=None):
        out = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" '
               f'fill="none" stroke="{LINE}" stroke-width="1.2" '
               f'stroke-dasharray="4 3"/>')
        out += label(x + w / 2, y - 6, title, 10, cls="fig-step")
        if sub:
            out += label(x + w / 2, y + h + 13, sub, 9.5, cls="fig-label")
        return out

    def facedown(x, y, w=17, h=24, n=1):
        out = ""
        for i in range(n):
            ox = x + i * 4
            out += (f'<rect x="{ox}" y="{y - i * 2}" width="{w}" height="{h}" rx="2.5" '
                    f'fill="#8A837A" stroke="#5A544C" stroke-width="1"/>')
        return out

    def faceup(x, y, rank, suit, w=17, h=24):
        c = TER[suit]["top"]
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2.5" '
                f'fill="#FBFAF6" stroke="{INK}" stroke-width="1"/>'
                f'<rect x="{x}" y="{y}" width="{w}" height="4" rx="2" fill="{c}"/>'
                + label(x + w / 2, y + h / 2 + h * 0.13,
                        str(rank), max(10.0, h * 0.36), cls="fig-strong"))

    def fancard(x, y, rank, suit, w, h):
        """A card whose rank sits where a fanned card still shows it.

        A hand in a figure had been drawn as a row of separate upright cards,
        which is how cards look on a table and not how they look in a hand. In a
        fan the middle of every card but the last is covered, so the rank moves
        off the centre and into the upper left, exactly where a real card puts
        its index and for the same reason.
        """
        c = TER[suit]["top"]
        out = (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="4" '
               f'fill="#FBFAF6" stroke="{INK}" stroke-width="1.3"/>')
        out += (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="7" rx="3.5" '
                f'fill="{c}"/>')
        out += f'<rect x="{x:.1f}" y="{y + 4:.1f}" width="{w}" height="3" fill="{c}"/>'
        out += label(x + w * 0.30, y + h * 0.44, str(rank), h * 0.30, cls="fig-strong")
        return out

    def fan(cx, y, items, w, h, spread, hidden=False):
        """Cards on an arc, rotated about a pivot below the hand.

        Every card is drawn at the same place and only the rotation separates
        them, so the spacing is an angle rather than a number to keep in step
        with the card width."""
        out = ""
        n = len(items)
        piv_y = y + h * 3.0
        for i, it in enumerate(items):
            a = (i - (n - 1) / 2) * spread
            out += f'<g transform="rotate({a:.2f} {cx:.1f} {piv_y:.1f})">'
            if hidden:
                out += (f'<rect x="{cx - w / 2:.1f}" y="{y:.1f}" width="{w}" '
                        f'height="{h}" rx="4" fill="#8A837A" stroke="#5A544C" '
                        f'stroke-width="1.2"/>')
            else:
                out += fancard(cx - w / 2, y, it[0], it[1], w, h)
            out += "</g>"
        return out

    def die(x, y, n, winner=False):
        f = "#C0392B" if winner else "#FBFAF6"
        t = "#FBFAF6" if winner else INK
        return (f'<rect x="{x}" y="{y}" width="22" height="22" rx="4" fill="{f}" '
                f'stroke="{"#7B2018" if winner else INK}" stroke-width="1.4"/>'
                f'<text x="{x + 11:.1f}" y="{y + 16:.1f}" text-anchor="middle" '
                f'font-size="13" fill="{t}" class="fig-strong">{n}</text>')

    def seat(x, y, w, who, name, row_filled, hidden):
        """A rival across the table: colour, victory row, a hidden hand."""
        p = PLAYER[who]
        out = (f'<rect x="{x}" y="{y}" width="{w}" height="42" rx="5" '
               f'fill="#F4F1E9" stroke="{LINE}" stroke-width="1"/>')
        out += (f'<circle cx="{x + 15:.1f}" cy="{y + 21:.1f}" r="9" fill="{p["fill"]}" '
                f'stroke="{p["edge"]}" stroke-width="1.2"/>')
        out += label(x + 30, y + 25, name, 9.5, anchor="start", cls="fig-step")
        sx = x + 68
        for i in range(5):
            fill = "#FBFAF6" if i >= 5 - row_filled else "#FBFAF6"
            out += (f'<rect x="{sx + i * 19}" y="{y + 8}" width="17" height="26" rx="2.5" '
                    f'fill="{fill}" stroke="{LINE}" stroke-width="1"'
                    + ('' if i >= 5 - row_filled else ' stroke-dasharray="2 2"') + '/>')
            if i >= 5 - row_filled:
                out += (f'<rect x="{sx + i * 19}" y="{y + 8}" width="17" height="4.5" '
                        f'rx="2" fill="{TER["plains"]["top"]}"/>')
        # BELOW the strip, not inside it: at 9.5 the caption reached the slot
        # boxes it names. The strip is 34 tall, so this clears it by 8.
        out += label(sx + 47, y + 50, "victory row", 9.5, cls="fig-label")
        # Their hand is held too, and hidden: a fan of backs says both at once,
        # where a neat stack read as a draw pile sitting on the table.
        out += fan(x + w - 34, y + 5, [None] * hidden, 20, 30, 13, hidden=True)
        return out

    # ---------------------------------------------------------- rivals, far
    b += seat(40, 0, 258, "rival", "Bex", 2, 3)
    b += seat(322, 0, 258, "third", "Cy", 1, 3)

    # ---------------------------------------------------------- the middle
    # the map: a small grown cluster, three colours on it
    map_x, map_y = 250, 118
    layout = [(0, 0, "plains"), (1, 0, "forest"), (2, 0, "mountain"),
              (-1, 1, "ocean"), (0, 1, "plains"), (1, 1, "mountain"), (2, 1, "forest"),
              (0, 2, "ocean"), (1, 2, "plains"), (2, 2, "plains")]
    units = {(0, 0): ("you", 2), (0, 1): ("you", 1), (1, 2): ("you", 1),
             (1, 0): ("rival", 1), (2, 1): ("rival", 2), (2, 0): ("third", 1),
             (2, 2): ("third", 1)}
    for col, row, ter in sorted(layout, key=lambda t: (t[1], t[0])):
        x, y = axial(col, row)
        b += prism(map_x + x, map_y + y, ter)
        if (col, row) in units:
            who, n = units[(col, row)]
            b += unit(map_x + x, map_y + y, who, n)
    x, y = axial(3, 1)
    b += prism(map_x + x, map_y + y, None, empty=True, dashed=True)
    b += label(map_x + 55, map_y - 42, "THE MAP", 11, cls="fig-strong")
    b += label(map_x + 55, map_y - 29, "shared, and it grows", 9.5, cls="fig-label")

    # the market: deck plus 3x3, to the left of the map
    mk_x, mk_y = 40, 92
    b += panel(mk_x - 10, mk_y - 10, 150, 132, "MARKET",
               "nine face up \u00b7 buy at or under your rank cap")
    b += facedown(mk_x, mk_y + 40, 28, 38, 3)
    b += label(mk_x + 18, mk_y + 96, "upgrade", 9.5, cls="fig-label")
    b += label(mk_x + 18, mk_y + 106, "deck", 9.5, cls="fig-label")
    grid = [(11, "plains"), (16, "ocean"), (12, "forest"),
            (18, "mountain"), (13, "plains"), (17, "ocean"),
            (15, "forest"), (14, "mountain"), (20, "plains")]
    for i, (rank, suit) in enumerate(grid):
        gx = mk_x + 50 + (i % 3) * 28
        gy = mk_y + (i // 3) * 38
        b += faceup(gx, gy, rank, suit, 24, 33)

    # the tile supply: four open piles, right of the map
    sp_x, sp_y = 468, 92
    b += panel(sp_x - 14, sp_y - 14, 124, 150, "TILE SUPPLY",
               "open \u2014 no bag, nothing hidden")
    # Two columns, and the row gap is set by the TALLEST prism rather than by a
    # flat number: Mountain stands three layers and overlapped the pile beneath
    # it when this was spaced evenly.
    drop = R + TER["mountain"]["h"] + 22
    for i, ter in enumerate(("plains", "forest", "ocean", "mountain")):
        px = sp_x + 28 + (i % 2) * 56
        py = sp_y + 16 + (i // 2) * drop
        b += prism(px, py, ter)

    # the play area: the melds and the dice, below the map
    pa_x, pa_y = 178, 268
    b += panel(pa_x - 12, pa_y - 12, 336, 88, "PLAY AREA",
               "every meld stays here until it is spent")
    melds = [("you", [(5, "plains"), (6, "plains")]),
             ("rival", [(8, "mountain"), (8, "ocean")]),
             ("third", [(4, "mountain")])]
    mx = pa_x
    for who, cards in melds:
        p = PLAYER[who]
        b += (f'<circle cx="{mx + 8:.1f}" cy="{pa_y + 6:.1f}" r="5" fill="{p["fill"]}" '
              f'stroke="{p["edge"]}" stroke-width="1.1"/>')
        for j, (rank, suit) in enumerate(cards):
            b += faceup(mx + j * 26, pa_y + 16, rank, suit, 24, 33)
        mx += max(2, len(cards)) * 26 + 28
    b += die(pa_x + 236, pa_y + 20, 2, winner=True)
    b += die(pa_x + 262, pa_y + 20, 2)
    b += die(pa_x + 288, pa_y + 20, 3)
    # Centred on the dice would push the right end of this caption through the
    # PLAY AREA border, which sits at pa_x + 288. Centred to fit instead.
    b += label(pa_x + 250, pa_y + 64, "dice \u2014 the coloured one led", 9.5, cls="fig-label")

    # the shared pile and the coin supply
    b += facedown(96, 296, 22, 30, 2)
    b += label(110, 338, "shared pile", 9.5, cls="fig-label")
    b += gold(544, 296)
    b += gold(562, 302)
    b += gold(552, 312)
    b += label(554, 336, "gold supply", 9.5, cls="fig-label")

    # ---------------------------------------------------------- your seat
    yx, yy, yw = 96, 376, 476
    b += (f'<rect x="{yx}" y="{yy}" width="{yw}" height="72" rx="7" fill="#F4F1E9" '
          f'stroke="{LINE}" stroke-width="1.2"/>')
    b += (f'<circle cx="{yx + 22:.1f}" cy="{yy + 24:.1f}" r="9" '
          f'fill="{PLAYER["you"]["fill"]}" stroke="{PLAYER["you"]["edge"]}" '
          f'stroke-width="1.3"/>')
    b += label(yx + 40, yy + 30, "YOUR BOARD", 10, anchor="start", cls="fig-strong")
    b += label(yx + 205, yy + 9, "RESERVE", 9.5, cls="fig-step")
    b += label(yx + 337, yy + 9, "VICTORY ROW", 9.5, cls="fig-step")
    b += label(yx + 436, yy + 9, "GOLD", 9.5, cls="fig-step")
    # The reserve: five tiers of EQUAL size, the emptied ones hollow. Drawn with
    # growing heights at first, which read as a bar chart of something and made
    # the leftmost tiers look small rather than spent.
    for i in range(5):
        rx = yx + 152 + i * 22
        spent = i < 2
        b += (f'<rect x="{rx}" y="{yy + 17}" width="18" height="28" rx="2.5" '
              f'fill="{"#FBFAF6" if spent else PLAYER["you"]["fill"]}" '
              f'stroke="{PLAYER["you"]["edge"]}" stroke-width="1.1"'
              + (' stroke-dasharray="2 2"' if spent else '') + '/>')

    for i in range(5):
        vx = yx + 294 + i * 22
        filled = i >= 2
        b += (f'<rect x="{vx}" y="{yy + 14}" width="18" height="28" rx="2.5" '
              f'fill="#FBFAF6" stroke="{LINE}" stroke-width="1"'
              + ('' if filled else ' stroke-dasharray="2 2"') + '/>')
        if filled:
            b += (f'<rect x="{vx}" y="{yy + 17}" width="18" height="5" rx="2" '
                  f'fill="{TER["forest"]["top"]}"/>')
    b += label(yx + 294, yy + 64,
               "tiers empty from the top \u00b7 the row fills from the right",
               9.5, cls="fig-label")
    b += gold(yx + 436, yy + 32)

    # your hand, face up, nearest of all
    # EIGHT cards, not ten: the 5 and 6 of Plains are sitting in the play area
    # above, and a figure that says ten while showing a meld already played
    # teaches the one thing about the hand that matters wrongly.
    # A HAND WITH SOMETHING IN IT. The old eight were 2,3,7,9,9,11,14,17, whose
    # longest legal meld is TWO — checked against enumerateMelds, not guessed. A
    # setup figure showing a hand you could do nothing with teaches the meld rule
    # backwards. These eight hold, in the engine's own enumeration:
    #
    #   four   1-2-3-4
    #   three  1-2-3 · 2-3-4 · 9-9-10
    #   two    1-2 · 2-3 · 3-4 · 9-9 · 9-10
    #   and 17 alone, which is what a high card is for — cash it, or attack.
    #
    # The run of four deliberately spans all four suits: melds do not care about
    # suit, and a reader who sees a run in one colour will assume they do. The
    # 9-9-10 is there because duplicates are free and nothing else says so.
    hand = [(1, "ocean"), (2, "mountain"), (3, "plains"), (4, "forest"),
            (9, "ocean"), (9, "plains"), (10, "mountain"), (17, "forest")]
    b += fan(yx + yw / 2, yy + 92, hand, 52, 72, 8.6)
    b += label(yx + yw / 2, yy + 214,
               "YOUR HAND \u2014 eight left; the 5 and 6 are on the table",
               9.5, cls="fig-step")
    b += label(yx + yw / 2, yy + 228,
               "ten between your turns, and nobody else ever sees it",
               9.5, cls="fig-label")
    return svg(0, 0, b, vb="auto")


F["table"] = table()


# ------------------------------------------------- the worked round, in two
def trick():
    """Round one of the worked round: three melds, one comparison, three dice.

    The trick is the one moment where everybody acts at once, and prose has to
    walk it player by player. Drawn side by side it is a single glance: add
    each row, biggest wins, dice go out in order.
    """
    b = ""
    melds = [("you", "Ada", [(5, "plains"), (6, "plains")], 11, 2),
             ("rival", "Bex", [(8, "mountain"), (8, "ocean")], 16, 1),
             ("third", "Cy", [(4, "mountain")], 4, 3)]
    cw, ch = 40, 56
    x = 0
    for who, name, cards, total, place in melds:
        p = PLAYER[who]
        wide = max(2, len(cards)) * (cw + 6)
        cx = x + wide / 2 - 3
        b += (f'<circle cx="{x + 9:.1f}" cy="{8:.1f}" r="7" fill="{p["fill"]}" '
              f'stroke="{p["edge"]}" stroke-width="1.2"/>')
        b += label(x + 22, 12, name, 11, anchor="start", cls="fig-step")
        for j, (rank, suit) in enumerate(cards):
            b += card(x + j * (cw + 6), 22, rank, suit, w=cw, h=ch)
        sums = (" + ".join(str(r) for r, _ in cards) + f" = {total}"
                if len(cards) > 1 else str(total))
        b += label(cx, 22 + ch + 18, sums, 13,
                   cls="fig-strong" if place == 1 else "fig-label")
        # the die each one takes: the winner's die is the coloured one, and it
        # shows the MELD SIZE, not the placing — the single thing about the
        # dice that readers get wrong
        dx = cx - 8.5
        dy = 22 + ch + 30
        if place == 1:
            b += (f'<rect x="{dx}" y="{dy}" width="17" height="17" rx="3.5" '
                  f'fill="#C0392B" stroke="#7B2018" stroke-width="1.3"/>'
                  f'<text x="{dx + 8.5:.1f}" y="{dy + 12.5:.1f}" text-anchor="middle" '
                  f'font-size="10.5" fill="#FBFAF6" class="fig-strong">2</text>')
            b += label(cx, dy + 30, "winner\u2019s die: her meld", 8, cls="fig-attack")
            b += label(cx, dy + 40, "was 2 cards. Leads next.", 8, cls="fig-attack")
        else:
            b += (f'<rect x="{dx}" y="{dy}" width="17" height="17" rx="3.5" '
                  f'fill="#FBFAF6" stroke="#2A2E2B" stroke-width="1.3"/>'
                  f'<text x="{dx + 8.5:.1f}" y="{dy + 12.5:.1f}" text-anchor="middle" '
                  f'font-size="10.5" class="fig-strong">{place}</text>')
            b += label(cx, dy + 30, f"{place}{'nd' if place == 2 else 'rd'} to spend",
                       8, cls="fig-label")
        x += wide + 34
    b += label((x - 34) / 2, 22 + ch + 100,
               "Highest TOTAL takes the trick \u2014 one big card beats two small ones.",
               11, cls="fig-strong")
    b += label((x - 34) / 2, 22 + ch + 115,
               "Ada matched Bex\u2019s two cards and lost, so one of hers is set aside "
               "for a coin.", 9, cls="fig-label")
    return svg(0, 0, b, vb="auto")


F["trick"] = trick()


def worked_map():
    """The map at the end of that same round, so a reader can check their own.

    THE LAYOUT IS THE REAL ONE. The first draft of this drew three Mountains in
    a row, and the text three lines above it says they sit in a triangle with a
    Plains beyond each outer face — a figure quietly contradicting the section
    it illustrates, which is the exact fault that had the combat figure showing
    a gold coin for a version. The cells below are the engine's STARTS[3], the
    same ones setup_maps draws, plus the one Ocean tile Bex explored.
    """
    b = ""
    MTS = [(1, 3), (2, 2), (2, 3)]
    PLS = [(0, 3), (2, 1), (3, 4)]          # Ada, Bex, Cy in seat order
    NEW = (1, 2)                            # the Ocean Bex laid this round
    cells = ([(c, r, "mountain") for c, r in MTS]
             + [(c, r, "plains") for c, r in PLS]
             + [(NEW[0], NEW[1], "ocean")])
    for col, row, ter in sorted(cells, key=lambda t: (t[1], t[0])):
        x, y = axial(col, row)
        b += prism(x, y, ter)
    # Bex settled the Mountain at (2,2) and still holds her Plains
    for (col, row), (who, n) in {PLS[0]: ("you", 2), PLS[1]: ("rival", 1),
                                 PLS[2]: ("third", 1), (2, 2): ("rival", 1)}.items():
        x, y = axial(col, row)
        b += unit(x, y, who, n)
    # call the new tile out with a leader line rather than a badge sitting on
    # the tile above it
    nx, ny = axial(*NEW)
    b += (f'<path d="M{nx - 34:.1f} {ny - 46:.1f} L{nx - 8:.1f} {ny - 20:.1f}" '
          f'fill="none" stroke="#C0392B" stroke-width="1.6" stroke-linecap="round"/>')
    b += label(nx - 38, ny - 50, "Bex explored this", 9, anchor="end",
               cls="fig-attack")
    xs = [axial(c, r)[0] for c, r, _ in cells]
    ys = [axial(c, r)[1] for c, r, _ in cells]
    b += label((min(xs) + max(xs)) / 2, max(ys) + R + 36,
               "After the map phase: Bex settled a Mountain and laid the Ocean;",
               10, cls="fig-strong")
    b += label((min(xs) + max(xs)) / 2, max(ys) + R + 51,
               "Ada put a second unit on her Plains; Cy cashed and kept his coins.",
               10, cls="fig-strong")
    return svg(0, 0, b, vb="auto")


F["worked_map"] = worked_map()


# ------------------------------------------------------- terrain, compared
def terrains():
    """What actually differs between the four terrains.

    The version this replaces printed a name, a capacity and a defence bonus
    under each tile, with "flat / 2 layers / 3 layers" above them — three of
    those four things being facts about the plastic rather than about the game.
    It also left out the single largest difference between one terrain and the
    others: Ocean is the only one with a rule of its own.

    So: four columns of the things a player compares, and a band underneath for
    the sea, which is not a column because it is not the same kind of fact.

    The defence row prints the bonus AND what it means in the hand. "+2" is the
    number in the rule; "beat them by 3" is the number you need when you are
    holding cards and deciding whether to try. A reader should not have to do
    that addition themselves at the table.
    """
    b = ""
    INK, SOFT, LINE, PANEL = "#2A2E2B", "#6B6F68", "#CDC7B8", "#F4F1E9"
    COL, GAP = 138, 12
    # Ordered by how hard they are to take, which is the order the rules table
    # uses and the order the numbers make sense in.
    cols = [
        ("plains", "Plains", 3, 0, "Room to grow.", "Three units fit \u2014 the only",
         "ground that stacks deep."),
        ("ocean", "Ocean", 1, 0, "A road, not a home.", "Holds one, and open water",
         "carries a unit any distance."),
        ("forest", "Forest", 2, 1, "Cover.", "Two units, and the trees are",
         "worth a rank in a fight."),
        ("mountain", "Mountain", 1, 2, "The hard ground.", "One unit, and the best",
         "defence in the game."),
    ]

    top = 0
    for i, (key, name, holds, bonus, head, l1, l2) in enumerate(cols):
        x = i * (COL + GAP)
        cx = x + COL / 2
        b += (f'<rect x="{x}" y="{top}" width="{COL}" height="286" rx="8" '
              f'fill="{PANEL}" stroke="{LINE}" stroke-width="1.1"/>')
        # The tile sits on its own height, so the moulding reads at a glance —
        # but every LABEL below it is at a fixed y, shared across the four
        # columns. Hanging the name off the prism instead put Mountain's name
        # through the row beneath it, because Mountain is the tall one.
        b += prism(cx, top + 52, key)
        b += label(cx, top + 118, name, 13, cls="fig-strong")

        # HOLDS, drawn as the units themselves: a number you can count is a
        # number nobody has to trust
        b += label(cx, top + 136, "HOLDS", 9, cls="fig-step")
        span = (holds - 1) * 24
        for k in range(holds):
            b += unit(cx - span / 2 + k * 24, top + 152, "rival", 1)
        b += label(cx, top + 172, f"{holds} unit" + ("s" if holds > 1 else ""),
                   9, cls="fig-label")

        # DEFENCE, both ways round
        b += (f'<line x1="{x + 14}" y1="{top + 182}" x2="{x + COL - 14}" '
              f'y2="{top + 182}" stroke="{LINE}" stroke-width="1"/>')
        b += label(cx, top + 196, "DEFENCE", 9, cls="fig-step")
        b += label(cx, top + 216, f"+{bonus}", 17,
                   cls="fig-attack" if bonus else "fig-label")
        b += label(cx, top + 230, f"beat them by {bonus + 1}", 9, cls="fig-label")

        # what it is FOR
        b += (f'<line x1="{x + 14}" y1="{top + 240}" x2="{x + COL - 14}" '
              f'y2="{top + 240}" stroke="{LINE}" stroke-width="1"/>')
        b += label(cx, top + 254, head, 9.5, cls="fig-strong")
        b += label(cx, top + 266, l1, 9, cls="fig-label")
        b += label(cx, top + 276, l2, 9, cls="fig-label")

    # ---- the sea gets a band, because it is the one rule no other terrain has
    W = 4 * COL + 3 * GAP
    sy = 308
    b += (f'<rect x="0" y="{sy}" width="{W}" height="158" rx="8" fill="none" '
          f'stroke="{TER["ocean"]["side"]}" stroke-width="1.3" '
          f'stroke-dasharray="5 3"/>')
    b += label(20, sy + 22, "ONLY THE SEA DOES THIS", 10, anchor="start",
               cls="fig-step")
    b += label(200, sy + 22,
               "\u2014 the first sea move each turn also lays a tile, free",
               9, anchor="start", cls="fig-label")

    # a unit sailing across open water, then a tile of ANY terrain arriving
    ox, oy = 158, sy + 82
    for k in range(3):
        b += prism(ox + k * (DX + 2), oy, "ocean")
    b += unit(ox, oy, "you", 1)
    ay = oy - R - 12
    b += (f'<path d="M{ox:.1f} {ay:.1f} L{ox + 2 * DX + 2:.1f} {ay:.1f} '
          f'M{ox + 2 * DX - 8:.1f} {ay - 6:.1f} l10 6 l-10 6" '
          f'fill="none" stroke="#C0392B" stroke-width="2" stroke-linecap="round" '
          f'stroke-linejoin="round"/>')
    b += label(ox + DX, oy + R + 20, "sail as far as the open water reaches",
               9, cls="fig-label")

    nx = ox + 2 * (DX + 2) + 168
    b += (f'<path d="M{ox + 2 * DX + SQ + 14:.1f} {ay:.1f} L{nx - SQ - 10:.1f} '
          f'{ay:.1f} M{nx - SQ - 20:.1f} {ay - 6:.1f} l10 6 l-10 6" '
          f'fill="none" stroke="#C0392B" stroke-width="2" stroke-linecap="round" '
          f'stroke-linejoin="round"/>')
    # An empty dashed cell rather than a green one: the point is that you pick
    # the terrain, and drawing a Forest there says Forest.
    b += prism(nx, oy, None, empty=True, dashed=True)
    b += label(nx, oy + 4, "ANY", 11, cls="fig-attack")
    b += label(nx, oy + R + 20, "then lay a tile of ANY terrain,", 9,
               cls="fig-label")
    b += label(nx, oy + R + 31, "anywhere the map legally takes it", 9,
               cls="fig-label")
    b += label(nx, oy + R + 42, "\u2014 no card needed, once a turn", 9,
               cls="fig-label")
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
    """v0.24: an attack is a DUEL, and the figure has to show two hands, not a
    coin.

    The previous version drew a gold piece beside the struck tile and said "one
    defender removed — your unit stays in reserve". Both halves of that are now
    wrong: there is no coin price, and clearing the last defender takes the
    ground. A figure that teaches the replaced rule is worse than no figure,
    because it is the part of the page a reader believes without checking.

    Two rows rather than three beats across: a single line of card-card-tile
    overflowed the print column by 114px, and this is a DETAIL figure, so it is
    already drawn large.
    """
    cw, ch = 42, 58
    gap = 30
    b = ""

    # ---- row 1: the card you SPENT against a card from their HAND
    xa = 0
    xd = xa + cw + gap + 14
    b += card(xa, 12, 12, "plains", w=cw, h=ch)
    b += card(xd, 12, 9, "forest", w=cw, h=ch)
    b += label(xa + cw / 2, 4, "attack", 10, cls="fig-attack")
    b += label(xd + cw / 2, 4, "defence", 10, cls="fig-step")
    # WHERE each card comes from is the part players got wrong: the attacker
    # commits nothing extra, so an attack costs exactly what a settle costs.
    b += label(xa + cw / 2, ch + 42, "the card you spent", 8, cls="fig-label")
    b += label(xd + cw / 2, ch + 42, "one card from hand", 8, cls="fig-label")
    b += label((xa + cw + xd) / 2, 12 + ch / 2 + 8, "vs", 12, cls="fig-label")
    b += label(xa + cw / 2, 12 + ch + 18, "12", 13, cls="fig-strong")
    # the ground is on the DEFENDER's side of the sum, and that is the whole
    # point of the terrain: a bonus, not a toll
    b += label(xd + cw / 2, 12 + ch + 18, "9 + 1 = 10", 13, cls="fig-strong")
    b += label(xd + cw / 2, 12 + ch + 32, "Forest defends", 9, cls="fig-step")

    # ---- row 2: the ground changes hands
    centre = (xa + xd + cw) / 2
    ty = 12 + ch + 32 + 26 + R
    b += prism(centre, ty, "forest")
    b += unit(centre, ty, "you", 1)
    # the defender going home
    ax = centre + R + 6
    b += (f'<path d="M{ax:.1f} {ty - 8:.1f} l16 0 M{ax + 10:.1f} {ty - 13:.1f} '
          f'l6 5 l-6 5" fill="none" stroke="#C0392B" stroke-width="2.2" '
          f'stroke-linecap="round" stroke-linejoin="round"/>')
    b += label(ax + 20, ty - 12, "home", 9, anchor="start", cls="fig-attack")
    b += label(centre, ty + R + TER["forest"]["h"] + 17, "yours now", 10,
               cls="fig-step")
    b += label(centre, ty + R + TER["forest"]["h"] + 38,
               "Higher total wins \u2014 and clearing the LAST",
               11, cls="fig-strong")
    b += label(centre, ty + R + TER["forest"]["h"] + 53,
               "defender takes the ground.", 11, cls="fig-strong")
    return svg(0, 0, b, vb="auto")


F["combat"] = combat()

# ------------------------------------------------------- fortify
def fortify():
    """What a coin on a unit buys, now that it is a WALL.

    Three versions of this rule have now been drawn here. The first showed the
    coin absorbing an attack, which measured terribly — once bots learned that
    hitting a wall bought nothing, walls stopped being attacked at all. The
    second showed the assault: one card refused, two cards fighting with the
    lower of the pair. This one shows the wall, and the contrast that IS the
    rule — a card you were dealt bounces, a card you researched goes through.
    """
    b = ""
    cw, ch = 34, 48
    INK, SOFT, LINE = "#2A2E2B", "#6B6F68", "#CDC7B8"

    # ---- left: a starting-deck card bounces off
    b += label(52, -26, "DEALT", 10, cls="fig-step")
    b += card(0, -8, 9, "plains", w=cw, h=ch)
    b += (f'<path d="M{cw + 10} {ch / 2 - 8:.0f} l30 0 M{cw + 32} '
          f'{ch / 2 - 14:.0f} l6 6 l-6 6" fill="none" stroke="{SOFT}" '
          f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    bx, by = cw + 60, ch / 2 - 8
    b += (f'<circle cx="{bx}" cy="{by}" r="13" fill="none" stroke="#C0392B" '
          f'stroke-width="2.4"/>'
          f'<line x1="{bx - 9}" y1="{by + 9}" x2="{bx + 9}" y2="{by - 9}" '
          f'stroke="#C0392B" stroke-width="2.4" stroke-linecap="round"/>')
    b += label(bx, by + 34, "bounces", 10, cls="fig-attack")
    b += label(bx, by + 47, "9 under 10", 10, cls="fig-attack")

    # ---- the walled tile in the middle, and what it holds at
    tx, ty = 200, ch / 2 - 6
    b += prism(tx, ty, "plains")
    b += unit(tx, ty, "rival", 1)
    b += gold(tx, ty - 11)
    b += label(tx, ty + R + TER["plains"]["h"] + 18, "wall 10", 12,
               cls="fig-strong")
    b += label(tx, ty + R + TER["plains"]["h"] + 31, "a Tribe's tier", 9,
               cls="fig-label")

    # ---- right: a researched card goes through
    rx = 252
    b += label(rx + cw / 2, -26, "RESEARCHED", 10, cls="fig-step")
    b += (f'<path d="M{rx - 40} {ch / 2 - 8:.0f} l30 0 M{rx - 18} '
          f'{ch / 2 - 14:.0f} l6 6 l-6 6" fill="none" stroke="{SOFT}" '
          f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    b += card(rx, -8, 14, "plains", w=cw, h=ch)
    b += label(rx + cw / 2, ch + 12, "breaks it", 12, cls="fig-attack")
    b += label(rx + cw / 2, ch + 26, "14 over 10", 9, cls="fig-label")
    b += label(rx + cw / 2, ch + 39, "takes the ground", 9, cls="fig-label")

    b += label(160, ch + 96,
               "A wall holds at your tier's number \u2014 10 / 12 / 14 / 16 / 18,",
               11, cls="fig-strong")
    b += label(160, ch + 111,
               "two under the rank you may buy. It is a FLOOR:",
               11, cls="fig-strong")
    b += label(160, ch + 126,
               "a better card from hand fights instead.", 11, cls="fig-strong")
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
    CAP = 16                      # a Kingdom player is reading this figure
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
    # NOT a choice. The market used to let you bury whichever position you
    # liked; it now covers the HIGHEST rank showing, which is what makes the
    # step deterministic and the setup simple. A figure offering a decision the
    # rules do not have is the kind of error a reader never thinks to check.
    b += label(total_w / 2, total_h + 46,
               "a draw covers the highest rank showing \u2014 nobody chooses",
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
    wall_x = slots_x0 + 172         # the tier's wall, two under its rank cap
    feed_x = W - PAD - 116          # feed coin column
    moves_x = W - PAD - 52          # free-move column

    def shield(cx, cy, n):
        """A heater shield with the rank it holds at. Same glyph as the printed
        board, so a player who has seen one recognises the other."""
        w, h = 22.0, 24.0
        x0, y0 = cx - w / 2, cy - h / 2
        out = (f'<path d="M{x0:.1f} {y0:.1f} h{w:.1f} v{h*0.42:.1f} '
               f'q0 {h*0.40:.1f} {-w/2:.1f} {h*0.58:.1f} '
               f'q{-w/2:.1f} {-h*0.18:.1f} {-w/2:.1f} {-h*0.58:.1f} Z" '
               f'fill="#FBFAF6" stroke="#2A2E2B" stroke-width="1.2"/>')
        out += (f'<path d="M{x0:.1f} {y0 + h*0.26:.1f} h{w:.1f}" '
                f'stroke="#CDC7B8" stroke-width="0.8" fill="none"/>')
        out += label(cx, cy + 3, str(n), 12, cls="fig-strong")
        return out

    # ---- header ----
    y = PAD + 4
    b += label(PAD, y, "RESERVE", 12, anchor="start", cls="fig-step")
    b += label(wall_x, y, "WALL", 11, cls="fig-step")
    b += label(feed_x, y, "FOOD", 11, anchor="start", cls="fig-step")
    b += label(moves_x, y, "MOVES", 11, anchor="start", cls="fig-step")
    b += label(slots_x0, y, "empty from the top band down",
               9.5, anchor="start", cls="fig-label")

    # (label, meld limit, units, food coins, free moves) — units are 2/3/5/5/5
    # as of v0.23. This figure had its own copy of the column and kept the v0.22
    # numbers when the table beside it changed, so the caption contradicted the
    # rulebook it illustrates. check_rules now reads the figure too.
    # WALL is the rank cap less two (\u00a707): 12/14/16/18/20 minus 2. Written out
    # rather than computed so check_rules can read both numbers off this figure
    # and hold them against the engine, which is what caught this column being
    # absent from the figure while the printed board had it.
    bands = [("Tribe", 2, 2, 0, 1, 10),
             ("Settlement", 3, 3, 1, 2, 12),
             ("Kingdom", 4, 5, 2, 3, 14),
             ("Empire", 5, 5, 3, 4, 16),
             ("Civilization", 6, 5, 4, 5, 18)]
    # Tribe spent, Settlement half-emptied — the state the caption describes.
    filled_state = {0: 0, 1: 2, 2: 5, 3: 5, 4: 5}

    band_h = 46
    y = PAD + 18
    ur = 9                 # unit ellipse radius x
    ustep = 2 * ur + 6
    for i, (name, limit, n, coins, moves, wall) in enumerate(bands):
        cy = y + band_h / 2
        b += (f'<rect x="{PAD}" y="{y}" width="{W-2*PAD}" height="{band_h-8}" rx="6" '
              f'fill="{"#F4F1E9" if i % 2 else "#E7E3D8"}" stroke="#CDC7B8" '
              f'stroke-width="1"/>')
        by = y + (band_h - 8) / 2
        # meld-limit chip
        b += (f'<rect x="{chip_x}" y="{by-14}" width="26" height="28" rx="3.5" '
              f'fill="#FBFAF6" stroke="#2A2E2B" stroke-width="1.4"/>')
        b += label(chip_x + 13, by + 2, str(limit), 15, cls="fig-strong")
        b += label(chip_x + 13, by + 12, "cards", 8, cls="fig-label")
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
        # the wall this tier defends at
        b += shield(wall_x, by, wall)
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
