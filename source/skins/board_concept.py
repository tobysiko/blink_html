# -*- coding: utf-8 -*-
"""A player board rebuilt as a ladder — Lean economy, no food, no ascension.

The printed board is a table: five rows of five columns with the tiers as rows.
Nothing about reading it feels like climbing. This draws the tier track as what
it actually is — a staircase you ascend by emptying your reserve — and drops the
two columns the Lean configuration removes.

What went, and why:

  FOOD and ASCENSION are gone. `candidate-versions.md` measured them as a closed
  loop: ascension pays 26.5 a game, food takes 31.7 back, and in 6,913 recycles a
  player was short of the food owed 0.1% of the time. No unit was ever starved
  off the map. Removing them together takes two columns off the board and a
  recurring step out of the phase — the answer to "too complex" that Hans im
  Glück's note asks for.

  ON THE BOARD, the seven-line glossary, is gone. It is on the player aid.

What arrived:

  The staircase. Five blocks rising left to right, each holding the units that
  tier still owes you. Your tier is the leftmost block with units left in it, so
  position on the ladder is a silhouette, not a number to look up.

  Iconography instead of labels. Meld limit is little cards, moves are chevrons,
  the rank cap is a numeral in a card-shaped box. Each is named once, above the
  first step, and never repeated.

A4 landscape, millimetres. `board_a4.py` remains the source of truth for
geometry and for every number; this is a concept.
"""

import marks

PW, PH, M = 297.0, 210.0, 14.0

INK, SOFT, FAINT = "#26302C", "#6B6F68", "#B9B4A8"
PAPER, LINE = "#FCFBF7", "#CDC7B8"
GOLD, GOLDl, GOLDd = "#C9992B", "#F0E2B4", "#8A6A18"

# Tribe → Civilization: parchment warming into a cold horizon, the card back's
# past-to-future axis stood on end.
WASH = ["#F2E5C8", "#EBE3CB", "#E0E1D3", "#D3DDDA", "#C6DAE4"]
PIP = ["#A98A3A", "#95873F", "#77855F", "#55808F", "#2F7C9E"]

# label, meld limit, units owed, free moves, rank cap, WALL
# The wall is the cap less two — board_a4.py's WALL_OFFSET, and build_aid.py
# prints the same 10/12/14/16/18. It is what a fortified unit defends at, so it
# belongs beside the cap: both are ranks, and the pair is always two apart.
BANDS = [
    ("Tribe",        2, 2, 1, "12", "10"),
    ("Settlement",   3, 3, 2, "14", "12"),
    ("Kingdom",      4, 5, 3, "16", "14"),
    ("Empire",       5, 5, 4, "18", "16"),
    ("Civilization", 6, 5, 5, "20", "18"),
]

# Poker, 2.5 x 3.5 in — the same stock the deck prints on.
CARD_W, CARD_H = 63.5, 88.9
# How much of a card the board reveals when it is slid home. board_a4.py uses
# 16 mm; face.py's index zone is 16 mm too, and its contents end at about
# 15.4 mm, so 16 leaves half a millimetre for a human hand. 18 gives 2.5 mm of
# slack and still reads as a strip rather than as a card.
VROW_REVEAL = 18.0

SUITS = ("plains", "forest", "ocean", "mountain")
HOLDS = {"plains": 3, "forest": 2, "ocean": 1, "mountain": 1}
# The ground bonus is added to the DEFENDER, not the attacker — build_aid.py
# prints it as "+1 defence" / "+2 defence". The first pass of this board headed
# the column "attack", which is the opposite of what the number does.
DEFEND = {"plains": 0, "forest": 1, "ocean": 0, "mountain": 2}

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

# ---- staircase geometry ---------------------------------------------------
SW, SGAP = 49.0, 2.5              # step width, gap between steps
# Right-aligned, not centred: the ladder should arrive at the right margin, and
# it opens a wider triangle of void on the left for GOLD and the die.
SX0 = PW - M - 5 * SW - 4 * SGAP
FLOOR = 142.0
TOP0, RISE = 106.0, 11.0          # first step's top, and the rise per step

