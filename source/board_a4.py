# -*- coding: utf-8 -*-
"""Blink player board, print-exact on A4 landscape.
All coordinates are millimetres; the SVG declares width/height in mm so the
PDF prints 1:1. Unit slots are 15 mm; feeding coin slots sit beside each band.
"""

import sys

from version import VTAG

# A VARIANT SHEET, not the printed board. The rulebook still carries the
# assault (§07), so a WALL column here would print a rule the book does not
# have. `--wall` makes the sheet for the proposal instead — the tier ladder the
# app plays with, 10/12/14/16/18 — so it can be put on a table and tried.
#   python3 board_a4.py            ->  board_a4.svg
#   python3 board_a4.py --wall     ->  board_a4_wall.svg
WALL = "--wall" in sys.argv
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
    step, cw, ch = 4.4, 7.0, 10.5
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


def fan_width(n):
    return (n - 1) * 4.4 + 7.0 + 5.0        # + lean overhang


# Every left-anchored mono line drawn, so the overflow check at the end can
# measure them. Collected rather than recomputed: the check should see exactly
# what was drawn.
LINES = []


def T(x, y, s, size=4.2, anchor="middle", col=INK, weight="400", mono=False,
      spacing="0", style=""):
    if mono and anchor == "start":
        LINES.append((s, x, size))
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
    # THE ROW, LEFT TO RIGHT, and every column sized from what it holds rather
    # than from a number typed here. Losing the ASCEND column freed 25 mm; it
    # goes to the meld fan, which needs room for six cards, and to the space
    # between the three groups so they read as three things.
    maxmeld = max(b[1] for b in BANDS)
    meld_w  = fan_width(maxmeld)
    meld_x0 = band_x
    cap_x0  = meld_x0 + meld_w + 5
    # WALL sits beside BUY UP TO on purpose: both are ranks, and the two
    # numbers on any row are two apart, which is the whole rule without a
    # sentence. It costs 17 mm, taken from the tier-name gap and the reserve
    # one below — see the two subtractions there.
    wall_x0 = cap_x0 + 20 if WALL else cap_x0
    name_x0 = (wall_x0 + 16) if WALL else (cap_x0 + 19)
    # The row has to end inside the margin with MOVES' heading on it, so the
    # gaps are spent from a budget rather than guessed. Widening the name gap
    # to 48 pushed MOVES 9 mm off the sheet; the food column gives it back,
    # because four coins do not need 12 mm of pitch.
    slots_x0 = name_x0 + (34 if WALL else 48)
    food_x0  = slots_x0 + slots_w + (9 if WALL else 12)
    food_w   = max(b[3] for b in BANDS)*(CD+1.5)
    moves_x0 = food_x0 + food_w + 10
    sep_x    = slots_x0 + slots_w + (4 if WALL else 6)   # units | upkeep

    s.append(T(meld_x0, top, "MELD", 3.6, anchor="start", col=SOFT, mono=True,
               spacing="0.4"))
    if WALL:
        # nine characters, start-anchored, ran straight into WALL. Centred over
        # its own card corner it clears the shield and still sits above what it
        # names — and the base sheet, which has no neighbour there, is untouched.
        s.append(T(cap_x0 + 7.5, top, "BUY UP TO", 3.6, col=SOFT, mono=True,
                   spacing="0.4"))
    else:
        s.append(T(cap_x0, top, "BUY UP TO", 3.6, anchor="start", col=SOFT,
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
    s.append(T(food_x0 + food_w/2, top, "FOOD", 4.2,
               col=GOLDd, mono=True, spacing="0.6", weight="600"))
    # "MV" was two letters nobody had to guess at once they had learned them,
    # which is a poor bargain on a board a stranger picks up.
    moves_cx = (moves_x0 + PW - M - 2) / 2      # centred in what is left
    s.append(T(moves_cx, top, "MOVES", 4.2, col=SOFT, mono=True, spacing="0.6"))

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
        s.append(T(name_x0, y-1.3, name, 4.0, anchor="start", weight="600"))
        s.append(T(name_x0, y+3.6, f"{n} units", 3.3, anchor="start",
                   col=SOFT, mono=True))
        lead_x0 = name_x0 + 34
        lead_x1 = slots_x0 - 11
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
        if coins:
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
        else:
            s.append(T(food_x0 + food_w/2, y+1.5, "free", 3.3,
                       col=SOFT, mono=True, style="font-style:italic"))
        # MOVES: a number and a stride, centred as one group under its heading.
        # The box is what made this read as another meld chip from across the
        # table; drifting left in a column two hands wide is what made it read
        # as an afterthought.
        s.append(T(moves_cx - 4.5, y+2.4, str(moves), 7.5, weight="600"))
        ax = moves_cx + 0.5
        s.append(f'<path d="M{ax:.1f} {y:.1f} l7 0 M{ax+4.6:.1f} {y-2.6:.1f} '
                 f'l2.6 2.6 l-2.6 2.6" fill="none" stroke="{SOFT}" '
                 f'stroke-width="0.8" stroke-linecap="round" '
                 f'stroke-linejoin="round"/>')
        y += band_h + 1.5

    # THE DIRECTION OF TRAVEL, once, down the whole reserve: you always take
    # from the topmost tier that still has units, and that is the one rule on
    # this board with no number to print. A faint arrow says it without a word.
    # After the loop `y` sits one band BELOW the last row, so the bottom of the
    # track is y - BAND_H/2 - 1.5. Reading that wrong put the arrowhead through
    # the glossary line.
    arr_x = slots_x0 - 6.0
    top_y = row_y - BAND_H/2 - 1
    bot_y = y - BAND_H/2 - 3
    s.append(f'<path d="M{arr_x:.1f} {top_y:.1f} L{arr_x:.1f} {bot_y-2.6:.1f}" '
             f'fill="none" stroke="{FAINT}" stroke-width="0.5"/>')
    s.append(f'<path d="M{arr_x-1.8:.1f} {bot_y-3.4:.1f} L{arr_x:.1f} {bot_y:.1f} '
             f'L{arr_x+1.8:.1f} {bot_y-3.4:.1f}" fill="none" stroke="{FAINT}" '
             f'stroke-width="0.6" stroke-linecap="round" stroke-linejoin="round"/>')

    # One rule down the row: to its left is what you hold, to its right what
    # holding it costs you every recycle.
    s.append(f'<line x1="{sep_x}" y1="{row_y-BAND_H/2:.2f}" x2="{sep_x}" '
             f'y2="{y-1.5-BAND_H/2:.2f}" '
             f'stroke="{LINE}" stroke-width="0.4"/>')

    # The column glosses used to be squeezed in here as two 3.3 mm lines that
    # could not take a third without landing on the round order. They are a
    # proper column in the lower zone now — see ON THE BOARD — which is what
    # the board is for: naming its own parts. Everything about the ORDER of a
    # turn has gone to the player aid.

    # ============ lower zone: gold, scoring, and the board's own words =====
    #
    # WHAT IS NOT HERE ANY MORE. The round order and the menu of a turn both
    # used to sit on this board, and both are now on the player aid, which is
    # in the player's hand rather than under their units and can be read
    # without leaning over the table. A board that repeats the aid is two
    # sources for one rule, and the pair drifted apart once already.
    #
    # What is left is exactly what only this board can say: what its own
    # printed words mean, and how the game is scored.
    low = y + 13.5
    s.append(f'<line x1="{M}" y1="{low-6}" x2="{PW-M}" y2="{low-6}" '
             f'stroke="{LINE}" stroke-width="0.4"/>')

    # --- three columns: gold, scoring, and what a turn may contain --------
    gx = M
    gvw, gvh = 82, 17
    sx = 106.0
    rx = 196.0

    s.append(T(gx, low, "GOLD", 4.6, anchor="start", weight="600"))

    gv_y = low + 9
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
            "+  the rank of its CENTRE card (3+ cards)",
            "3  per terrain: biggest connected stretch",
            "gold breaks ties"]):
        s.append(T(sx, low+6.4+j*4.1, line, 3.0, anchor="start",
                   col=SOFT if j == 4 else INK, mono=True, spacing="0.1"))

    # The board naming its own parts. Every word here is printed somewhere on
    # this sheet; nothing here is about the order of play.
    s.append(T(rx, low, "ON THE BOARD", 4.6, anchor="start", weight="600"))
    TERMS = ([("WALL", "a fortified unit defends here")] if WALL else []) + [
        ("MELD",        "cards you may play in a round"),
        ("BUY UP TO",   "highest rank you may take"),
        ("MOVES",       "free moves each turn"),
        ("FOOD",        "pay these slots each recycle"),
        ("ASCENSION",   "coins printed there, taken once"),
        ("RESERVE",     "empties from the top band down"),
        ("VICTORY ROW", "retired cards, fills rightwards"),
    ]
    for j, (term, gloss) in enumerate(TERMS):
        ty = low + 6.4 + j*4.1
        s.append(T(rx, ty, term, 3.0, anchor="start", col=INK, mono=True,
                   weight="600", spacing="0.1"))
        s.append(T(rx + 26, ty, gloss, 3.0, anchor="start", col=SOFT,
                   mono=True, spacing="0.1"))
    score_last = low + 6.4 + (len(TERMS) - 1)*4.1

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
    vy = PH - 16                       # only the top 16 mm sits on the board
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
    for line, x0, size in LINES:
        w = len(line) * size * 0.6
        if x0 + w > PW - M:
            raise SystemExit(
                f"board_a4: a line of text overflows the right margin by "
                f"{x0 + w - (PW - M):.0f} mm:\n    {line[:70]}...")

    # hard check: nothing may spill past the RIGHT margin either. MV is the
    # last column now that ASCEND has been folded into FOOD.
    right_edge = moves_x0 + 12
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
    name = "board_a4_wall.svg" if WALL else "board_a4.svg"
    pathlib.Path(name).write_text(svg)
    print(f"wrote {name}", len(svg), "bytes")
