# -*- coding: utf-8 -*-
"""Blink player board, print-exact on A4 landscape.
All coordinates are millimetres; the SVG declares width/height in mm so the
PDF prints 1:1. Unit slots are 13 mm, the size of the unit pieces. A right-hand column carries two
card-sized areas: the personal DISCARD pile and the SHOWN map objective.
"""

import sys

from version import VTAG

# A VARIANT SHEET, not the printed board. The rulebook still carries the
# assault (§07), so a WALL column here would print a rule the book does not
# have. `--wall` makes the sheet for the proposal instead — the tier ladder the
# app plays with, 10/12/14/16/18 — so it can be put on a table and tried.
#   python3 board_a4.py             ->  board_a4.svg, with the WALL column
#   python3 board_a4.py --no-wall   ->  board_a4_nowall.svg, the pre-wall sheet
WALL = "--no-wall" not in sys.argv
# THE FOOD COLUMN IS GONE IN v0.26, and so is ascension, which shared it.
# Growing costs nothing now, so the board has nothing to print about the price
# of a tier. `--food` puts the column back for a v0.25 board.
FOOD = "--food" in sys.argv
# MOVES LEFT THE LADDER IN v0.26: movement comes from the meld - one per card
# you play - so a per-tier allowance is a number that decides nothing. The
# printed board is four columns; `--moves` puts the fifth back for anyone
# playing `cardMoves: "ladder"`.
MOVES = "--moves" in sys.argv
WALL_OFFSET = -2                 # a wall holds two under what you may buy

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
# 13 mm IS THE PIECE, not a layout choice: the unit pieces are 13 mm across,
# so a ring any smaller is a ring a unit does not fit in. When the card column
# arrived the width it needed came out of the gaps around the rings - the meld
# fan, the column spacing, the tier-name gap - never out of the rings.
D = 13.0                         # unit diameter, mm - the physical piece
UNIT_PIECE = 13.0
R = D / 2
GAP = 1.5                        # gap between unit slots
CD = 9.0                         # coin slot diameter
CR = CD / 2
# The row is drawn CENTRED on its baseline y. It used to start at y - R - 3
# while standing only D + 2.5 tall, which put the rectangle's middle 1.75 mm
# above the middle of the circles it was meant to contain — so the unit slots
# and the meld chip, both a full D across, broke through the bottom edge of
# their own row. Anything drawn at y is now centred in the band by definition.
BAND_H = D + 2.5                 # 15.5: a ring, with room above and below
ROW_GAP = 1.5

# ---- the card column -------------------------------------------------------
# THE REAL CARD, not a round number: poker size, 63.5 x 88.9 mm, which is what
# a printed deck is cut to (the print-and-play sheets cut a hair smaller, at
# 63 x 88, so they fit too). Each area is the card's whole footprint plus half
# a millimetre of play on every side, drawn LANDSCAPE: two portrait cards side
# by side need 131 mm of width, which the tier ladder cannot give up, while two
# landscape ones stacked fit the 133 mm between the masthead and the victory row.
CARD_W, CARD_H = 63.5, 88.9      # portrait, mm
PLAY = 0.5                       # clearance on every side of the card
AREA_W = CARD_H + 2 * PLAY       # landscape: the card lies on its side
AREA_H = CARD_W + 2 * PLAY
AREA_GAP = 4.5                   # between the two areas
COL_GUTTER = 6.0                 # between the ladder / lower zone and the column

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


def card_fan(x, y, n, active=False):
    """MELD as a FAN OF CARDS, because that is what a meld is.

    It used to be a numbered rounded rectangle - and so did MOVES, three
    columns away, which made the two most-used numbers on the board look like
    the same thing. A fan cannot be mistaken for anything else, and it is
    countable: the staircase from two cards to six down the five rows is the
    whole point of the tier track, and it is now a shape rather than a digit.

    Drawn leftmost-first so the top card of the fan is the rightmost, the way a
    right-handed player holds one. `x` is the left edge, `y` the centre.
    """
    step, cw, ch = FAN_STEP, 7.0, 10.5
    out = ""
    for k in range(n):
        cx = x + k * step
        lean = -14 + k * (28.0 / max(1, n - 1)) if n > 1 else 0
        out += (f'<g transform="rotate({lean:.1f} {cx + cw / 2:.2f} {y + ch / 2:.2f})">'
                f'<rect x="{cx:.2f}" y="{y - ch / 2:.2f}" width="{cw}" height="{ch}" '
                f'rx="1.2" fill="{GOLD if active else PAPER}" stroke="{INK}" '
                f'stroke-width="0.5"/>')
        # The count on the TOP card - the rightmost, the one a right-handed
        # player sees the rank of. A fan alone is countable but slow; the
        # digit is what makes it parse at a glance, and it sits where a
        # card would carry it anyway.
        if k == n - 1:
            out += T(cx + cw / 2, y + 2.6, str(n), 6.5, weight="700")
        out += '</g>'
    return out