# Inside a block: a name strip on the tread, the sockets in the middle, and a
# shelf of counts along the bottom. Only two small marks are left in the notch
# above each tread, which is what lets the staircase read as a silhouette.
NAME_H = 12.0                     # tread strip that carries the tier name
SHELF_Y = FLOOR - 7.5             # centreline of the meld/moves shelf


def step_x(i):
    return SX0 + i * (SW + SGAP)


def step_top(i):
    return TOP0 - i * RISE


def T(x, y, s, size=4.2, anchor="middle", col=None, weight="400", mono=False,
      ls=0.0, italic=False, opacity=None):
    fam = ("'IBM Plex Mono',monospace" if mono
           else "Fraunces,Georgia,serif" if weight in ("600", "700")
           else "'IBM Plex Sans',sans-serif")
    it = ' font-style="italic"' if italic else ""
    op = f' opacity="{opacity}"' if opacity else ""
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="{fam}" '
            f'font-size="{size}" font-weight="{weight}" fill="{col or INK}" '
            f'text-anchor="{anchor}" letter-spacing="{ls}"{it}{op}>{s}</text>')


def hex_chip(cx, cy, r, suit):
    ink = marks.COLOUR[suit]["ink"]
    g = GLYPH[suit].format(ink="#fff", page=ink)
    s = r * 2 * 0.62
    return (f'<g><polygon points="{marks.hex_points(cx, cy, r)}" fill="{ink}"/>'
            f'<svg x="{cx - s / 2:.2f}" y="{cy - s / 2:.2f}" '
            f'width="{s:.2f}" height="{s:.2f}" viewBox="0 0 24 24">{g}</svg></g>')


def pips(cx, cy, n, col, step=3.1, rr=1.15):
    w = (n - 1) * step
    return "".join(
        f'<path d="M{cx - w / 2 + i * step:.2f} {cy - rr} '
        f'L{cx - w / 2 + i * step + rr:.2f} {cy} '
        f'L{cx - w / 2 + i * step:.2f} {cy + rr} '
        f'L{cx - w / 2 + i * step - rr:.2f} {cy} Z" fill="{col}"/>'
        for i in range(n))


def meld_cards(x, cy, n):
    """The meld limit as little cards — the same shape effect A wears."""
    w, h, off = 4.6, 6.6, 2.3
    return "".join(
        f'<rect x="{x + i * off:.2f}" y="{cy - h / 2:.2f}" width="{w}" '
        f'height="{h}" rx=".8" fill="#fff" stroke="{INK}" stroke-width=".4"/>'
        for i in range(n)), x + (n - 1) * off + w


def chevrons(x, cy, n):
    """Free moves, one chevron each."""
    p = 2.9
    return "".join(
        f'<path d="M{x + i * p:.2f} {cy - 2.1} l2 2.1 l-2 2.1" fill="none" '
        f'stroke="{INK}" stroke-width=".75" stroke-linecap="round" '
        f'stroke-linejoin="round"/>' for i in range(n)), x + (n - 1) * p + 2


def cap_box(x, cy, cap):
    """The rank cap, in a card-shaped box because what it limits is a card."""
    w, h = 9.4, 12.4
    return (f'<rect x="{x:.2f}" y="{cy - h / 2:.2f}" width="{w}" height="{h}" '
            f'rx="1.3" fill="#fff" stroke="{INK}" stroke-width=".5"/>'
            + T(x + w / 2, cy + 2.7, cap, 7.4, weight="600")), x + w


def wall_mark(cx, cy, n, r=5.2, num=6.2):
    """The wall rank: a tile inside a rampart.

    board_a4.py draws this as a heater shield, which is a fine picture of a wall
    and the wrong word — the cards already have a mark for a fortified tile, and
    it is a ring drawn around the hex (marks.py, `_rampart`). Reusing it means a
    player who has learned effect B has already learned this box: a hex with a
    wall around it, and the rank that wall holds written inside."""
    out = (f'<polygon points="{marks.hex_points(cx, cy, r + 1.9)}" fill="none" '
           f'stroke="{INK}" stroke-width=".62" stroke-linejoin="round" '
           f'opacity=".85"/>'
           f'<polygon points="{marks.hex_points(cx, cy, r)}" fill="#fff" '
           f'stroke="{INK}" stroke-width=".5" stroke-linejoin="round"/>')
    return out + T(cx, cy + num * 0.36, str(n), num, weight="600")


