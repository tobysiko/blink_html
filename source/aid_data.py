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
        ("EXPLORE", FOREST, "a new tile of the card's suit · must touch TWO tiles"),
        ("ATTACK",  RED,    "a duel · your rank vs card + ground · take it: +1 gold"),
        ("CASH",    STONE,  "1 gold"),
    ]


def terrain(GOLD, FOREST, OCEAN, STONE):
    return [("Plains", GOLD, "holds 3"), ("Forest", FOREST, "2 · +1 defence"),
            ("Ocean", OCEAN, "1 · sea road"), ("Mountain", STONE, "1 · +2 defence")]


# Free actions: no card spent, any order, your own turn only.
FREE = [
    ("MOVE", "1 per meld card",
     "land: through your own tiles · sea: across empty Ocean · never an attack."),
    ("WATER", "once a turn",
     "sail onto a new Ocean tile laid on your water's coast."),
    ("RESEARCH", "",
     "with trade, twice a turn · 1 gold then 2 · draw onto the highest rank · "
     "retire lowest · take up to your rank cap."),
    ("TRADE", "",
     "one of the same two · draw the market's top two, blind · bury any two."),
    ("FORTIFY", "1 gold",
     "a coin on a unit · defends at your WALL + terrain, or a better card."),
    ("COLONY", "",
     "a victory card's B effect · one victory effect per round."),
]

TIERS = [
    # tier, units, meld, rank cap, WALL (= cap - 2)
    #
    # FOUR NUMBERS, not six. Food and ascension left the game in v0.26, and so
    # did free moves: MOVEMENT COMES FROM THE MELD now - each card you play
    # carries one - so a moves column on the ladder would be a number that
    # decides nothing. What a tier still tells you is how many cards you may
    # meld, how many units you hold, how high you may buy, and what a coin on
    # one of your units defends at.
    ("Tribe",        "2", "2", "12", "10"),
    ("Settlement",   "3", "3", "14", "12"),
    ("Kingdom",      "5", "4", "16", "14"),
    ("Empire",       "5", "5", "18", "16"),
    ("Civilization", "5", "6", "20", "18"),
]

# THE ROUND, as the table meets it. (key, what happens, who acts)
ROUND = [
    ("LAY",     "everyone lays a meld FACE DOWN", "leader first, then clockwise"),
    ("REVEAL",  "turn them all over together",    "one beat, all at once"),
    ("DECLARE", "spend a victory card on its A effect, or not",
                "leader first — you can see every meld"),
    ("RANK",    "highest total wins the trick",
                "ties: more cards, a tie-winning A, the higher victory card "
                "spent on A, highest card, earliest laid"),
    ("MAP",     "spend your meld, winner first",
                "but first see the line below"),
]

# WHAT A COIN CAN DO. (key, price, what)
COIN_USES = [
    # "1 then 2", not "1 → 2": U+2192 is NOT in the IBM Plex latin subset
    # the PDFs embed, so it depended on the renderer quietly substituting
    # some other font for that one character - and printed as an empty box
    # wherever it could not. Nothing on either aid may use a glyph the
    # face lacks; check_rules.py refuses one now.
    # ONE ALLOWANCE OF TWO, shared: research twice, trade twice, or one of
    # each, at 1 gold then 2. Printed as two separate "1 then 2" prices, the
    # pair read as two allowances of two each.
    # (the sheet prints the shared allowance once, above these two boxes)
    ("RESEARCH", "1 then 2", "retire your lowest · take a card up to your rank cap, "
                             "to hand or discard"),
    ("TRADE",    "1 then 2", "draw the market's top two, blind · bury any two back"),
    ("FORTIFY",  "1",         "on a unit: defends at WALL + terrain until a fight or "
                              "a move"),
    ("KEEP",     "—",    "gold breaks a tie at the end"),
]

# WHAT A VICTORY-ROW CARD CAN DO. One of three, then it leaves the row.
# The A wording is generated from the engine at build time, not written here.
VROW_USES = [
    ("A", "in the DECLARE step", "add its rank to your meld's total this trick"),
    ("B", "in your map phase", "found a colony — new tiles and units from the supply"),
    ("C", "in your map phase", "take 2–5 gold, by its rank band"),
]