def rank_corner(x, y, n):
    """CAP as the INDEX CORNER OF A CARD - the rank printed in the top-left of
    every playing card ever made.

    It was a bare number sitting between the meld chip and the tier name, which
    made it the one column on the board with no shape at all: a reader had to
    remember what the heading meant. A card corner says "this is about a card's
    rank" before anything is read, and it cannot be confused with the fan
    beside it because it is an outline, not a stack.

    Drawn as an L: down the left edge, round the corner, along the top. The
    open bottom-right is what makes it read as a corner rather than a box - a
    card continuing off to the right, which is exactly the "and everything
    below this" the rule means.
    """
    # Wide enough for TWO digits inside the bracket: at 10 mm the caps ran out
    # past the top rule and the corner read as an underline instead of a card.
    w, h, r = 15.0, 12.0, 1.8
    out = (f'<path d="M{x:.2f} {y + h / 2:.2f} '
           f'L{x:.2f} {y - h / 2 + r:.2f} '
           f'Q{x:.2f} {y - h / 2:.2f} {x + r:.2f} {y - h / 2:.2f} '
           f'L{x + w:.2f} {y - h / 2:.2f}" '
           f'fill="none" stroke="{INK}" stroke-width="0.7" '
           f'stroke-linecap="round"/>')
    # ...and a stub of the far corner, so the eye closes the card for itself
    out += (f'<path d="M{x + w:.2f} {y + h / 2:.2f} l-3.5 0" '
            f'fill="none" stroke="{FAINT}" stroke-width="0.7" '
            f'stroke-linecap="round"/>')
    # the index, sitting inside the bracket where a card carries it
    out += T(x + w / 2 + 0.6, y + 2.6, str(n), 7.0, anchor="middle", weight="700")
    return out


FAN_STEP = 3.4                   # was 4.4: the ladder gave width to the card column


def fan_width(n):
    return (n - 1) * FAN_STEP + 7.0 + 5.0   # + lean overhang


# Every left-anchored mono line drawn, so the overflow check at the end can
# measure them. Collected rather than recomputed: the check should see exactly
# what was drawn.
LINES = []


def T(x, y, s, size=4.2, anchor="middle", col=INK, weight="400", mono=False,
      spacing="0", style=""):
    if mono and anchor == "start":
        LINES.append((s, x, size, y))
    fam = "IBM Plex Mono" if mono else "IBM Plex Sans"
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="{fam}" '
            f'font-size="{size}" fill="{col}" text-anchor="{anchor}" '
            f'font-weight="{weight}" letter-spacing="{spacing}" '
            f'style="{style}">{s}</text>')


def shield(x, y, n):
    """The WALL value, drawn as the thing it is.

    Every other column on this board has a shape that says what it is before a
    word is read — a fan of cards for the meld, a card's index corner for the
    rank cap, circles for units, coins for food. A bare number for the wall
    would be the one column a reader has to remember the heading for.

    A heater shield: flat across the top, straight down the shoulders, then
    curving to a point. Drawn at the same 15x12 as the card corner beside it,
    so the two rank-scale numbers — what you may BUY and what your wall HOLDS —
    read as a pair, two apart, which is the rule.
    """
    w, h = 13.0, 13.5
    x0, y0 = x, y - h / 2
    out = (f'<path d="M{x0:.2f} {y0:.2f} '
           f'h{w:.2f} '
           f'v{h * 0.42:.2f} '
           f'q0 {h * 0.40:.2f} {-w / 2:.2f} {h * 0.58:.2f} '
           f'q{-w / 2:.2f} {-h * 0.18:.2f} {-w / 2:.2f} {-h * 0.58:.2f} '
           f'Z" fill="{PANEL}" stroke="{INK}" stroke-width="0.7"/>')
    # a band across the shoulders: it reads as masonry rather than as a crest,
    # and it keeps the number off the outline at small sizes
    out += (f'<path d="M{x0:.2f} {y0 + h * 0.26:.2f} h{w:.2f}" '
            f'stroke="{LINE}" stroke-width="0.4" fill="none"/>')
    out += T(x0 + w / 2, y + 2.4, str(n), 6.2, weight="600")
    return out


def unit_slot(x, y, filled=False):
    if filled:
        return (f'<circle cx="{x:.2f}" cy="{y+1:.2f}" r="{R:.2f}" fill="{REDdk}"/>'
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{R:.2f}" fill="{RED}" '
                f'stroke="{REDdk}" stroke-width="0.5"/>')
    return (f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{R:.2f}" fill="none" '
            f'stroke="{FAINT}" stroke-width="0.6" stroke-dasharray="1.6 1.6"/>')


DIE = 15.0                       # printed die slot, mm — suits a 12-16 mm die


def die_slot(x, y):
    """Where your initiative die waits until your turn is over.

    A die IN its slot means that player has still to act this round; a die out
    of it means they are done. That is the whole of it, and it holds however
    the die left - rolled for something, or simply lifted out because the turn
    ended. One state, no exceptions, and the table can read who is left at a
    glance instead of comparing four numbers.

    Two of these are printed, one at each top corner, and a player uses
    whichever is nearer the middle of the table — the board is symmetrical
    because the seating is not. The slot is drawn in the same dashed, faint
    idiom as an empty unit slot, because it means the same thing: something
    belongs here and is not here yet.

    OUT OF THE SLOT IS NOT OFF THE TABLE. The coloured die still carries the
    winner's meld size, and the player who matched it gives a card up at the
    start of their OWN map turn - so the last player in the order is still
    reading that number when the winner has long finished. A finished die goes
    beside its slot, face up, not back in the box.
    """
    out = (f'<rect x="{x:.2f}" y="{y:.2f}" width="{DIE}" height="{DIE}" rx="2.6" '
           f'fill="none" stroke="{FAINT}" stroke-width="0.6" '
           f'stroke-dasharray="1.6 1.6"/>')
    # A five-pip face, faint: it says "a die" without being mistaken for an
    # instruction to set the die to five.
    for px, py in ((0.28, 0.28), (0.72, 0.28), (0.5, 0.5), (0.28, 0.72), (0.72, 0.72)):
        out += (f'<circle cx="{x + DIE*px:.2f}" cy="{y + DIE*py:.2f}" r="0.9" '
                f'fill="{FAINT}"/>')
    return out