WALL_W = (5.2 + 1.9) * 2 * 0.8660254      # the mark's full width, for layout


def objective(cx, cy, r=2.0):
    """A map objective: a middle tile you hold, with two neighbours you hold.

    Drawn schematic and bent, not as a straight line — the rule allows any
    bend, and `claude/map-objectives.md` records that the straight card art
    teaches a shape the rule does not have. Terrain is deliberately not
    coloured in: the mark says "an objective", the cards say which.
    """
    d = r * 0.8660254
    out = ""
    for dx, dy, fill in ((0, 0, "#fff"), (-d, 1.5 * r, INK), (d, 1.5 * r, "#fff")):
        out += (f'<polygon points="{marks.hex_points(cx + dx, cy + dy, r)}" '
                f'fill="{fill}" stroke="{INK}" stroke-width=".5" '
                f'stroke-linejoin="round"/>')
    return out


def socket(cx, cy, r=5.5):
    return (f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r}" fill="#fff" '
            f'fill-opacity=".62" stroke="{SOFT}" stroke-width=".45" '
            f'stroke-dasharray="1.7 1.6" opacity=".8"/>'
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r - 1.6}" fill="none" '
            f'stroke="{SOFT}" stroke-width=".28" opacity=".45"/>')


def sockets(cx, top, n):
    """The units this tier still owes you. Three to a row; five becomes three
    over two, which keeps every step the same width.

    Centred in the band between the name strip and the shelf rather than hung
    from the tread — top-anchored sockets left the tall blocks looking like a
    pile at the top of an empty box."""
    p, gap, out = 12.6, 12.4, ""
    rows = [n] if n <= 3 else [3, n - 3]
    mid = ((top + NAME_H) + (FLOOR - 12)) / 2
    y0 = mid - (len(rows) - 1) * gap / 2
    for r, count in enumerate(rows):
        y = y0 + r * gap
        for k in range(count):
            out += socket(cx - (count - 1) * p / 2 + k * p, y)
    return out


def coin(cx, cy, r=3.4):
    return (f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r}" fill="{GOLDl}" '
            f'stroke="{GOLD}" stroke-width=".55"/>'
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r - 1.25}" fill="none" '
            f'stroke="{GOLD}" stroke-width=".35" opacity=".7"/>')


DEFS = '''<defs>
<pattern id="wv" width="8.66" height="15" patternUnits="userSpaceOnUse">
  <g fill="none" stroke="#FFFFFF" stroke-width=".38" opacity=".34">
    <polygon points="4.33,-2.5 8.66,0 8.66,5 4.33,7.5 0,5 0,0"/>
    <polygon points="0,5 4.33,7.5 4.33,12.5 0,15 -4.33,12.5 -4.33,7.5"/>
    <polygon points="8.66,5 12.99,7.5 12.99,12.5 8.66,15 4.33,12.5 4.33,7.5"/>
  </g>
</pattern>
</defs>'''