# ---------------------------------------------------------------- new in v0.26
# The A4 sheet grew a second side for these. The folded card carries the meld
# rule and the recycle already, in one line each; these are the same facts at
# the length a sheet can afford.

# WHAT YOU MAY LAY. The game is a trick-taker and the aid did not say this
# anywhere - the single largest omission on the sheet.
MELD = {
    "rule": "ANY UNBROKEN RUN of ranks",
    "free": "duplicates free \u00b7 suits irrelevant",
    "ok":   "2-3-3-4-4",
    "bad":  "2-2-4-4",
    "why":  "no 3",
    "cap":  "up to your tier's MELD limit",
    # kept short deliberately: it shares a line with the rule itself

    "win":  "highest TOTAL takes the trick \u2014 not the longest meld",
}

# WHERE A CARD GOES. The one system with no physical tell on the table: cards
# leave your hand, and almost all of them come back. A player who does not know
# this hoards.
FLOW = [
    ("YOUR HAND",   "ten cards",        "always ten — nothing you play leaves you"),
    ("YOUR MELD",   "face down, then up", "what you lay for the trick"),
    ("THE MAP",     "settle \u00b7 explore \u00b7 attack", "or cash it for 1 gold"),
    ("YOUR DISCARD", "face up on your board", "everything you spent this cycle"),
    # "BACK TO HAND" was 2mm wider than the box it titles - the boxes are
    # (page - margins - gaps) / 5 and nothing was going to make it fit.
    ("RECYCLE",     "your discard IS your new hand", "ten cards \u00b7 nothing you play "
                                                     "ever leaves you"),
]

# What does NOT come back to you, and where it goes instead.
FLOW_ASIDE = [
    ("A victory card you spend", "leaves the row \u2014 to the MARKET"),
    ("A card bumped from a full row", "to the MARKET as well \u00b7 trade draws from it"),
    # WHERE IT GOES IS THE POINT, and it goes to YOUR OWN DISCARD. This line
    # said SHARED PILE for a day, which was the engine's behaviour and the
    # rulebook's wording and the wrong rule: the design had already reversed
    # it, because a playtester found losing the card outright too harsh.
    ("Matched the winner, lost", "one card set aside \u2014 into YOUR discard, +1 gold "
                                 "\u00b7 you meld it again next recycle"),
]

# THE RECYCLE, in order. Two steps in the base game. (The perks module adds a
# third between them; it is published separately, with its own rules.)
# PICK UP, not REFILL: you never draw cards to refill - the discard IS the hand.
RECYCLE = [
    ("WHEN", "hand empty, meld spent", "at once, mid-turn \u2014 finish your turn after"),
    ("1 \u00b7 INCOME", "with objectives", "1 gold per objective you hold right now, shown or hidden"),
    ("2 \u00b7 PICK UP", "always", "take your discard back \u2014 that IS your ten \u00b7 "
                                   "nothing is drawn"),
]

# MAP OBJECTIVES - base game as of v0.26.
OBJECTIVES = {
    "what":  "three tiles you occupy: a MIDDLE terrain with one named terrain "
             "on either side of it",
    "bend":  "the two ends need not touch each other \u2014 a bend counts exactly "
             "as a straight line",
    "deal":  "two each, dealt AFTER the starting map is laid",
    "show":  "SHOW ONE, KEEP ONE \u00b7 both score",
    "score": "2 points for every arrangement you hold at the end",
    "twice": "build it twice and it pays twice: each MIDDLE tile pays once, and "
             "an end may serve two middles",
    "cost":  "the card you show tells the table which single tile would break it",
}

# INCOME - printed since v0.26 (the engine's default whenever objectives are
# in play). It used to be drawn as a module, with crossroads income beside it
# and the hidden card paying nothing; neither is the printed rule.
INCOME = [
    ("1 GOLD PER OBJECTIVE", "at each recycle, for each of your two cards whose "
                             "pattern you hold right now \u2014 shown or hidden"),
    ("FLAT", "one coin per card, however many arrangements it has"),
    ("POINTS STILL COUNT", "income is paid at the recycle; the points are counted "
                           "at the end"),
]