def coin_slot(x, y):
    return (f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{CR:.2f}" fill="{PAPER}" '
            f'stroke="{GOLD}" stroke-width="0.7"/>'
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{CR-2:.2f}" fill="none" '
            f'stroke="{GOLDl}" stroke-width="0.6"/>')


def card_area(x, y, title, lines, glyph):
    """A place for ONE CARD, drawn at the card's own footprint.

    Tinted and dashed like every other "something goes here" on this sheet (the
    victory-row slots, the unit rings, the die corners), so it reads as a
    space to fill rather than a box of rules. The words sit at the top left and
    a card laid on the area covers them, which is what a card area on a
    published board does: the label is for the empty space, and once the card
    is down the card says what it is.
    """
    out = (f'<rect x="{x:.2f}" y="{y:.2f}" width="{AREA_W:.2f}" '
           f'height="{AREA_H:.2f}" rx="3" fill="{PANEL}" fill-opacity="0.7" '
           f'stroke="{FAINT}" stroke-width="0.7" stroke-dasharray="2.5 2"/>')
    out += T(x + 5, y + 9.5, title, 5.2, anchor="start", weight="600",
             spacing="0.2")
    for j, ln in enumerate(lines):
        out += T(x + 5, y + 16.0 + j * 4.6, ln, 3.4, anchor="start", col=SOFT,
                 mono=True)
    out += glyph(x + AREA_W - 6, y + AREA_H - 6)
    return out


def glyph_pile(xr, yb):
    """Three cards squared into a pile - the discard. (xr, yb) is the
    bottom-right corner the glyph sits in."""
    w, h = 13.0, 18.0
    out = ""
    for k in range(3):
        x = xr - w - (2 - k) * 2.2
        y = yb - h - k * 1.8
        out += (f'<rect x="{x:.2f}" y="{y:.2f}" width="{w}" height="{h}" '
                f'rx="1.4" fill="{PAPER}" stroke="{FAINT}" stroke-width="0.6"/>')
    return out