def build():
    o = [f'<rect width="{PW}" height="{PH}" fill="{PAPER}"/>', DEFS]

    # ---- header ----------------------------------------------------------
    o.append(T(M, 26, "BLINK", 12.5, anchor="start", weight="700", ls=1.5))
    o.append(T(M + 54, 26, "player board", 6.2, anchor="start", col=SOFT,
               italic=True))
    o.append(T(M + 54, 32.5, "lean economy &middot; no food, no ascension", 3.4,
               anchor="start", col=FAINT, mono=True, ls=.4))

    # the ground, and the wall that stands on it. Both are defence, so they sit
    # together; the number each step carries is the rank the wall holds.
    tx = PW - M
    for suit in reversed(SUITS):
        o.append(hex_chip(tx - 4.6, 23, 4.6, suit))
        o.append(T(tx - 4.6, 31.6, str(HOLDS[suit]), 3.3, col=SOFT, mono=True))
        d = DEFEND[suit]
        o.append(T(tx - 4.6, 35.8, f"+{d}" if d else "&middot;", 3.3,
                   col=SOFT if d else FAINT, mono=True))
        tx -= 12.4
    o.append(T(tx + 1, 31.6, "holds", 3.1, anchor="end", col=FAINT, mono=True))
    o.append(T(tx + 1, 35.8, "defends", 3.1, anchor="end", col=FAINT, mono=True))

    # the initiative die, up here rather than wedged into the narrow end of the
    # void. It is a placed component like the terrain chips beside it, and the
    # header is the one band on the board with room for a marked square.
    o.append(f'<rect x="168" y="15" width="20" height="20" rx="3" '
             f'fill="#fff" fill-opacity=".6" stroke="{SOFT}" '
             f'stroke-width=".5" stroke-dasharray="2.2 2"/>')
    for dx, dy in ((174, 21), (178, 25), (182, 29)):
        o.append(f'<circle cx="{dx}" cy="{dy}" r="1.4" fill="{SOFT}" '
                 f'opacity=".5"/>')
    # no caption: a dashed square with pips in it, labelled INITIATIVE, does not
    # need to be told it is where the die goes, and the header is dense enough
    o.append(T(192, 26.5, "INITIATIVE", 4.8, anchor="start", weight="600"))

    # ---- gold, in the wide part of the void the staircase opens ----------
    # The die used to sit under this and looked wedged in: the void is a
    # staircase-shaped triangle, not a rectangle, and below Tribe's label stack
    # it narrows to about 26 mm. So the die went to the header, where a 20 mm
    # box fits beside the terrain strip, and the well took the space it left.
    # It is the right trade: gold is a physical pile that wants area, the die is
    # one small object that wants a marked square.
    o.append(T(M, 46, "GOLD", 5.2, anchor="start", weight="600"))
    o.append(f'<rect x="{M}" y="51" width="74" height="30" rx="2.6" '
             f'fill="{GOLDl}" fill-opacity=".5" stroke="{GOLD}" '
             f'stroke-width=".55"/>')
    o.append(coin(M + 18, 66, 8))
    o.append(T(M + 34, 64, "keep your coins here", 3.6, anchor="start",
               col=GOLDd))
    o.append(T(M + 34, 70.4, "no limit &mdash; pile them up", 3.3,
               anchor="start", col=SOFT))

    # ---- the staircase ---------------------------------------------------
    # Everything that names a tier lives ON its block. The notch above each
    # tread carries two small marks and nothing else — pips for the age, and the
    # pair of ranks. Earlier drafts stacked pips + name + both boxes into that
    # wedge, which is only one step wide and bounded by a diagonal: five crowded
    # clusters fighting each other, and a staircase you could no longer see.
    for i, (label, meld, units, moves, cap, wall) in enumerate(BANDS):
        x, top = step_x(i), step_top(i)
        cx, h = x + SW / 2, FLOOR - top
        o.append(f'<rect x="{x:.2f}" y="{top:.2f}" width="{SW}" height="{h:.2f}" '
                 f'rx="2.2" fill="{WASH[i]}"/>')
        o.append(f'<rect x="{x:.2f}" y="{top:.2f}" width="{SW}" height="{h:.2f}" '
                 f'rx="2.2" fill="url(#wv)"/>')
        # the tread: a firmer line on the step's top edge
        o.append(f'<line x1="{x + 1.4:.2f}" y1="{top:.2f}" x2="{x + SW - 1.4:.2f}" '
                 f'y2="{top:.2f}" stroke="{PIP[i]}" stroke-width=".8" '
                 f'opacity=".55" stroke-linecap="round"/>')

        # ON the tread, the name. 49 mm holds "Civilization" comfortably at this
        # size, and a name inside its own block cannot be mistaken for its
        # neighbour's the way a floating one can.
        o.append(T(cx, top + 8.4, label, 5.8, weight="600"))
        o.append(sockets(cx, top, units))

        # IN THE NOTCH, the age and the two ranks: what you may buy, and what
        # your wall holds. Always two apart, which is easier to see than to say.
        o.append(pips(cx, top - 19, i + 1, PIP[i]))
        row, x0 = top - 8.5, cx - (9.4 + 2.6 + WALL_W) / 2
        box, xe = cap_box(x0, row, cap)
        o.append(box)
        o.append(wall_mark(xe + 2.6 + WALL_W / 2, row, wall))

        # ALONG THE BOTTOM, on a shelf shared by all five, the two counts: cards
        # you may meld, moves you get free. Both grow as you climb, so the shelf
        # is read across rather than down.
        cw, chw = (meld - 1) * 2.3 + 4.6, (moves - 1) * 2.9 + 2
        sx = cx - (cw + 5.5 + chw) / 2
        cards, _ = meld_cards(sx, SHELF_Y, meld)
        o.append(cards)
        chev, _ = chevrons(sx + cw + 5.5, SHELF_Y, moves)
        o.append(chev)

    # ---- legend: each mark named once, under the floor --------------------
    ly0, ty = FLOOR + 5.5, FLOOR + 6.9
    lx = M
    cards, xe = meld_cards(lx, ly0, 3)
    o.append(cards)
    o.append(T(xe + 2.2, ty, "meld", 3.2, anchor="start", col=FAINT, mono=True))
    # a stand-in for the cap box: the real one is 12.4 mm tall and would break
    # out of the legend line into the rule below it
    xb = xe + 20
    o.append(f'<rect x="{xb:.2f}" y="{ly0 - 4.3:.2f}" width="6.4" '
             f'height="8.6" rx="1" fill="#fff" stroke="{INK}" '
             f'stroke-width=".45"/>')
    o.append(T(xb + 8.6, ty, "buy up to", 3.2, anchor="start", col=FAINT,
               mono=True))
    xw = xb + 40
    o.append(wall_mark(xw, ly0, "", r=2.9, num=0.01))
    o.append(T(xw + 5.8, ty, "wall holds", 3.2, anchor="start", col=FAINT,
               mono=True))
    chev, xe3 = chevrons(xw + 30, ly0, 2)
    o.append(chev)
    o.append(T(xe3 + 2.5, ty, "moves", 3.2, anchor="start", col=FAINT,
               mono=True))
    o.append(T(PW - M, ty,
               "your tier is the first step with units left on it", 3.5,
               anchor="end", col=SOFT, italic=True))
    # the one rule the marks cannot carry: what a wall is FOR. It is here rather
    # than in the header because this is where the mark is named.
    # ten millimetres below the marks, not five: at five the sentence ran
    # through the bottom point of the wall hexagon above it
    o.append(T(M, ty + 8.6, "1 gold fortifies a unit &mdash; it then defends at "
               "your wall, or at a better card from your hand", 3.4,
               anchor="start", col=SOFT, italic=True))

    # ---- scoring, two rows so nothing has to be squeezed -----------------
    # One row could not hold four sources at a readable size across 269 mm; the
    # last one ran off the sheet. Two rows also let the two victory-row points
    # sit together, which is the pairing board_a4.py's own comment says gets
    # lost when they are written as a running sentence.
    r1, r2 = 168.5, 175.5
    o.append(f'<line x1="{M}" y1="161.5" x2="{PW - M}" y2="161.5" '
             f'stroke="{LINE}" stroke-width=".4"/>')
    o.append(T(M, r1, "SCORING", 5.2, anchor="start", weight="600"))

    gx = M + 34
    o.append(socket(gx, r1 - 1.4, 3.4))
    o.append(T(gx + 8, r1, "1", 5, weight="600"))
    o.append(T(gx + 13, r1, "per unit on the map", 3.6, anchor="start", col=SOFT))

    gx = M + 104
    o.append(f'<rect x="{gx - 2.4:.2f}" y="{r1 - 5:.2f}" width="4.8" '
             f'height="6.8" rx=".8" fill="#fff" stroke="{INK}" '
             f'stroke-width=".4"/>')
    o.append(T(gx + 8, r1, "1", 5, weight="600"))
    o.append(T(gx + 13, r1, "per card in your victory row, &#43; the rank of "
               "its centre card", 3.6, anchor="start", col=SOFT))

    # "3 per terrain, biggest connected stretch" used to sit here as a general
    # rule. It belongs to the map objectives now, so the board points at them
    # rather than pricing them — map-objectives.md has the pricing still open.
    gx = M + 34
    o.append(objective(gx, r2 - 2.0))
    o.append(T(gx + 8, r2, "each map objective you hold", 3.6, anchor="start",
               col=SOFT))
    o.append(T(PW - M, r2, "gold breaks ties", 3.4, anchor="end", col=FAINT,
               mono=True))

    # ---- victory row -----------------------------------------------------
    # Real cards, not abstract boxes. Five poker cards side by side need
    # 5 x 63.5 = 317.5 mm and the sheet is 297, so they cannot all sit whole
    # inside the margins — but they can sit whole ON THE ROW and let the sheet
    # cut the outer two, which is board_a4.py's answer and the right one: the
    # first and last slots run off the edges as position indicators, and the
    # cards overhang the board, which is what they would do on a table anyway.
    # Centring five slots puts the scoring slot dead centre at 148.5 mm.
    #
    # The first pass here drew 42 x 18 mm boxes, which are not cards and do not
    # tell a player where to put one.
    vrow_x0 = (PW - 5 * CARD_W) / 2                  # -10.25: wider than the sheet
    vy = PH - VROW_REVEAL                            # only the top strip is on the board
    vlabel = vy - 6.2
    o.append(T(M, vlabel, "VICTORY ROW", 5.2, anchor="start", weight="600"))
    o.append(T(M + 46, vlabel, "&mdash; slide cards in from below; only the "
               "index band shows, and the centre slot scores", 3.5,
               anchor="start", col=SOFT))

    # rank order as a direction, not as a caption under a card that is off-page
    ax0, ax1 = PW - M - 74, PW - M
    o.append(f'<line x1="{ax0}" y1="{vlabel - 1.3:.1f}" x2="{ax1 - 3.4:.1f}" '
             f'y2="{vlabel - 1.3:.1f}" stroke="{FAINT}" stroke-width=".45"/>')
    o.append(f'<path d="M{ax1 - 3.6:.1f} {vlabel - 3.3:.1f} L{ax1:.1f} '
             f'{vlabel - 1.3:.1f} L{ax1 - 3.6:.1f} {vlabel + 0.7:.1f} Z" '
             f'fill="{FAINT}"/>')
    o.append(T(ax0 + 1, vlabel - 3.4, "LOWEST RANK", 2.9, anchor="start",
               col=FAINT, mono=True, ls=.3))
    o.append(T(ax1 - 5, vlabel - 3.4, "HIGHEST", 2.9, anchor="end", col=FAINT,
               mono=True, ls=.3))

    o.append(f'<clipPath id="sheet"><rect x="0" y="0" width="{PW}" '
             f'height="{PH}"/></clipPath><g clip-path="url(#sheet)">')
    for k in range(5):
        cx, mid = vrow_x0 + k * CARD_W, k == 2
        o.append(f'<rect x="{cx:.2f}" y="{vy:.2f}" width="{CARD_W}" '
                 f'height="{CARD_H}" rx="3" fill="{"#F6EED8" if mid else "#fff"}" '
                 f'fill-opacity="{.85 if mid else .5}" '
                 f'stroke="{GOLD if mid else FAINT}" '
                 f'stroke-width="{1.1 if mid else .55}"'
                 f'{"" if mid else chr(32) + chr(115) + "troke-dasharray=" + chr(34) + "2.5 2" + chr(34)}/>')
        # slot 1's number would fall off the left edge with the rest of its box
        o.append(T(max(cx + 5.5, 4.5), vy + 7.6, str(k + 1), 5.5, anchor="start",
                   col=INK if mid else FAINT, weight="600" if mid else "400"))
    mcx = vrow_x0 + 2 * CARD_W
    o.append(T(mcx + 12, vy + 7.4, "SCORES", 3.8, anchor="start", col=GOLDd,
               mono=True, ls=.5, weight="600"))
    o.append(f'<path d="M{mcx + 13:.1f} {vy - 3.4:.1f} L{mcx + 16.2:.1f} '
             f'{vy - .5:.1f} L{mcx + 19.4:.1f} {vy - 3.4:.1f} Z" fill="{GOLD}"/>')
    o.append("</g>")
    return "".join(o)


SVG = (f'<svg class="board" viewBox="0 0 {PW} {PH}" '
       f'xmlns="http://www.w3.org/2000/svg" role="img" '
       f'aria-label="Blink player board, lean ladder concept">{build()}</svg>')
