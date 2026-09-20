# -*- coding: utf-8 -*-
"""What the player aids say, in one place.

TWO SHEETS READ FROM HERE: the folded 88x63 mm card (build_aid.py) and the A4
pictorial sheet (build_aid_visual.py). They are two RENDERINGS of one set of
facts, and the facts live here so they cannot drift apart.

That is not hypothetical. This project's notes already record the player board
and the FIGURE of the player board disagreeing about a column, twice, in
opposite directions - and a rulebook, a board and an aid each missing a
different number from the same ladder. Two aids maintained separately would be
the same fault with a third copy of it.

Colours are passed in rather than imported, because the folded card flips its
whole palette for the black-and-white build and the A4 sheet does not.
"""


def card_uses(GOLD, FOREST, RED, STONE):
    """The four things ONE card of your meld may do. Exactly one, per card."""
    return [
        ("SETTLE",  GOLD,   "a unit from your top tier"),
        ("EXPLORE", FOREST, "a new tile · must touch TWO · rank 10 or under pays 1 gold"),
        ("ATTACK",  RED,    "a duel · your rank vs their card + the ground"),
        ("CASH",    STONE,  "1 gold"),
    ]


def terrain(GOLD, FOREST, OCEAN, STONE):
    return [("Plains", GOLD, "holds 3"), ("Forest", FOREST, "2 · +1 defence"),
            ("Ocean", OCEAN, "1 · sea road"), ("Mountain", STONE, "1 · +2 defence")]


# Free actions: no card spent, any order, your own turn only.
FREE = [
    ("MOVE", "your tier",
     "land: across your own units · sea: across empty Ocean · never an attack."),
    ("WATER", "first sea move",
     "one free tile of ANY terrain, anywhere · touch-two applies, reach does not."),
    ("RESEARCH", "",
     "twice · 1 gold then 2 · draw onto the highest rank · retire your lowest · "
     "buy at or under your cap."),
    ("FORTIFY", "1 gold",
     "a coin on a unit · it defends at your tier's WALL, or a better card from hand."),
    ("GOLD", "",
     "free · shift coins between reserve and walls."),
    ("COLONY", "",
     "one a turn · spend a victory card on its B effect."),
]

TIERS = [
    # tier, units, meld, moves, rank cap, WALL (= cap - 2)
    # FOOD AND ASCENSION LEFT THE GAME IN v0.26, and the two columns went with
    # them. Growing costs nothing now, so there is no price to read off a tier.
    ("Tribe",        "2", "2", "1", "12", "10"),
    ("Settlement",   "3", "3", "2", "14", "12"),
    ("Kingdom",      "5", "4", "3", "16", "14"),
    ("Empire",       "5", "5", "4", "18", "16"),
    ("Civilization", "5", "6", "5", "20", "18"),
]

# THE ROUND, as the table meets it. (key, what happens, who acts)
ROUND = [
    ("LAY",     "everyone lays a meld FACE DOWN", "leader first, then clockwise"),
    ("REVEAL",  "turn them all over together",    "one beat, all at once"),
    ("DECLARE", "spend a victory card on its A effect, or not",
                "leader first — you can see every meld"),
    ("RANK",    "highest total wins the trick",
                "then most cards, then highest card, then earliest laid"),
    ("MAP",     "spend your meld, in that order",
                "winner first · set-aside and gold settle here"),
]

# WHAT A COIN CAN DO. (key, price, what)
COIN_USES = [
    ("RESEARCH", "1 → 2", "take a card at or under your tier's cap into your discard"),
    ("FORTIFY",  "1",         "stand it on a unit · it defends at your tier's WALL"),
    ("KEEP",     "—",    "gold breaks a tie at the end of the game"),
]

# WHAT A VICTORY-ROW CARD CAN DO. One of three, then it leaves the row.
# The A wording is generated from the engine at build time, not written here.
VROW_USES = [
    ("A", "in the DECLARE step", "add its rank to your meld's total this trick"),
    ("B", "in your map phase", "found a colony — new tiles and units from the supply"),
    ("C", "at any moment", "take 2–5 gold, by its rank band"),
]