def glyph_eye(xr, yb):
    """An open eye - the objective everybody can read."""
    w, h = 20.0, 10.0
    x0, cy = xr - w, yb - h / 2 - 2
    out = (f'<path d="M{x0:.2f} {cy:.2f} Q{x0 + w / 2:.2f} {cy - h:.2f} '
           f'{x0 + w:.2f} {cy:.2f} Q{x0 + w / 2:.2f} {cy + h:.2f} {x0:.2f} '
           f'{cy:.2f} Z" fill="{PAPER}" stroke="{FAINT}" stroke-width="0.7"/>')
    out += (f'<circle cx="{x0 + w / 2:.2f}" cy="{cy:.2f}" r="3.2" fill="none" '
            f'stroke="{FAINT}" stroke-width="0.7"/>')
    out += (f'<circle cx="{x0 + w / 2:.2f}" cy="{cy:.2f}" r="1.3" '
            f'fill="{FAINT}"/>')
    return out


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
    # THE TOP EDGE IS THE ONE FACING THE TABLE, so it is where the die goes.
    # Both corners carry a slot and a player uses one: someone sitting to the
    # left of the play area wants their die on their right, and vice versa.
    # Printing both costs nothing and saves every left-hand seat from reaching
    # across their own board all game.
    dy = M + 2
    s.append(die_slot(M + 2, dy))
    s.append(die_slot(PW - M - 2 - DIE, dy))
    inner_l, inner_r = M + 2 + DIE + 6, PW - M - 2 - DIE - 6

    s.append(T(inner_l, M+8, "BLINK", 9, anchor="start", weight="600"))
    s.append(T(inner_l+34, M+8, "player board", 5, anchor="start", col=SOFT,
               style="font-style:italic"))
    s.append(T(inner_r, M+7, f"{VTAG}", 3.4,
               anchor="end", col=SOFT, mono=True, spacing="0.3"))
    # The board names its own parts. One line does the whole rule, including
    # why there are two of them.
    s.append(T((inner_l + inner_r) / 2, M+15.5,
               "your initiative die waits in either corner \u2014 whichever is "
               "nearer the table \u2014 and comes out when your turn ends", 3.0,
               col=SOFT, mono=True))
    s.append(f'<line x1="{M}" y1="{M+19}" x2="{PW-M}" y2="{M+19}" '
             f'stroke="{INK}" stroke-width="0.5"/>')

    # ================= THE CARD COLUMN, geometry first =====================
    # Down the right-hand side, under the masthead and above the victory row:
    # the DISCARD on top and the SHOWN OBJECTIVE below it. Everything else on
    # the sheet is laid out in what is left to their left, so these numbers come
    # before the ladder's.
    mast_y = M + 19
    col_x1 = PW - M - 1.0            # a millimetre inside the right trim
    col_x0 = col_x1 - AREA_W
    left_r = col_x0 - COL_GUTTER     # the ladder and lower zone end here
    disc_y0 = mast_y + 3.0
    obj_y0 = disc_y0 + AREA_H + AREA_GAP
    col_bot = obj_y0 + AREA_H

    top = M + 24.5

    # ================= RESERVE / PROGRESS TRACK =========================
    # one continuous track, split into the four bands, laid as stacked rows.
    band_x = M + 2
    row_y = top + 11

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
    # THE ROW, LEFT TO RIGHT, and every column sized from what it holds rather
    # than from a number typed here. Losing the ASCEND column freed 25 mm; it
    # goes to the meld fan, which needs room for six cards, and to the space
    # between the three groups so they read as three things.
    maxmeld = max(b[1] for b in BANDS)
    meld_w  = fan_width(maxmeld)
    meld_x0 = band_x
    cap_x0  = meld_x0 + meld_w + 3.5
    # WALL sits beside BUY UP TO on purpose: both are ranks, and the two
    # numbers on any row are two apart, which is the whole rule without a
    # sentence. It costs 17 mm, taken from the tier-name gap and the reserve
    # one below — see the two subtractions there.
    # BUY UP TO and WALL sat 20 mm apart, which put their headings a single
    # space apart: across the table the row was headed "BUY UP TO WALL", one
    # phrase naming one thing, when they are two ranks two apart. The gap only
    # had to be that tight because MOVES needed the width at the far end of the
    # row; without it there is room to say they are two columns. The full board
    # (--food --moves) keeps the old 20, because the width is still spoken for
    # there and MOVES falls off the sheet at 26.
    _UPKEEP = FOOD or MOVES
    wall_x0 = cap_x0 + (20 if _UPKEEP else 19) if WALL else cap_x0
    name_x0 = (wall_x0 + 15) if WALL else (cap_x0 + 19)
    # The row has to end inside the margin with MOVES' heading on it, so the
    # gaps are spent from a budget rather than guessed. Widening the name gap
    # to 48 pushed MOVES 9 mm off the sheet; the food column gives it back,
    # because four coins do not need 12 mm of pitch.
    # 28: the longest tier name ("Settlement", 19.7 mm at 3.8) plus the lead
    # arrow into the reserve and the take-from-the-top arrow it crosses.
    slots_x0 = name_x0 + 28
    food_x0  = slots_x0 + slots_w + (9 if WALL else 12)
    food_w   = max(b[3] for b in BANDS)*(CD+1.5) if FOOD else 0
    # Without the column its gap goes too, or MOVES floats in a void where the
    # coins used to be and the board looks like it lost something.
    moves_x0 = food_x0 + food_w + (10 if FOOD else 0)
    sep_x    = slots_x0 + slots_w + (4 if WALL else 6)   # units | upkeep

    # IS THERE ANYTHING TO THE RIGHT OF THE RESERVE? Food and moves were both
    # columns out there, and v0.26 has neither - so the row ran to the right
    # margin anyway and left 76 mm of empty panel past the last unit slot, with
    # the units|upkeep rule drawn down the middle of the void. From across the
    # table that reads as a column somebody forgot to print, which is a worse
    # board than a narrower one.
    #
    # So the row ends where its content ends, and the ladder is then CENTRED on
    # the sheet instead of pinned to the left margin with a hole on the right.
    # Every x above is band_x plus a constant, so centring is one shift applied
    # to all of them - no second layout to keep in step with the first. With
    # --food or --moves this is a no-op and the board is exactly as it was.
    UPKEEP = _UPKEEP
    # The ladder now ends at the card column's gutter, not at the right trim.
    band_r = left_r if UPKEEP else (slots_x0 + slots_w + 2.5)
    shift  = 0.0 if UPKEEP else max(0.0, (left_r - band_r) / 2)
    if shift:
        meld_x0 += shift; cap_x0 += shift; wall_x0 += shift
        name_x0 += shift; slots_x0 += shift
        food_x0 += shift; moves_x0 += shift; sep_x += shift
        band_x += shift; band_r += shift

    s.append(T(meld_x0, top, "MELD", 3.6, anchor="start", col=SOFT, mono=True,
               spacing="0.4"))
    if WALL:
        # nine characters, start-anchored, ran straight into WALL. Centred over
        # its own card corner it clears the shield and still sits above what it
        # names — and the base sheet, which has no neighbour there, is untouched.
        s.append(T(cap_x0 + 7.5, top, "RANK CAP", 3.6, col=SOFT, mono=True,
                   spacing="0.2"))
    else:
        s.append(T(cap_x0, top, "RANK CAP", 3.6, anchor="start", col=SOFT,
                   mono=True, spacing="0.4"))
    if WALL:
        # short, and centred over the shield: "BUY UP TO" is nine characters
        # and the two headings met in the middle at anything longer.
        s.append(T(wall_x0 + 6.5, top, "WALL", 3.6, col=SOFT,
                   mono=True, spacing="0.4"))
    # just the label: the rule about emptying top-down ran into FOOD, and it
    # belongs with the other standing rules under the track anyway
    s.append(T(slots_x0, top, "RESERVE", 4.2,
               anchor="start", col=SOFT, mono=True, spacing="0.4"))
    # ONE COLUMN, TWO JOBS. Food and the ascension reward are the same number
    # at every tier - 0/1/2/3/4 both - so ASCEND is no longer a column of its
    # own hiding at the right-hand edge where nobody read it. The ascension
    # coins START on the food slots: reach the tier, take them, and the slots
    # they leave are exactly what that tier now costs to feed. One row of
    # circles, and the reward arrives as something you pick up rather than a
    # number printed somewhere else.
    if FOOD:
        s.append(T(food_x0 + food_w/2, top, "FOOD", 4.2,
                   col=GOLDd, mono=True, spacing="0.6", weight="600"))
    # "MV" was two letters nobody had to guess at once they had learned them,
    # which is a poor bargain on a board a stranger picks up.
    moves_cx = (moves_x0 + left_r) / 2          # centred in what is left
    if MOVES:
        s.append(T(moves_cx, top, "MOVES", 4.2, col=SOFT, mono=True, spacing="0.6"))

    y = row_y
    for i, (name, limit, n, coins, moves, asc, cap) in enumerate(BANDS):
        band_h = BAND_H
        band_top = y - band_h/2
        # band background
        active = False      # a blank board: nothing pre-filled
        s.append(f'<rect x="{band_x-2}" y="{band_top:.2f}" '
                 f'width="{band_r-(band_x-2):.2f}" '
                 f'height="{band_h}" rx="2.4" fill="{PANEL if i%2==0 else PAPER}" '
                 f'stroke="{LINE}" stroke-width="0.4"/>')
        # FOOD is the number that ambushes people — it comes due on a recycle,
        # in the middle of somebody else's excitement — so the column is tinted
        # the colour of the coins it asks for, all the way down.
        if FOOD:
            s.append(f'<rect x="{food_x0-3}" y="{band_top:.2f}" width="{food_w+6}" '
                     f'height="{band_h}" fill="{GOLDl}" fill-opacity="0.3"/>')
        # MELD, as a fan of that many cards
        s.append(card_fan(meld_x0, y, limit, active))
        # the rank cap, beside the meld fan: how HIGH, next to how MANY
        s.append(rank_corner(cap_x0, y, cap))
        if WALL:
            s.append(shield(wall_x0, y, max(1, int(cap) + WALL_OFFSET)))
        # band name, and a lead line from it INTO the reserve. A tier is not a
        # label sitting near some circles: it is the name of the row those
        # units come out of, and the two were reading as separate columns.
        s.append(T(name_x0, y-1.3, name, 3.8, anchor="start", weight="600"))
        s.append(T(name_x0, y+3.6, f"{n} units", 3.3, anchor="start",
                   col=SOFT, mono=True))
        lead_x0 = name_x0 + 21.0
        lead_x1 = slots_x0 - 0.8
        s.append(f'<path d="M{lead_x0:.1f} {y:.1f} L{lead_x1:.1f} {y:.1f}" '
                 f'fill="none" stroke="{FAINT}" stroke-width="0.4"/>')
        s.append(f'<path d="M{lead_x1-2.2:.1f} {y-1.6:.1f} l2.2 1.6 l-2.2 1.6" '
                 f'fill="none" stroke="{FAINT}" stroke-width="0.5" '
                 f'stroke-linecap="round" stroke-linejoin="round"/>')
        # RESERVE reads left to right: the slots start at the same edge on every
        # tier, so the track is a staircase you can see growing rather than five
        # rows of circles floating at five different offsets. (They were centred
        # once, back when this column was too wide for its content.)
        for k in range(n):
            cx = slots_x0 + R + k*(D+GAP)
            s.append(unit_slot(cx, y, filled=False))
        # FOOD is centred in its column: the coins are a QUANTITY, not a
        # sequence, and a centred cluster grows symmetrically down the tiers
        # instead of drifting rightward off a fixed left edge.
        if coins and FOOD:
            row_w = coins*CD + (coins-1)*1.5
            off = (food_w - row_w) / 2
            for c in range(coins):
                cx = food_x0 + off + CR + c*(CD+1.5)
                s.append(coin_slot(cx, y))
            # a bracket under the slots on the tiers that pay one, so the setup
            # instruction is legible from the board itself
            if asc:
                x1 = food_x0 + off + 1
                x2 = food_x0 + off + row_w - 1
                yy = y + R - 0.6
                s.append(f'<path d="M{x1:.2f} {yy:.2f} l0 1.2 L{x2:.2f} {yy+1.2:.2f} '
                         f'l0 -1.2" fill="none" stroke="{GOLDd}" stroke-width="0.4"/>')
        elif FOOD:
            s.append(T(food_x0 + food_w/2, y+1.5, "free", 3.3,
                       col=SOFT, mono=True, style="font-style:italic"))
        # MOVES: a number and a stride, centred as one group under its heading.
        # The box is what made this read as another meld chip from across the
        # table; drifting left in a column two hands wide is what made it read
        # as an afterthought.
        if MOVES:
            s.append(T(moves_cx - 4.5, y+2.4, str(moves), 7.5, weight="600"))
            ax = moves_cx + 0.5
            s.append(f'<path d="M{ax:.1f} {y:.1f} l7 0 M{ax+4.6:.1f} {y-2.6:.1f} '
                     f'l2.6 2.6 l-2.6 2.6" fill="none" stroke="{SOFT}" '
                     f'stroke-width="0.8" stroke-linecap="round" '
                     f'stroke-linejoin="round"/>')
        y += band_h + ROW_GAP

    # THE DIRECTION OF TRAVEL, once, down the whole reserve: you always take
    # from the topmost tier that still has units, and that is the one rule on
    # this board with no number to print. A faint arrow says it without a word.
    # After the loop `y` sits one band BELOW the last row, so the bottom of the
    # track is y - BAND_H/2 - 1.5. Reading that wrong put the arrowhead through
    # the glossary line.
    arr_x = slots_x0 - 5.0
    top_y = row_y - BAND_H/2 - 1
    bot_y = y - ROW_GAP - BAND_H/2 - 1.5
    s.append(f'<path d="M{arr_x:.1f} {top_y:.1f} L{arr_x:.1f} {bot_y-2.6:.1f}" '
             f'fill="none" stroke="{FAINT}" stroke-width="0.5"/>')
    s.append(f'<path d="M{arr_x-1.8:.1f} {bot_y-3.4:.1f} L{arr_x:.1f} {bot_y:.1f} '
             f'L{arr_x+1.8:.1f} {bot_y-3.4:.1f}" fill="none" stroke="{FAINT}" '
             f'stroke-width="0.6" stroke-linecap="round" stroke-linejoin="round"/>')

    # One rule down the row: to its left is what you hold, to its right what
    # holding it costs you every recycle. With nothing on the right there is no
    # division to draw, and the line became the right-hand wall of an empty box.
    if UPKEEP:
        s.append(f'<line x1="{sep_x}" y1="{row_y-BAND_H/2:.2f}" x2="{sep_x}" '
                 f'y2="{y-ROW_GAP-BAND_H/2:.2f}" '
                 f'stroke="{LINE}" stroke-width="0.4"/>')

    # ON THE BOARD IS GONE (v0.26, card-column pass). It was a seven-line
    # glossary of words printed elsewhere on this sheet, and every gloss in it
    # is in the rulebook and on the player aid as well; the room it took is what
    # the discard and the shown objective needed. What it said that only this
    # board could say - that the victory row fills from the right - now sits in
    # the victory row itself, on slot 5.

    # ============ lower zone: gold and scoring =============================
    #
    # WHAT IS NOT HERE ANY MORE. The round order and the menu of a turn both
    # used to sit on this board, and both are now on the player aid, which is
    # in the player's hand rather than under their units and can be read
    # without leaning over the table. A board that repeats the aid is two
    # sources for one rule, and the pair drifted apart once already.
    low = y + 4.5
    s.append(f'<line x1="{M}" y1="{low-6}" x2="{left_r:.2f}" y2="{low-6}" '
             f'stroke="{LINE}" stroke-width="0.4"/>')

    # --- two columns: gold, and how the game is scored -------------------
    gx = M
    gvw, gvh = 82, 15
    sx = gx + gvw + 10

    s.append(T(gx, low, "GOLD", 4.6, anchor="start", weight="600"))

    gv_y = low + 6.5
    s.append(f'<rect x="{gx}" y="{gv_y}" width="{gvw}" height="{gvh}" rx="3" '
             f'fill="{PAPER}" stroke="{GOLD}" stroke-width="0.8"/>')
    # Twelve printed circles read as twelve slots, and a player who filled
    # them would reasonably think that was the ceiling. It is not — gold is
    # unbounded. So: one coin with a couple behind it, which reads as a pile.
    ccx, ccy = gx + 14, gv_y + gvh/2
    s.append(f'<circle cx="{ccx-3.5:.2f}" cy="{ccy-2:.2f}" r="5.5" fill="{PAPER}" '
             f'stroke="{GOLDl}" stroke-width="0.6"/>')
    s.append(f'<circle cx="{ccx+3.5:.2f}" cy="{ccy+2:.2f}" r="5.5" fill="{PAPER}" '
             f'stroke="{GOLDl}" stroke-width="0.6"/>')
    s.append(f'<circle cx="{ccx:.2f}" cy="{ccy:.2f}" r="5.5" fill="{PAPER}" '
             f'stroke="{GOLD}" stroke-width="0.9"/>')
    s.append(f'<circle cx="{ccx:.2f}" cy="{ccy:.2f}" r="3.6" fill="none" '
             f'stroke="{GOLDl}" stroke-width="0.6"/>')
    s.append(T(gx + 25, ccy - 0.8, "keep your coins here", 3.0, anchor="start",
               col=INK, mono=True))
    s.append(T(gx + 25, ccy + 3.6, "no limit \u2014 pile them up", 2.9,
               anchor="start", col=SOFT, mono=True))

    # The victory row scores TWICE: a point per card, and the rank of its
    # centre card on top (engine: vrowScore = length + centre). One line per
    # source — a running sentence is where the per-card half got lost.
    s.append(T(sx, low, "SCORING", 4.6, anchor="start", weight="600"))
    for j, line in enumerate([
            "1  per unit on the map",
            "1  per card in your victory row",
            "+  the rank in the centre slot (3+ cards)",
            "+  2 per objective arrangement",
            "gold breaks ties"]):
        s.append(T(sx, low+6.4+j*3.9, line, 3.0, anchor="start",
                   col=SOFT if j == 4 else INK, mono=True, spacing="0.1"))

    score_last = low + 6.4 + 4 * 3.9

    # --- THE CARD COLUMN, drawn ------------------------------------------
    # The discard is on top, the shown objective below it, beside the note
    # about the OTHER objective - the one that is not on this board at all.
    s.append(card_area(col_x0, disc_y0, "DISCARD",
                       ["face up; it becomes your hand", "at the recycle"],
                       glyph_pile))
    s.append(card_area(col_x0, obj_y0, "SHOWN OBJECTIVE",
                       ["face up for everyone to read"], glyph_eye))
    # THE HIDDEN OBJECTIVE HAS NO AREA, on purpose: it lives in the hand,
    # where its different back keeps it apart from the playing cards and tells
    # the table it is there without saying what it is. A printed space for it
    # would be a face-down card on the table for somebody to knock over or
    # peek at. The note sits level with the foot of the shown objective and
    # points across the gutter at it, outside the area so a card never hides it.
    note = ("keep your hidden objective in your hand \u2014 "
            "its different back sets it apart")
    note_size = 3.2
    note_y = col_bot - 2.0
    note_x1 = left_r - 7.0                         # where the text ends
    note_x0 = note_x1 - len(note) * note_size * 0.6
    s.append(T(note_x1, note_y, note, note_size, anchor="end", col=SOFT,
               mono=True, style="font-style:italic"))
    na0, na1 = note_x1 + 1.5, col_x0 - 1.5
    s.append(f'<path d="M{na0:.2f} {note_y - 1.1:.2f} L{na1 - 0.3:.2f} '
             f'{note_y - 1.1:.2f}" stroke="{SOFT}" stroke-width="0.5"/>')
    s.append(f'<path d="M{na1 - 2.4:.2f} {note_y - 2.8:.2f} L{na1:.2f} '
             f'{note_y - 1.1:.2f} L{na1 - 2.4:.2f} {note_y + 0.6:.2f}" '
             f'fill="none" stroke="{SOFT}" stroke-width="0.5" '
             f'stroke-linecap="round" stroke-linejoin="round"/>')

    # --- VICTORY ROW: five slots, wholly inside the trim -------------------
    # v0.26 print pass: the slots used to be drawn at full poker-card size,
    # 63.5 mm each, centred on the sheet - five of them are 317.5 mm on a
    # 297 mm page, so slots 1 and 5 ran off the left and right edges and all
    # five ran off the bottom. A printed component may not depend on paper it
    # does not have. The slots are now the printable width split five ways,
    # and only the strip a card's top edge covers. A card (63.5 mm) is wider
    # than its slot (about 54 mm), so neighbours overlap a little, each still
    # showing its top-left index - and the cards hang off the board's edge,
    # which is what they would do on a table anyway.
    # The card column is the tallest thing above the row now, so it decides
    # where the row starts; the left-hand zone is checked against it below.
    by = max(gv_y + gvh, score_last, note_y, col_bot) + 3.0   # divider above the row
    vlabel_y = by + 5.2
    vy = vlabel_y + 3.0                          # top of the slots
    vbot = PH - M - 1.0                          # inside the bottom trim
    pitch = (PW - 2 * M) / 5
    s.append(T(M, vlabel_y, "VICTORY ROW", 4.6, anchor="start", weight="600"))
    s.append(T(M + 36, vlabel_y, "\u2014 slide cards in from below; the centre "
               "slot scores", 3.2, anchor="start", col=SOFT, mono=True))

    # Rank order, stated as a direction: on the label's own line but at the far
    # right, clear of the sentence, so the two can never print over each other.
    lo_x = PW - M - 84
    s.append(T(lo_x, vlabel_y, "LOWEST RANK", 2.9, anchor="start",
               col=SOFT, mono=True, spacing="0.3"))
    hi_x = PW - M
    hi_w = len("HIGHEST") * 2.9 * 0.6 + 7 * 0.3
    ax0 = lo_x + len("LOWEST RANK") * (2.9 * 0.6 + 0.3) + 3
    ax1 = hi_x - hi_w - 3
    s.append(f'<line x1="{ax0:.1f}" y1="{vlabel_y-1.0:.1f}" x2="{ax1-3.4:.1f}" '
             f'y2="{vlabel_y-1.0:.1f}" stroke="{SOFT}" stroke-width="0.5"/>')
    s.append(f'<path d="M{ax1-3.6:.1f} {vlabel_y-3.0:.1f} L{ax1:.1f} '
             f'{vlabel_y-1.0:.1f} L{ax1-3.6:.1f} {vlabel_y+1.0:.1f} Z" fill="{SOFT}"/>')
    s.append(T(hi_x, vlabel_y, "HIGHEST", 2.9, anchor="end",
               col=SOFT, mono=True, spacing="0.3"))

    for k in range(5):
        cx = M + k * pitch + 0.8
        w = pitch - 1.6
        mid = (k == 2)
        s.append(f'<rect x="{cx:.2f}" y="{vy:.2f}" width="{w:.2f}" '
                 f'height="{vbot - vy:.2f}" rx="2.4" '
                 f'fill="{GOLDl if mid else PAPER}" '
                 f'{"fill-opacity=" + chr(34) + "0.55" + chr(34) + " " if mid else ""}'
                 f'stroke="{GOLD if mid else FAINT}" '
                 f'stroke-width="{1.4 if mid else 0.7}"'
                 f'{"" if mid else " stroke-dasharray=" + chr(34) + "2.5 2" + chr(34)}/>')
        s.append(T(cx + 4.0, vy + 7.0, f"{k+1}", 5.5, anchor="start",
                   col=INK if mid else FAINT, weight="600" if mid else "400"))
        if mid:
            s.append(T(cx + 11, vy + 6.7, "SCORES", 3.8, anchor="start", col=GOLDd,
                       mono=True, spacing="0.5", weight="600"))
        # WHERE THE FIRST CARD GOES. This was a line in the ON THE BOARD
        # legend; it belongs on the slot it is about.
        if k == 4:
            s.append(T(cx + 11, vy + 6.5, "fills from the right", 3.2,
                       anchor="start", col=SOFT, mono=True))
    s.append(f'<line x1="{M}" y1="{by:.2f}" x2="{PW-M}" y2="{by:.2f}" '
             f'stroke="{LINE}" stroke-width="0.4"/>')
    if vbot - vy < 12:
        raise SystemExit(f"board_a4: the victory-row slots are only "
                         f"{vbot - vy:.1f} mm tall - the lower zone grew")
    if ax1 - ax0 < 20:
        raise SystemExit("board_a4: the LOWEST RANK arrow has no room to run")
    if M + 36 + len("\u2014 slide cards in from below; the centre slot scores") * 3.2 * 0.6 > lo_x - 3:
        raise SystemExit("board_a4: the victory-row sentence runs into LOWEST RANK")

    # hard check: PROSE may not run off the sheet either. The column check
    # below never looked at text, so the setup note overflowed the margin by
    # 40 mm, printed happily, and was caught only by looking at it.
    #
    # 0.6 em per glyph, which is IBM Plex Mono's own advance - NOT a number
    # measured off a render.
    #
    # It was briefly 0.5, taken from a proof, and that let the next overflow
    # straight through. The proofs are rendered with the webfont MISSING (see
    # check_fonts.py), so every width in them belongs to whatever the renderer
    # substituted. Calibrating a monospace guard against a picture of a
    # different typeface measures the wrong thing twice.
    for line, x0, size, ly in LINES:
        w = len(line) * size * 0.6
        if x0 + w > PW - M:
            raise SystemExit(
                f"board_a4: a line of text overflows the right margin by "
                f"{x0 + w - (PW - M):.0f} mm:\n    {line[:70]}...")
        # ...and, beside the card column, may not run into it. A line that
        # starts left of the column and sits level with it ends at the gutter.
        if x0 < col_x0 and disc_y0 - 3 < ly < col_bot + 3 and x0 + w > col_x0 - 2:
            raise SystemExit(
                f"board_a4: a line of text runs {x0 + w - (col_x0 - 2):.1f} mm "
                f"into the card column:\n    {line[:70]}...")
        # ...and a line INSIDE a card area stays inside its outline.
        if x0 >= col_x0 and x0 + w > col_x1 - 2:
            raise SystemExit(
                f"board_a4: a card-area line overflows its outline by "
                f"{x0 + w - (col_x1 - 2):.1f} mm:\n    {line[:70]}...")

    # hard check: nothing may spill past the RIGHT edge of the ladder's own
    # space either, which now ends at the card column's gutter. (The --food /
    # --moves variant sheets will trip this: their extra columns need the
    # width the card column took.)
    right_edge = max(band_r, (food_x0 + food_w + 3) if FOOD else 0,
                     (moves_x0 + 12) if MOVES else 0)
    if right_edge > left_r:
        raise SystemExit(f"board_a4: the tier ladder runs "
                         f"{right_edge - left_r:.1f} mm into the card column's "
                         f"gutter")

    # ---- THE PIECES --------------------------------------------------------
    # The ring is the unit piece's size. Squeezing the ladder for room is
    # done in the gaps, and this is what stops it being done in the rings.
    if D != UNIT_PIECE:
        raise SystemExit(f"board_a4: unit rings are {D} mm; the pieces are "
                         f"{UNIT_PIECE} mm")
    if (CARD_W, CARD_H) != (63.5, 88.9):
        raise SystemExit("board_a4: the card areas are not sized for a "
                         "standard poker card (63.5 x 88.9 mm)")

    # ---- THE CARD COLUMN --------------------------------------------------
    # Each area must hold a whole poker card, in the orientation it is drawn.
    if AREA_W < CARD_H + 2 * PLAY or AREA_H < CARD_W + 2 * PLAY or PLAY < 0.5:
        raise SystemExit(f"board_a4: a card area is {AREA_W:.1f} x {AREA_H:.1f} "
                         f"mm, smaller than the {CARD_H} x {CARD_W} card it holds")
    # ...wholly inside the trim: not a millimetre of an outline may be cut off.
    if col_x0 < M + 0.5 or col_x1 > PW - M - 0.5:
        raise SystemExit("board_a4: a card area crosses the left or right trim")
    # ...under the masthead rule and clear of the corner die slot above it,
    if disc_y0 < max(mast_y, dy + DIE) + 1.0:
        raise SystemExit("board_a4: the discard area runs into the masthead or "
                         "the initiative die slot")
    # ...clear of each other,
    if obj_y0 < disc_y0 + AREA_H + 2.0:
        raise SystemExit("board_a4: the discard and objective areas overlap")
    # ...and above the victory row, so the tuck strip keeps its full width.
    if col_bot > by - 1.5:
        raise SystemExit(f"board_a4: the objective area runs "
                         f"{col_bot - (by - 1.5):.1f} mm into the victory row")
    # A card area's title is sans, not mono, so it is measured generously.
    for title in ("DISCARD", "SHOWN OBJECTIVE"):
        if 5 + len(title) * 5.2 * 0.65 > AREA_W - 5:
            raise SystemExit(f"board_a4: the {title} title overflows its area")
    # The hidden-objective note: on the sheet, out of the column, and clear of
    # the gold box and the scoring lines above it (cap height 0.7 em).
    if note_x0 < M or note_x1 > col_x0 - 2:
        raise SystemExit("board_a4: the hidden-objective note runs off its zone")
    note_top = note_y - note_size * 0.72
    if note_top < max(gv_y + gvh, score_last + 1.0) + 2.0:
        raise SystemExit("board_a4: the hidden-objective note collides with "
                         "the gold box or the scoring lines")

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
    name = "board_a4.svg" if WALL else "board_a4_nowall.svg"
    pathlib.Path(name).write_text(svg)
    print(f"wrote {name}", len(svg), "bytes")
