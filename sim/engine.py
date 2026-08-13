# -*- coding: utf-8 -*-
"""Blink v0.22 — rules engine.

Faithful to the v0.21 rulebook. The v0.21 redesign is the important change:
a meld competes for the trick and NOTHING MORE. There is no pattern on the
map. Each card of the meld is then spent INDEPENDENTLY, in any order, on any
cell in reach — settle a unit, explore a tile, attack, or take 1 gold — and
each card sees the map as the previous card left it.

Documented simplifications are listed in SIMPLIFICATIONS at the bottom;
everything else is implemented as written.

Coordinates are pointy-top odd-r offset (col, row).
"""
import random, itertools
from collections import Counter

TER = ("plains", "forest", "ocean", "mountain")
HOLDS = {"plains": 3, "forest": 2, "ocean": 1, "mountain": 1}

# Optional: population limits that GROW with the tile owner's band, instead of
# being fixed per terrain. One dict per band (Founding, Growth, Expansion,
# Empire). Set Game.LIMIT_LADDER to a key of LADDERS to switch one on; None
# keeps the fixed HOLDS above. The limit that applies to a tile is always the
# TILE OWNER's, so two players may legally stack the same terrain differently.
LADDERS = {
    # flat start, everything stackable by Empire
    "flat_wide": [
        {"plains": 1, "forest": 1, "ocean": 1, "mountain": 1},
        {"plains": 2, "forest": 2, "ocean": 1, "mountain": 1},
        {"plains": 3, "forest": 2, "ocean": 1, "mountain": 1},
        {"plains": 4, "forest": 3, "ocean": 2, "mountain": 2},
    ],
    # gentler: opens sooner, tops out near today's numbers
    "gentle": [
        {"plains": 2, "forest": 1, "ocean": 1, "mountain": 1},
        {"plains": 2, "forest": 2, "ocean": 1, "mountain": 1},
        {"plains": 3, "forest": 2, "ocean": 1, "mountain": 1},
        {"plains": 3, "forest": 3, "ocean": 2, "mountain": 2},
    ],
}
ATTACK_COST = {"plains": 0, "ocean": 0, "forest": 1, "mountain": 2}
BAG_EACH = 15

# Combination melds: two multi-card melds played together if they fit the
# meld limit. Module-level because enumerate_melds is a free function.
# pair+pair and 3+2 are excluded -- "twoset" already covers those.
COMBO_MELDS = False

# tier -> (name, units, meld limit, food per recycle, free moves,
#          ascension coins taken once on arrival, rank cap when buying)
# food is NOT cumulative; free moves refresh every map phase
BANDS = [("Tribe",        2, 2, 0, 1, 0, 11),
         ("Settlement",   4, 3, 1, 2, 1, 13),
         ("Kingdom",      5, 4, 2, 3, 2, 15),
         ("Empire",       5, 5, 3, 4, 3, 17),
         ("Civilization", 4, 6, 4, 5, 4, 20)]

STARTS = {
    2: ([(1, 0), (2, 0)], [(0, 0), (3, 0)]),
    3: ([(1, 3), (2, 2), (2, 3)], [(0, 3), (2, 1), (3, 4)]),
    4: ([(1, 2), (2, 2), (2, 3), (3, 3)], [(0, 2), (2, 1), (2, 4), (4, 3)]),
}



# --------------------------------------------------------------- geometry
DIRS = ("E", "NE", "SE", "W", "NW", "SW")
OPPOSITE = {"E": "W", "W": "E", "NE": "SW", "SW": "NE", "NW": "SE", "SE": "NW"}


def step(cell, d):
    """The cell adjacent to `cell` in direction `d` (pointy-top, odd-r offset)."""
    c, r = cell
    odd = r & 1
    return {
        "E":  (c + 1, r),
        "W":  (c - 1, r),
        "NE": (c + odd, r - 1),
        "NW": (c - 1 + odd, r - 1),
        "SE": (c + odd, r + 1),
        "SW": (c - 1 + odd, r + 1),
    }[d]


def nbrs(c, r):
    return {step((c, r), d) for d in DIRS}


class Tile:
    """One physical hex. Fixed position, six neighbour slots, and whatever is
    standing on it. Nothing about a tile is stored anywhere else."""
    __slots__ = ("cell", "terrain", "units", "gold", "link", "m")

    def __init__(self, cell, terrain, m=None):
        self.cell = cell
        self.terrain = terrain
        self.m = m             # owning Map, so capacity can read the owner's band
        self.units = []        # owner ids; a tile is single-owner while occupied
        self.gold = 0          # fortification coins, at most one per unit
        self.link = {d: None for d in DIRS}   # direction -> Tile, or None if unexplored

    # --- what is standing here -----------------------------------
    @property
    def owner(self):
        return self.units[0] if self.units else None

    def capacity_for(self, seat):
        """How many units SEAT may stack here. With a ladder in play this is
        the seat's own band; otherwise the fixed terrain value."""
        if self.m is None or self.m.limits is None or seat is None:
            return HOLDS[self.terrain]
        return self.m.limits[self.m.band_of(seat)][self.terrain]

    @property
    def capacity(self):
        """The ceiling the INVARIANT checks against.

        With a ladder in play this is the widest limit any band grants, not the
        owner's current one, because limits gate PLACEMENT only. A stack built
        legally at Empire stays standing if its owner later regresses a band —
        the alternative is culling your own people every time you lose ground,
        which starvation already does once. See findings-limits.md."""
        if self.m is None or self.m.limits is None:
            return HOLDS[self.terrain]
        return max(b[self.terrain] for b in self.m.limits)

    def has_room(self, p):
        return (self.owner in (None, p)) and len(self.units) < self.capacity_for(p)

    # --- graph ---------------------------------------------------
    def neighbours(self):
        return [t for t in self.link.values() if t is not None]

    def empty_slots(self):
        return [step(self.cell, d) for d in DIRS if self.link[d] is None]

    def __repr__(self):
        return f"<{self.terrain[:4]} {self.cell} u={self.units} g={self.gold}>"



# --------------------------------------------------------------- melds
def enumerate_melds(hand, limit):
    """Every legal v0.22 meld from this hand, up to `limit` cards.

    THE RULE: the ranks of the cards must form an unbroken run — every rank
    between the lowest and the highest must be present. Duplicates of any rank
    are free and suits are irrelevant. One card is always legal.

    Enumerated by brute force over combinations, which is exact and cheap: a
    ten-card hand at limit 6 is about a thousand candidates. The old
    taxonomy-driven enumerator is gone with the taxonomy.

    Returns (kind, payload) pairs to keep the bot interface unchanged; kind is
    always "run" now.
    """
    out = []
    n = min(limit, len(hand))
    for k in range(1, n + 1):
        for combo in itertools.combinations(sorted(hand), k):
            ranks = {c[0] for c in combo}
            if max(ranks) - min(ranks) + 1 == len(ranks):
                out.append(("run", tuple(combo)))
    return out


def is_legal_meld(cards):
    """The rule itself, for tests and for the invariant check."""
    if not cards:
        return False
    ranks = {c[0] for c in cards}
    return max(ranks) - min(ranks) + 1 == len(ranks)


def hand_power(cards):
    """How much trick-winning material a hand holds.

    Measured, the property that predicts results is ADJACENCY, not rank height:
    four 10s make one meld and no runs, while 8-9-10 across suits makes runs and
    sets everywhere. See findings-starting-hand.md.
    """
    cnt = Counter(c[0] for c in cards)
    v = 0.0
    for r, k in cnt.items():
        v += 1.4 * (k - 1)                       # pairs and better
        if cnt.get(r + 1):
            v += 1.0 * min(k, cnt[r + 1])        # neighbours meld
    v += 0.03 * sum(c[0] for c in cards)         # ranks break ties and score
    v += 0.25 * len({c[1] for c in cards})       # suit spread: terrain reach
    return v


def draft_pick(kept, offered, need):
    """Keep the cards that most improve the hand, greedily. A human drafts for
    combinations; keeping at random was the sim's weakest assumption."""
    picks = []
    pool = list(offered)
    for _ in range(min(need, len(pool))):
        best, bv = None, -1e9
        for c in pool:
            v = hand_power(kept + picks + [c])
            if v > bv:
                best, bv = c, v
        picks.append(best)
        pool.remove(best)
    return picks


def meld_cards(kind, payload):
    return tuple(payload)


def meld_size(kind, payload):
    return len(payload)

class Map:
    """The board: a graph of Tile objects. Adding a tile wires it to its
    neighbours in both directions; nothing else may touch `tiles`."""

    def __init__(self, n):
        mts, pls = STARTS[n]
        self.limits = None          # None = fixed HOLDS; else a LADDERS entry
        self.band_of = lambda seat: 0   # replaced by Game once players exist
        self.tiles = {}
        for c in mts:
            self._add(c, "mountain")
        for c in pls:
            self._add(c, "plains")
        self.starts = list(pls)
        for i, c in enumerate(pls):
            self.tiles[c].units.append(i)
        # An open supply: every unused tile is visible and may be taken freely
        # until that terrain runs out. No bag, no face-up tile market.
        self.supply = Counter({t: BAG_EACH for t in TER})
        for t in self.tiles.values():
            self.supply[t.terrain] -= 1

    # --- structure ------------------------------------------------
    def _add(self, cell, terrain):
        t = Tile(cell, terrain, self)
        self.tiles[cell] = t
        for d in DIRS:
            other = self.tiles.get(step(cell, d))
            if other is not None:
                t.link[d] = other
                other.link[OPPOSITE[d]] = t
        return t

    def check_graph(self):
        """Neighbour links are symmetric and agree with the geometry."""
        for t in self.tiles.values():
            for d, u in t.link.items():
                if u is None:
                    assert step(t.cell, d) not in self.tiles, \
                        f"{t.cell} missing link {d}"
                else:
                    assert u.cell == step(t.cell, d), f"{t.cell} bad link {d}"
                    assert u.link[OPPOSITE[d]] is t, f"{t.cell} link {d} not mutual"
            assert len(set(t.units)) <= 1, f"{t.cell} has two owners"
            assert len(t.units) <= t.capacity, f"{t.cell} overstacked"
            assert 0 <= t.gold <= len(t.units), f"{t.cell} has stray fortification"

    # --- queries --------------------------------------------------
    @property
    def terr(self):
        return {c: t.terrain for c, t in self.tiles.items()}

    def legal_spaces(self):
        """Empty slots touching at least two tiles (v0.20 §06)."""
        cand = set()
        for t in self.tiles.values():
            cand.update(t.empty_slots())
        return {c for c in cand if len(nbrs(*c) & set(self.tiles)) >= 2}

    def tile_available(self, suit):
        return self.supply[suit] > 0

    def owner(self, c):
        t = self.tiles.get(c)
        return t.owner if t else None

    def civ(self, p):
        return {c for c, t in self.tiles.items() if t.owner == p}

    def cell_actions(self, c, suit, p, spaces, budget):
        t = self.tiles.get(c)
        if t is not None:
            if t.terrain != suit:
                return []
            if t.owner in (None, p):
                return ["settle"] if t.has_room(p) else []
            return ["attack"] if budget >= ATTACK_COST[t.terrain] else []
        if c in spaces and self.tile_available(suit):
            return ["explore"]
        return []

    # --- mutations ------------------------------------------------
    def do_explore(self, c, suit):
        """Take a tile of `suit` from the open supply. False if that terrain is
        exhausted - a tile can never come from nothing."""
        if self.supply[suit] <= 0:
            return False
        self.supply[suit] -= 1
        self._add(c, suit)
        return True

    def settle(self, c, p):
        t = self.tiles[c]
        if t.gold:                      # "stacked onto" disturbs the unit
            t.gold = 0
        t.units.append(p)

    def take_unit_off(self, c):
        """Pull one unit off a tile (starvation, not combat). A fortification
        coin cannot outlive the unit it was protecting."""
        t = self.tiles[c]
        u = t.units.pop() if t.units else None
        t.gold = min(t.gold, len(t.units))
        return u

    def fortify(self, c):
        t = self.tiles[c]
        if t.units and t.gold < len(t.units):
            t.gold += 1
            return True
        return False

    def remove_unit(self, c):
        """An attack takes the fortifying gold if there is one, else a unit.
        Returns the owner whose unit was removed, or None if gold absorbed it."""
        t = self.tiles[c]
        if t.gold:
            t.gold -= 1
            return None
        return t.units.pop() if t.units else None


# --------------------------------------------------------------- placement
def adjacent(m, cell):
    """Neighbouring cells, walked through the tile graph where one exists.

    A meld's pattern is a walk over cells, and a cell is either a Tile or an
    empty slot beside one. From a Tile we follow its six links (and its empty
    slots); only from an empty slot, which has no object yet, do we fall back
    to the coordinate arithmetic.
    """
    t = m.tiles.get(cell)
    if t is not None:
        return [u.cell for u in t.neighbours()] + t.empty_slots()
    return sorted(nbrs(*cell))


def reach(m, p_i, civ=None):
    """Every cell a card of yours may act on (v0.21 §06 rule 1).

    A tile you occupy, or any tile / legal empty space adjacent to one you
    occupy. Melds no longer walk patterns, so this is the whole geometry.
    """
    civ = m.civ(p_i) if civ is None else civ
    spaces = m.legal_spaces()
    out = set(civ)
    for c in civ:
        for u in adjacent(m, c):
            if u in m.tiles or u in spaces:
                out.add(u)
    return out


def card_options(m, card, p, gold, reachable=None, spaces=None):
    """Every legal (cell, action) for ONE card, judged against the map NOW.

    Cards resolve one at a time and each sees the map the previous card left,
    so this is always called fresh — a tile explored by card 1 is settleable
    by card 2.
    """
    spaces = m.legal_spaces() if spaces is None else spaces
    reachable = reach(m, p) if reachable is None else reachable
    suit = card[1]
    out = []
    for c in sorted(reachable):
        for a in m.cell_actions(c, suit, p, spaces, gold):
            out.append((c, a))
    return out


def piece_placements(*a, **k):
    """Removed in v0.21 — melds no longer land as patterns.

    Kept as a loud failure rather than deleted, because several v0.20 scripts
    import it and a silent empty list would look like 'no legal placement'
    instead of 'this script has not been ported'.
    """
    raise NotImplementedError(
        "piece_placements is a v0.20 pattern-placement API; v0.21 spends each "
        "card independently — use card_options()")


# --------------------------------------------------------------- player
class Player:
    def __init__(self, i):
        self.i = i
        self.hand = []
        self.discard = []
        self.gold = 0
        self.reserve = [b[1] for b in BANDS]     # units left in each band
        self.vrow = []
        self.played = ()
        self.kind = None
        self.bonus = 0
        self.ties = False
        self.spent_a = 0
        self.a_band = None
        self.reached = 0           # highest tier index whose ascension is paid

    def band(self):
        for j, n in enumerate(self.reserve):
            if n > 0:
                return j
        return len(BANDS) - 1

    def meld_limit(self):
        return BANDS[self.band()][2]

    def rank_cap(self):
        """Highest rank this tier may BUY from the market (§10). Not a holding
        rule — cards already yours stay yours."""
        return BANDS[self.band()][6]

    def ascension_due(self):
        """Coins owed for tiers reached for the first time. Called after every
        unit leaves the reserve; pays once per tier, ever."""
        owed = 0
        j = self.band()
        while self.reached < j:
            self.reached += 1
            owed += BANDS[self.reached][5]
        return owed

    def food(self):
        """Coins your people eat at the next recycle (this band only)."""
        return BANDS[self.band()][3]

    # v0.20 called this upkeep; kept so old scripts still read
    upkeep = food

    def free_moves(self):
        return BANDS[self.band()][4]

    def take_unit(self):
        j = self.band()
        if self.reserve[j] > 0:
            self.reserve[j] -= 1
            return True
        return False

    def collect_ascension(self):
        """Take any ascension coins now owed. Returns the amount."""
        return self.ascension_due()

    def return_unit(self):
        """A returned unit goes back to the band it came from - the LOWEST band
        with a free slot, i.e. the one most recently emptied. Regression is one
        step, not a reset to Founding."""
        for j in range(len(BANDS) - 1, -1, -1):
            cap = BANDS[j][1]
            if self.reserve[j] < cap:
                self.reserve[j] += 1
                return True
        return False

    def reserve_empty(self):
        return sum(self.reserve) == 0

    def cards_total(self):
        return len(self.hand) + len(self.discard) + len(self.played)


# --------------------------------------------------------------- game
class Game:
    def __init__(self, n, seed=0, bot=None):
        random.seed(seed)
        self.n = n
        self.m = Map(n)
        self.P = [Player(i) for i in range(n)]
        self.bot = bot or random_bot
        self.smart = False          # set True to use the placement policy
        self.round = 0
        self.stats = Counter()
        self.ledger = []   # (round, seat, phase, kind, coins)
        self.trace = []          # (round, seat, band, units_on_map)
        self.log = []
        self.ended_on = None
        self.final_rounds = None
        self.pro = set()             # seats using the stronger policies (pro_bot)
        # per-seat policy overrides, so one player can be given a different
        # strategy and played head to head against the house bot.
        self.greed = {}              # seat -> weight on the hand you KEEP
        self.retire_w = {}           # seat -> weight on rank when retiring
        self.gain_w = {}             # seat -> weight on the row's real gain
        self.move_policy = {}        # seat -> threat | patch
        self.c_first = {}            # seat -> pay from the victory row first
        self.phase_play = {}         # seat -> play the two-phase strategy
        self.pile = []               # shared face-down discard pile (§04, §09)
        self.removed = []            # cards spent on effects; out of the game
        # per-tier population limits (optional); the tile OWNER's band applies
        self.m.limits = LADDERS[self.LIMIT_LADDER] if self.LIMIT_LADDER else None
        self.m.band_of = lambda seat: self.P[seat].band()
        for pl in self.P:            # the unit each player starts on the map
            pl.take_unit()           # comes out of the Founding band
        self._deal()

    # --- setup ---------------------------------------------------
    def _deal(self):
        n = self.n
        if n == 2:
            sr, ar = range(6, 11), range(11, 16)
        elif n == 3:
            sr, ar = range(3, 11), range(11, 19)
        else:
            sr, ar = range(1, 11), range(11, 21)
        if self.FULL_ADV_DECK:
            # The rank caps (11/13/15/17/20) only mean anything if the market
            # actually reaches above them. A 2p deck of 11-15 is entirely under
            # Kingdom's cap, so three of the five caps were decorative.
            ar = range(11, 21)
        start = [(r, s) for r in sr for s in TER]
        adv = [(r, s) for r in ar for s in TER]
        if n == 3:                                # three-player suit balance
            threes = [c for c in start if c[0] == 3]
            keep = random.sample(threes, 2)
            start = [c for c in start if c[0] != 3] + keep
            missing = [s for s in TER if s not in [c[1] for c in keep]]
            adv = [c for c in adv if not (c[0] == 18 and c[1] in missing)]
        random.shuffle(start)
        hands = [start[i*10:(i+1)*10] for i in range(n)]
        # draft: cumulative keeps of 4, 6, 8, 10
        kept = [[] for _ in range(n)]
        for target in (4, 6, 8, 10):
            for i in range(n):
                need = target - len(kept[i])
                if i in self.pro and self.PRO_DRAFT:
                    picks = draft_pick(kept[i], hands[i], need)
                else:
                    random.shuffle(hands[i])
                    picks = hands[i][:need]
                kept[i] += picks
                hands[i] = [c for c in hands[i] if c not in picks]
            hands = [hands[(i - 1) % n] for i in range(n)]
        for i in range(n):
            self.P[i].hand = kept[i]
        self.card_total = len(start) + len(adv)
        # v0.22: ONE shuffled upgrade deck, and a face-up 2x3 grid.
        # Each grid position is a STACK — a drawn card is placed on top of one,
        # burying what was under it until the top card is taken.
        self.deck = list(adv)
        random.shuffle(self.deck)
        self.grid = [[self.deck.pop()] if self.deck else []
                     for _ in range(self.MARKET_GRID)]
        self.leader = 0

    # --- one round -----------------------------------------------
    def play_round(self):
        self.round += 1
        order = [(self.leader + k) % self.n for k in range(self.n)]

        table = []                                  # (seat, i) in play order
        for seat, i in enumerate(order):            # card phase
            p = self.P[i]
            melds = enumerate_melds(p.hand, p.meld_limit())
            kind, payload = self.bot(self, p, "meld", melds)
            p.kind, p.played = kind, payload
            p.combo_parts = payload if kind == "combo" else None
            p.bonus, p.ties, p.spent_a, p.a_band = 0, False, 0, None
            self.stats[f"meld_{meld_size(kind, payload)}"] += 1
            self.stats[f"shape_{kind}"] += 1
            self.stats[f"limit_{p.meld_limit()}"] += 1
            for c in meld_cards(kind, payload):
                p.hand.remove(c)
            table.append((seat, i))
            if self.smart and self.USE_EFFECT_A:
                self._maybe_declare_a(p, table)      # in the open, as you play

        def key(t):
            """v0.22: most cards, then highest card, then next-highest, and so
            on; earliest played breaks what is left. There are never ties."""
            seat, i = t
            p = self.P[i]
            ties = p.ties
            if self.TIE_RULE == "topband":
                ties = ties and p.spent_a >= 16
            tiebreak = 0 if self.TIE_RULE == "earliest" else -p.spent_a
            ranks = sorted((c[0] for c in meld_cards(p.kind, p.played)),
                           reverse=True)
            # negated so "bigger is better" sorts first; padded so a shorter
            # meld never compares past its own length
            lex = tuple(-r for r in ranks)
            return (-(meld_size(p.kind, p.played) + p.bonus),
                    -int(ties), tiebreak, lex, seat)
        ranked = sorted(list(enumerate(order)), key=key)
        winner = ranked[0][1]
        # optional instrumentation hook; no effect unless a caller sets it
        if getattr(self, "on_trick", None):
            self.on_trick(self, order, key, winner)
        for _, i in table:
            q = self.P[i]
            if q.a_band is not None:
                self.stats[f"a_band_{q.a_band}_win"] += int(i == winner)

        loser = ranked[-1][1]                       # worst meld this trick
        # capture BEFORE the map phase: the winner acts first and clears their
        # played tuple, so reading it inside the loop always returned 0 and the
        # match-discard rule silently never fired.
        win_size = meld_size(self.P[winner].kind, self.P[winner].played)
        for pos, (seat, i) in enumerate(ranked):    # map phase
            p = self.P[i]
            cards = list(meld_cards(p.kind, p.played))
            spent = list(cards)          # everything that goes to the discard
            if self.WINNER_BONUS_CARD:
                # nobody is docked a card; the WINNER gets one extra instead
                use = list(cards)
                gained = 0
                # the catch-up coin, without docking anyone a card
                pays = (self.LOSER_CONSOLATION == "all" and i != winner) or \
                       (self.LOSER_CONSOLATION == "last" and i == loser
                        and i != winner)
                if pays:
                    amt = self.CONSOLATION_GOLD
                    p.gold += amt
                    self.coins(p, "map", "gain: lost the trick", amt)
                    self.stats["gold_in_lost_trick"] += amt
                    self.stats["consolation_paid"] += amt
                if i == winner and self.GIVE_BONUS_CARD:
                    bonus = self._pick_bonus(p)
                    if bonus is not None:
                        p.hand.remove(bonus)
                        use.append(bonus)
                        spent.append(bonus)
                        self.stats["bonus_card"] += 1
                    else:                # hand empty: take the consolation coin
                        p.gold += 1
                        self.coins(p, "map", "gain: bonus (no cards left)", 1)
                        self.stats["bonus_gold"] += 1
                # v0.22: matching the winner's card count and losing costs a
                # card from hand, face down, to the shared pile. Playing FEWER
                # costs nothing — this is "one card less than the winner" made
                # explicit rather than enforced by docking.
                if (i != winner and self.MATCH_DISCARD
                        and len(cards) == win_size and p.hand):
                    drop = (self._pick_discard(p) if self.smart
                            else random.choice(p.hand))
                    p.hand.remove(drop)
                    self.pile.append(drop)
                    self.stats["match_discard"] += 1
            else:
                use = list(cards) if i == winner else self._drop_one(p)
                gained = len(cards) - len(use)
                p.gold += gained
                self.coins(p, "map", "gain: unused cards", gained)
                self.stats["gold_in_lost_trick"] += gained
                self.stats["cards_to_gold"] += gained
            self.stats["cards_played"] += len(cards)
            self._place(p, use)
            p.discard.extend(spent)
            p.played = ()
            # v0.22: your hand refills the MOMENT it empties, not at the end of
            # the turn. You pick everything back up straight away and still take
            # your research this turn — so playing your whole hand no longer
            # silently costs you the upgrade.
            # v0.22 question: moves before or after the meld? Before, a free
            # move extends your REACH for this turn's cards — march or sail up
            # to a rival, then play the card that kills. After, the unit always
            # arrives once the shooting is over.
            if self.smart and self.c_first.get(p.i, self.C_FIRST):
                # Top up from the ROW before the map phase, so a coin needed for
                # food is bought with a victory card rather than with a card
                # that was about to settle a unit. Without this the comparison
                # is rigged: _place always gets first refusal on the shortfall.
                self._maybe_cash_c(p, ahead=True)
            if self.smart and self.USE_MOVES and self.MOVE_TIMING == "before":
                self._free_moves(p, use)
            if self.IMMEDIATE_REFILL and not p.hand:
                if self.smart and self.USE_RECLAIM:
                    self._reclaim_for_food(p)
                self._recycle(p)
            self._maybe_upgrade(p)
            if self.smart and self.USE_EFFECT_B:
                self._maybe_use_b(p)
            if self.smart:
                self._maybe_cash_c(p)
            if self.smart and self.USE_EFFECT_D:
                self._maybe_use_d(p)
            if self.smart and self.USE_MOVES and self.MOVE_TIMING != "before":
                self._free_moves(p)
            if self.smart and self.USE_FORTIFY:
                self._maybe_fortify(p)
            if not p.hand:                   # still empty: refill at end of turn
                if self.smart and self.USE_RECLAIM:
                    self._reclaim_for_food(p)
                self._recycle(p)

        for pl in self.P:
            self.stats["peak"] = max(self.stats["peak"], pl.gold)
            self.trace.append((self.round, pl.i, pl.band(),
                               sum(t.units.count(pl.i) for t in self.m.tiles.values())))
        self.stats["recycles"] += 0
        self.leader = winner
        self._check_end()

    def _pay_ascension(self, p):
        """Reaching a tier for the first time pays its printed coins (§04)."""
        if not self.USE_ASCENSION:
            return
        owed = p.collect_ascension()
        if owed:
            p.gold += owed
            self.coins(p, "map", "gain: ascension", owed)
            self.stats["gold_in_ascension"] += owed
            self.stats["ascensions"] += 1

    def _pick_discard(self, p):
        """Which card to give up when you matched the winner and lost.

        Shed the card that contributes least to future melds — the one whose
        removal costs the least hand_power. Cheap and good enough."""
        if not p.hand:
            return None
        best, bv = None, -1e9
        for c in p.hand:
            rest = [x for x in p.hand if x is not c]
            v = hand_power(rest)
            if v > bv:
                best, bv = c, v
        return best

    def _pick_bonus(self, p):
        """The extra card the trick winner spends (WINNER_BONUS_CARD).

        Returns None if the hand is empty — the caller then pays a coin
        instead, which is the whole point of that clause: a winner who just
        emptied their hand is not left with nothing."""
        if not p.hand:
            return None
        if not self.smart:
            return random.choice(p.hand)
        spaces = self.m.legal_spaces()
        reachable = (reach(self.m, p.i) if self.m.civ(p.i)
                     else set(self.m.tiles) | spaces)
        best, best_v = None, -1e9
        for c in p.hand:
            opts = card_options(self.m, c, p.i, p.gold, reachable, spaces)
            v = max([value_card(self, p, cell, c, a) for cell, a in opts]
                    + [self.CASH_THRESHOLD])
            if v > best_v:
                best, best_v = c, v
        return best

    def _drop_one(self, p):
        cards = list(meld_cards(p.kind, p.played))
        if p.kind == "straight":
            s = sorted(cards)
            return random.choice([s[1:], s[:-1]])
        c = random.choice(cards)
        out = list(cards)
        out.remove(c)
        return out

    def _place(self, p, cards):
        """Spend each card of the meld INDEPENDENTLY (v0.21 §06).

        No pattern, no shape, no ordering constraint. The bot picks the card
        order too: it resolves whichever card is worth the most right now, so
        an explore can deliberately open ground that a later card settles.
        """
        if not cards:
            return
        todo = list(cards)
        while todo:
            # reach and legal spaces are recomputed every card, because the
            # previous card may have grown the map or emptied a tile
            exempt = not self.m.civ(p.i)          # re-entry rule (§06)
            spaces = self.m.legal_spaces()
            if exempt:
                reachable = set(self.m.tiles) | spaces
            else:
                reachable = reach(self.m, p.i)

            best = None                            # (value, card, cell, act)
            for card in todo:
                opts = card_options(self.m, card, p.i, p.gold, reachable, spaces)
                for cell, act in opts:
                    v = (value_card(self, p, cell, card, act) if self.smart
                         else random.random())
                    if best is None or v > best[0]:
                        best = (v, card, cell, act)
            if best is None:                       # nothing legal for any card
                self.stats["no_legal_placement"] += len(todo)
                self.stats["gold_in_unplaceable"] += len(todo)
                self.stats["cards_to_gold"] += len(todo)
                p.gold += len(todo)
                self.coins(p, "map", "gain: unplaceable", len(todo))
                return

            _, card, cell, act = best
            todo.remove(card)

            # cashing on purpose: v0.21 makes gold a first-class use of a card,
            # not a fallback. The bot cashes when the map is worth less than a
            # coin, or when food is not yet covered.
            if self.smart and self.CASH_FOR_FOOD:
                thr = self.CASH_THRESHOLD
                if p.i in self.pro and self.PRO_CASH:
                    # a coin is worth more when food is uncovered or an upgrade
                    # is one coin away; worth less when the map is contested
                    thr = 0.8
                    if p.gold < p.food() + 1:
                        thr = 2.2
                    elif p.gold >= 3:
                        thr = 0.4
                    ph = self.phase_of(p)
                    if ph is not None:
                        # early, a card is worth more on the map than as a coin;
                        # late, coins buy the research that banks rank
                        thr *= (self.PHASE_CASH_EARLY
                                + (1 - self.PHASE_CASH_EARLY) * ph)
                if best[0] < thr or p.gold < p.food():
                    # what did this coin actually cost? `best[0]` is the value
                    # of the best map action this card could have taken. The
                    # bot cashes the cards worth least, so the marginal cost of
                    # a coin is far below "one unit not placed".
                    self.stats["cash_value_x100"] += int(best[0] * 100)
                    self.stats["cash_events"] += 1
                    if best[3] == "settle":
                        self.stats["cash_gave_up_a_settle"] += 1
                    self.stats["cards_to_gold"] += 1
                    self.stats["gold_in_cashed"] += 1
                    p.gold += 1
                    self.coins(p, "map", "gain: cashed", 1)
                    continue

            self.stats["cards_resolved"] += 1
            if act == "explore":
                if self.m.do_explore(cell, card[1]):
                    self.stats["explore"] += 1
                else:
                    self.stats["explore_no_tile"] += 1
                    self.stats["gold_in_other"] += 1
                    self.stats["cards_to_gold"] += 1
                    p.gold += 1
                    self.coins(p, "map", "gain: no tile left", 1)
            elif act == "settle":
                if (self.USE_HOLD_BACK and not p.reserve_empty()
                        and self._would_climb(p)
                        and p.gold < self._next_food(p)):
                    self.stats["held_back"] += 1    # take gold rather than climb
                    self.stats["cards_to_gold"] += 1
                    self.stats["gold_in_other"] += 1
                    p.gold += 1
                    self.coins(p, "map", "gain: held back", 1)
                elif p.take_unit():
                    self.stats["settle"] += 1
                    self.m.settle(cell, p.i)
                    self._pay_ascension(p)
                else:
                    self.stats["settle_no_reserve"] += 1
                    self.stats["gold_in_other"] += 1
                    self.stats["cards_to_gold"] += 1
                    p.gold += 1
                    self.coins(p, "map", "gain: no reserve", 1)
            elif act == "attack":
                tile = self.m.tiles[cell]
                cost = ATTACK_COST[tile.terrain]
                if p.gold >= cost and tile.units:
                    p.gold -= cost
                    self.coins(p, "map", "spend: attack", cost)
                    self.stats["gold_out_attack"] += cost
                    victim = self.m.remove_unit(cell)
                    if victim is None:
                        self.stats["absorbed_by_fortification"] += 1
                    else:
                        self.stats["killed_by_attack"] += 1
                        self.P[victim].return_unit()
                else:
                    if tile.units:
                        self.stats["attack_no_gold"] += 1   # could not pay the terrain
                    p.gold += 1
                    self.stats["cards_to_gold"] += 1

    def _split(self, kind, cards, payload=None):
        if kind == "combo":
            # the components must be passed in: a lost trick drops a card, and a
            # flat list of cards cannot be decomposed back into components
            # unambiguously (7,7,8,9 is pair+run or run+stray).
            out = []
            for comp in (payload or ()):
                keep = [c for c in comp if c in cards]
                if keep:
                    out.append((keep, len({c[0] for c in keep}) > 1))
            return out
        if kind == "twoset":
            byr = {}
            for c in cards:
                byr.setdefault(c[0], []).append(c)
            return [(v, False) for v in byr.values() if v]
        return [(list(cards), kind == "straight")]

    def grid_top(self, k):
        return self.grid[k][-1] if self.grid[k] else None

    def _vrow_gain(self, p, card):
        """Points the victory row would gain from retiring this card (§13).

        The row scores its THIRD-HIGHEST rank once it holds three cards, so a
        single tall card among short ones is worth nothing and the marginal
        value of any retirement depends on what is already in the row.
        """
        row = sorted(c[0] for c in p.vrow)
        before = vrow_score(row)
        new = sorted(row + [card[0]])
        after = vrow_score(new)
        return after - before

    def _retirable(self, p):
        """Which cards in hand this player is ALLOWED to retire.

        RETIRE_ASCENDING: each retirement must outrank the one before it, so a
        row is built from the bottom up and a tall card cannot be dumped early.
        RETIRE_UNDER_CAP: you may only retire at or below your tier's rank cap —
        the same printed number that limits buying, reused as "what you have
        outgrown".
        """
        legal = list(p.hand)
        if self.RETIRE_LOWEST_N:
            # "shed something you have outgrown": the choice is restricted to
            # your N weakest cards, so a purchase can never be dumped straight
            # back out. N=1 removes the decision; N=3 keeps a real one.
            legal = sorted(legal, key=lambda c: c[0])[:self.RETIRE_LOWEST_N]
        if self.RETIRE_ASCENDING and p.vrow:
            top = max(c[0] for c in p.vrow)
            legal = [c for c in legal if c[0] > top]
        if self.RETIRE_UNDER_CAP:
            cap = p.rank_cap()
            legal = [c for c in legal if c[0] <= cap]
        return legal

    def _pick_retire(self, p):
        """Which card to send to the victory row.

        v0.22: only cards still in HAND may be retired — a card played to the
        table is spent, and spending it twice was the old engine's free lunch.
        That makes retirement a real cost, so the choice is a trade: what the
        row gains in points against what the hand loses in trick-winning
        material.

        MEASURED: weighing the row against hand_power the way the draft does
        LOSES to plain max-rank (26.7% vs 33.3% chance, 60 games). The row is
        worth far more than the hand material it costs, because a hand recycles
        every few rounds while the row is permanent and the rank cap makes tall
        cards scarce. So rank leads; hand_power only breaks ties.
        """
        if not p.hand:
            return None
        legal = self._retirable(p)
        if not legal:
            self.stats["retire_blocked"] += 1
            return None
        if not self.smart:
            return min(legal, key=lambda c: c[0])
        best, bv = None, -1e9
        for c in legal:
            rest = [x for x in p.hand if x != c]
            # the two row terms are independent: `retire_w` weighs raw rank,
            # `gain_w` weighs what the row ACTUALLY gains under the current
            # scoring rule. Tying them together made every scoring variant
            # behave identically, which is not a result but a wiring fault.
            rw = self.retire_w.get(p.i, self.RETIRE_RANK_W)
            gw = self.gain_w.get(p.i, self.RETIRE_GAIN_W)
            ph = self.phase_of(p)
            if ph is not None:
                gw *= self.PHASE_ROW_EARLY + (1 - self.PHASE_ROW_EARLY) * ph
                rw *= self.PHASE_ROW_EARLY + (1 - self.PHASE_ROW_EARLY) * ph
            v = (gw * self._vrow_gain(p, c) + rw * c[0] + hand_power(rest))
            if v > bv:
                best, bv = c, v
        return best

    def _maybe_upgrade(self, p):
        """Research — ONCE per turn (§10).

        Draw the top of the upgrade deck onto a grid position of your choice,
        retire a card FROM YOUR HAND to the victory row, pay 1 gold, and take
        any visible card at or below your tier's RANK CAP. Refill emptied
        positions.

        A player who has just emptied their hand cannot research this turn:
        there is nothing left to retire.
        """
        if len(p.vrow) >= 5:
            return
        if p.gold < 1:
            self.stats["upgrade_no_gold"] += 1     # wanted to research, broke
            return
        pool = p.hand + p.discard          # your whole deck, for judging a buy
        source = p.hand if self.RETIRE_FROM_HAND_ONLY else pool
        if not source:
            self.stats["upgrade_no_card_to_retire"] += 1
            return
        if not self.smart and random.random() > 0.35:
            return

        # 0. would this be a blind fish? With the tight caps (11/13/15/17/20) a
        # low tier facing a grid of tall cards can only buy if the card it draws
        # happens to fall under the cap. A real player looks first: if nothing
        # visible is buyable and the deck is unlikely to oblige, they keep the
        # action. Without this the bot burns the upgrade deck on draws it can
        # never buy, which is a bot artifact, not a property of the rule.
        if self.smart and self.SKIP_BLIND_RESEARCH:
            cap0 = p.rank_cap()
            visible = any(self.grid_top(k) is not None
                          and self.grid_top(k)[0] <= cap0
                          for k in range(len(self.grid)))
            if not visible:
                odds = (sum(c[0] <= cap0 for c in self.deck) / len(self.deck)
                        if self.deck else 0.0)
                if odds < self.BLIND_RESEARCH_ODDS:
                    self.stats["research_declined_blind"] += 1
                    return

        # 1. draw onto the grid (player's choice of position)
        if self.deck:
            card = self.deck.pop()
            k = self._pick_grid_slot(p, card)
            self.grid[k].append(card)
            self.stats["grid_draws"] += 1

        # 2. what may this tier buy?
        cap = p.rank_cap()
        avail = [(k, self.grid_top(k)) for k in range(len(self.grid))
                 if self.grid_top(k) is not None and self.grid_top(k)[0] <= cap]
        if not avail:
            self.stats["upgrade_blocked_by_cap"] += 1
            return

        if self.smart and self.SMART_MARKET:
            k, buy = max(avail, key=lambda kv: self._buy_value(p, kv[1], pool))
        else:
            k, buy = random.choice(avail)

        # 3. retire, pay, take
        if self.RETIRE_FROM_HAND_ONLY:
            retire = self._pick_retire(p)
            if retire is None:            # nothing legal to retire this turn
                return
            p.hand.remove(retire)
            self.stats["retire_rank"] += retire[0]
        else:                              # pre-v0.22: hand OR the table
            retire = (max(pool, key=lambda c: c[0]) if self.smart
                      else min(pool, key=lambda c: c[0]))
            (p.hand if retire in p.hand else p.discard).remove(retire)
        p.vrow.append(retire)
        p.gold -= 1
        self.coins(p, "map", "spend: upgrade", 1)
        self.stats["gold_out_upgrade"] += 1
        self.stats["upgrades"] += 1
        self.grid[k].pop()
        # v0.22: the card you buy goes STRAIGHT INTO YOUR HAND. It used to land
        # in the personal discard, which put it two rounds away from being
        # playable — and by the time it arrived it was the tallest card in hand
        # and got retired instead. Only ~21% of purchases ever reached the map.
        # Retire-then-buy is one card out, one card in, so the ten-card ceiling
        # is untouched either way.
        (p.hand if self.BUY_INTO_HAND else p.discard).append(buy)

        # 4. refill any empty position
        for j in range(len(self.grid)):
            if not self.grid[j] and self.deck:
                self.grid[j].append(self.deck.pop())

    def _pick_grid_slot(self, p, card):
        """Where to place the drawn card. Burying a card a RIVAL could buy but
        you cannot is the sharp play; the simple version buries the position
        whose top card is worth least to us."""
        if not self.smart:
            return random.randrange(len(self.grid))
        empty = [k for k in range(len(self.grid)) if not self.grid[k]]
        if empty:
            return empty[0]
        pool = p.hand + p.discard
        return min(range(len(self.grid)),
                   key=lambda k: self._buy_value(p, self.grid_top(k), pool))

    def _buy_value(self, p, card, pool):
        """Worth of a market card: completing or extending a run is what wins
        tricks; rank itself only breaks ties and scores in the victory row."""
        if card is None:
            return -1e9
        r = card[0]
        ranks = [c[0] for c in pool]
        v = 3.0 * ranks.count(r) + 1.5 * (ranks.count(r - 1) + ranks.count(r + 1))
        v += 0.08 * r
        return v

    PROPORTIONAL_STARVATION = True    # one unit back per gold you are short
    USE_EFFECT_D = False              # v0.23 candidate: conquest (see _maybe_use_d)
    USE_EFFECT_C = True               # cash victory cards for gold when short
    USE_EFFECT_C_PROACTIVE = True     # ...and when the slot costs nothing to lose
    C_GOLD_PER_POINT = 2              # coins a victory point must fetch to be sold
    ROW_HORIZON = 2                   # victory cards you still expect to retire
    ROW_PAD_RANK = 12                 # typical rank of those future cards
    PHASE_PLAY = False                # map first, rank when the end nears
    ENDGAME_AT = 6                    # reserve left, table-wide, that starts the endgame
    PHASE_CASH_EARLY = 0.35           # how readily you cash a card early (1 = as now)
    PHASE_ROW_EARLY = 0.30            # how much the row is worth early (1 = as now)
    C_FIRST = False                   # ask the ROW for coins before the hand
    USE_EFFECT_A = True               # spend a card to win a trick
    TIE_RULE = "rank"                 # rank | earliest | topband
    A_TIMING = "blind"                # rulebook v0.20: A is declared before any meld
    USE_EFFECT_B = True               # spend a card for extra settles
    USE_FORTIFY = True                # spend surplus gold protecting units
    USE_MOVES = True                  # the band's free moves, land and sea (§07)
    USE_RECLAIM = True                # pull fortification coins back to feed (§07)
    CASH_FOR_FOOD = True              # spend a card as gold on purpose (§06)
    CASH_THRESHOLD = 1.0              # map value below which a card is worth more as a coin
    SKIP_BLIND_RESEARCH = True        # don't research when nothing is buyable
    BLIND_RESEARCH_ODDS = 0.35        # ...unless the deck is this likely to help
    RETIRE_FROM_HAND_ONLY = True      # v0.22: cards on the table are spent (§10)
    BUY_INTO_HAND = True              # purchases land in hand, not the discard
    RETIRE_LOWEST_N = 0               # retire only from your N weakest cards (0=off)
    RETIRE_ASCENDING = False          # each retirement must outrank the last
    RETIRE_UNDER_CAP = False          # retire only at or below your rank cap
    MELD_GREED = 0.30                 # how much the hand you keep is worth
    RETIRE_GAIN_W = 3.0               # weight on the row's immediate point gain
    RETIRE_RANK_W = 1.2               # weight on raw rank: the row is permanent
    USE_HOLD_BACK = True              # take gold rather than climb into a band you cannot feed
    LIMIT_LADDER = None               # None = fixed HOLDS; or a key of LADDERS
    STARVE_CULLS_STACKS = True        # famine sheds stacks over the new limit
    WINNER_BONUS_CARD = True          # BASE RULE: reward the winner, dock nobody
    MATCH_DISCARD = True              # v0.22: match the winner's count and lose -> discard 1
    USE_ASCENSION = True              # v0.22: 1/2/3/4 coins, once per tier
    USE_WATER_ADVANTAGE = True        # v0.22: first sea move grants a free wild explore
    CONNECTED_MAJORITY = True         # v0.22: majority needs one connected group
    MARKET_GRID = 9                   # v0.22: 3x3 face-up grid
    FULL_ADV_DECK = True              # ranks 11-20 at EVERY player count
    IMMEDIATE_REFILL = True           # refill to ten the moment the hand empties
    MAJORITY_RULE = "area"            # area | units (units = the old rule)
    MAJORITY_TIES = "units"           # all | none | units (level-breaker)
    MAJORITY_MIN_AREA = 1             # a patch must be this many tiles to count
    MOVE_POLICY = "threat"            # threat | patch | strike
    MOVE_TIMING = "after"             # after | before the meld is spent
    OCEAN_PASS_OWN = False            # sail through ocean tiles you own
    MOVE_CAP = None                   # None = use the tier allowance (§07)
    GIVE_BONUS_CARD = True            # within that: does the winner get the extra card?
    LOSER_CONSOLATION = "last"        # none | all | last  (base rule: last)
    CONSOLATION_GOLD = 1              # coins paid to the trick loser
    SMART_MARKET = False              # buy to complete melds, not at random
    PRO_DRAFT = True                  # pro seats: draft for meldability
    PRO_CASH = True                   # pro seats: situational cash threshold
    PRO_MOVES = True                  # pro seats: reinforce/evacuate only

    def coins(self, p, phase, kind, n):
        """Record one reach-for-the-bank moment."""
        if n:
            self.ledger.append((self.round, p.i, phase, kind, n))

    def _eff_size(self, q):
        return meld_size(q.kind, q.played) + q.bonus

    def _leader(self, table, exclude=None):
        best = None
        for seat, i in table:
            q = self.P[i]
            if q is exclude or not q.played:
                continue
            k = (self._eff_size(q), int(q.ties), q.spent_a,
                 max(c[0] for c in meld_cards(q.kind, q.played)), -seat)
            if best is None or k > best:
                best = k
        return best

    def _declare_a_blind(self, p):
        """Commit before seeing anyone else's meld. All you know is your own."""
        if len(p.vrow) < 3:
            return
        size = meld_size(p.kind, p.played)
        if size >= p.meld_limit():      # already your best; likely to hold up
            return
        if size > 2:                    # only rescue genuinely weak melds
            return
        for card in sorted(p.vrow, key=lambda c: c[0]):
            add, ties = effect_a(card[0])
            p.vrow.remove(card)
            self.removed.append(card)
            p.bonus += add
            p.ties = p.ties or ties
            p.spent_a = max(p.spent_a, card[0])
            p.a_band = band_of(card[0])
            self.stats["effect_a_used"] += 1
            self.stats["effect_a_rank"] += card[0]
            self.stats[f"a_band_{p.a_band}"] += 1
            return

    def _maybe_declare_a(self, p, table):
        if self.A_TIMING == "blind":
            return self._declare_a_blind(p)
        """Spend a card to take a trick you are currently losing.

        Declared in the open as the meld is played, so it is judged only
        against what is already on the table - later players can still answer.
        """
        if len(p.vrow) < 3:                 # do not gut a thin row
            return
        rival = self._leader(table, exclude=p)
        if rival is None:
            return
        mine = (self._eff_size(p), 0, 0,
                max(c[0] for c in meld_cards(p.kind, p.played)), 0)
        if mine > rival:
            return                          # already winning; save the card
        for card in sorted(p.vrow, key=lambda c: c[0]):
            add, ties = effect_a(card[0])
            cand = (self._eff_size(p) + add, int(ties), card[0],
                    max(c[0] for c in meld_cards(p.kind, p.played)), 0)
            if cand > rival:
                p.vrow.remove(card)
                self.removed.append(card)
                p.bonus += add
                p.ties = p.ties or ties
                p.spent_a = max(p.spent_a, card[0])
                p.a_band = band_of(card[0])
                self.stats["effect_a_used"] += 1
                self.stats["effect_a_rank"] += card[0]
                self.stats[f"a_band_{p.a_band}"] += 1
                return

    def _maybe_use_b(self, p):
        """Effect B — found colonies (§10, v0.22).

        Lay new tiles, put units from your board on them, fortify them from the
        GENERAL SUPPLY. Touch-two still applies; REACH does not, so a colony may
        be founded anywhere along the map's edge. At most one card per turn.
        """
        if len(p.vrow) < 4 or p.reserve_empty():
            return
        for card in sorted(p.vrow, key=lambda c: c[0]):
            tiles, units, same_suit, steps = effect_b_v22(card[0])
            spaces = self.m.legal_spaces()          # already touch-two legal
            if not spaces:
                continue
            want = card[1] if same_suit else None
            usable = [c for c in sorted(spaces)
                      if want is None or self.m.supply.get(want, 0) > 0]
            if not usable:
                continue

            p.vrow.remove(card)
            self.removed.append(card)
            self.stats["effect_b_used"] += 1

            placed_tiles, settled = 0, 0
            for cell in usable:
                if placed_tiles >= tiles:
                    break
                terr = want
                if terr is None:                     # ranks 16-20: any terrain
                    opts = [t for t in TER if self.m.supply.get(t, 0) > 0]
                    if not opts:
                        break
                    terr = max(opts, key=lambda t: self.m.supply[t])
                if not self.m.do_explore(cell, terr):
                    continue
                placed_tiles += 1
                self.stats["colony_tile"] += 1
                if settled < units and p.take_unit():
                    self.m.settle(cell, p.i)
                    self._pay_ascension(p)
                    settled += 1
                    self.stats["colony_unit"] += 1
                    # fortification paid by the GENERAL SUPPLY, not the player
                    if self.m.fortify(cell):
                        self.stats["colony_fortify"] += 1
                        self.stats["supply_gold_spent"] += 1
                # touch-two is judged per placement, so refresh the spaces
                spaces = self.m.legal_spaces()
            b = band_of(card[0])
            self.stats[f"b_band_{b}_used"] += 1
            self.stats[f"b_band_{b}_tiles"] += placed_tiles
            self.stats[f"b_band_{b}_units"] += settled
            return

    def _sea_move(self, p):
        """A legal Ocean-to-Ocean move, if one exists and there is a free
        explore actually worth claiming afterwards."""
        if not self.m.legal_spaces():
            return None
        for c, t in self.m.tiles.items():
            if t.terrain != "ocean" or t.owner != p.i or not t.units:
                continue
            for u in t.neighbours():
                if u.terrain == "ocean" and not u.units:
                    return (c, u.cell)
        return None

    def _water_explore(self, p):
        """The water advantage (§07): your FIRST sea move each turn grants one
        free explore of ANY terrain — not tied to a card's suit. Touch-two and
        reach still apply."""
        if not self.USE_WATER_ADVANTAGE:
            return
        spaces = self.m.legal_spaces()
        reachable = reach(self.m, p.i)
        opts = [c for c in sorted(spaces) if c in reachable]
        if not opts:
            return
        terr = max((t for t in TER if self.m.supply.get(t, 0) > 0),
                   key=lambda t: self.m.supply[t], default=None)
        if terr is None:
            return
        if self.m.do_explore(opts[0], terr):
            self.stats["water_explore"] += 1

    def _free_moves(self, p, cards=()):
        """The band's free moves (§07). No card, never an attack.

        By land: across tiles your own units occupy, stepping off onto a free
        adjacent tile with room. By sea: across unoccupied Ocean.

        The policy is deliberately narrow — move a unit that is standing where
        it is about to be taken, or off a tile that is over-stacked onto empty
        ground. A greedy mover would make the sim measure the bot, not the game.
        """
        budget = p.free_moves() if self.MOVE_CAP is None else self.MOVE_CAP
        used_water = False
        # v0.22: the first sea move each turn buys a free explore of any
        # terrain, which is worth more than most land moves. A bot that never
        # takes it would make the water advantage measure as dead.
        if (self.USE_WATER_ADVANTAGE and self.smart and budget > 0
                and p.i in self.pro):
            sea = self._sea_move(p)
            if sea is not None:
                src_cell, dest = sea
                t = self.m.tiles[src_cell]
                t.units.remove(p.i)
                t.gold = min(t.gold, len(t.units))
                self.m.settle(dest, p.i)
                self.stats["free_move"] += 1
                used_water = True
                self._water_explore(p)
                budget -= 1
        while budget > 0:
            if p.i in self.pro and self.PRO_MOVES:
                pol = self.move_policy.get(p.i, self.MOVE_POLICY)
                mv = None
                if pol == "strike":
                    mv = self._strike_move(p, cards)
                elif pol == "patch":
                    mv = self._patch_move(p)
                if mv is None:
                    mv = self._pro_move(p)
                if mv is None:
                    return
                src_cell, dest = mv
                t = self.m.tiles[src_cell]
                t.units.remove(p.i)
                t.gold = min(t.gold, len(t.units))
                self.m.settle(dest, p.i)
                self.stats["free_move"] += 1
                budget -= 1
                continue
            src_cell = self._move_source(p)
            if src_cell is None:
                return
            dest = self._move_dest(p, src_cell)
            if dest is None:
                return
            t = self.m.tiles[src_cell]
            t.units.remove(p.i)
            t.gold = min(t.gold, len(t.units))       # a moved unit loses its coin
            self.m.settle(dest, p.i)
            self.stats["free_move"] += 1
            budget -= 1

    def _strike_targets(self, p, cards):
        """Rival units this player could actually hit with the cards in hand,
        given where they stand right now."""
        suits = {c[1] for c in cards}
        n = 0
        for c, t in self.m.tiles.items():
            if t.owner in (None, p.i) or not t.units:
                continue
            if t.terrain not in suits or p.gold < ATTACK_COST[t.terrain]:
                continue
            if any(u.owner == p.i and u.units for u in t.neighbours()):
                n += len(t.units)
        return n

    def _strike_move(self, p, cards):
        """Move to bring a rival INTO RANGE of a card you are about to play.

        This only means anything if moves happen BEFORE the meld is spent: sail
        or march up to a neighbour for free, then let the card do the killing.
        With moves after the meld, the unit arrives when the shooting is over.
        """
        if not cards:
            return None
        before = self._strike_targets(p, cards)
        best, best_gain = None, 0
        for c, t in self.m.tiles.items():
            if t.owner != p.i or not t.units:
                continue
            for d in (self._move_dest(p, c, True) or ()):
                dt = self.m.tiles[d]
                if not dt.has_room(p.i):
                    continue
                t.units.remove(p.i)
                dt.units.append(p.i)
                gain = self._strike_targets(p, cards) - before
                dt.units.pop()
                t.units.append(p.i)
                if gain > best_gain:
                    best, best_gain = (c, d), gain
        return best

    def _patch_move(self, p):
        """Move to JOIN UP a terrain (§13 dominance = largest connected stretch).

        Since dominance became "your biggest connected group of a terrain", free
        moves are the natural tool for welding two patches into one — and no
        other action in the game can do it without spending a card. The bot did
        not know that: `_pro_move` only ever reinforces or evacuates.

        Scores every legal (source, destination) by the NET change in the sum of
        your largest stretches across all four terrains, so a move that grows
        one patch but splits another is correctly valued at zero.
        """
        def total(seat):
            return sum(self._largest_patch(seat, t) for t in TER)

        before = total(p.i)
        best, best_gain = None, 0
        for c, t in self.m.tiles.items():
            if t.owner != p.i or not t.units:
                continue
            for d in (self._move_dest(p, c, True) or ()):
                dt = self.m.tiles[d]
                if not dt.has_room(p.i):
                    continue
                # try it, measure it, put it back. `owner` is derived from
                # units, so moving the unit is the whole mutation.
                t.units.remove(p.i)
                dt.units.append(p.i)
                gain = total(p.i) - before
                dt.units.pop()
                t.units.append(p.i)
                if gain > best_gain:
                    best, best_gain = (c, d), gain
        return best

    def _pro_move(self, p):
        """Move for a reason: reinforce a tile a rival can take, or evacuate one
        that is already lost. Never spread thin — spreading is what made the
        naive policy measure worse than not moving at all."""
        best = None
        for c, t in self.m.tiles.items():
            if t.owner != p.i or len(t.units) < 2:
                continue                              # need a spare unit
            for u in t.neighbours():
                if u.owner != p.i or not u.units:
                    continue
                threat = sum(1 for w in u.neighbours()
                             if w.owner not in (None, p.i) and w.units)
                if not threat:
                    continue
                if len(u.units) < u.capacity_for(p.i):
                    score = 2.0 * threat - len(u.units)
                    if best is None or score > best[0]:
                        best = (score, c, u.cell)
        return (best[1], best[2]) if best else None

    def _move_source(self, p):
        """A unit worth moving: threatened, or crowding a tile that holds more
        than it needs to."""
        best = None
        for c, t in self.m.tiles.items():
            if t.owner != p.i or not t.units:
                continue
            threatened = any(u.owner not in (None, p.i) and u.units
                             for u in t.neighbours())
            score = 0.0
            if threatened and t.gold == 0:
                score += 2.0
            if len(t.units) > 1:
                score += 1.0                          # a spare unit, tile stays yours
            else:
                score -= 1.5                          # moving surrenders the tile
            if score <= 0:
                continue
            if best is None or score > best[0]:
                best = (score, c)
        return best[1] if best else None

    def _move_dest(self, p, src_cell, all_of_them=False):
        """Where that unit can legally go. Land moves travel across your own
        occupied tiles and step off at the end; sea moves cross open Ocean."""
        t = self.m.tiles[src_cell]
        # walk the network of tiles you occupy
        seen, frontier = {src_cell}, [src_cell]
        while frontier:
            c = frontier.pop()
            for u in self.m.tiles[c].neighbours():
                if u.cell in seen:
                    continue
                if u.owner == p.i and u.units:
                    seen.add(u.cell)
                    frontier.append(u.cell)
        land = set()
        for c in seen:
            for u in self.m.tiles[c].neighbours():
                if u.owner in (None, p.i) and u.has_room(p.i) and u.cell != src_cell:
                    land.add(u.cell)
        # sea: from Ocean, across unoccupied Ocean
        sea = set()
        if t.terrain == "ocean":
            seen2, fr = {src_cell}, [src_cell]
            while fr:
                c = fr.pop()
                for u in self.m.tiles[c].neighbours():
                    if u.cell in seen2 or u.terrain != "ocean":
                        continue
                    # OCEAN_PASS_OWN: your own ships are not a wall. Ocean holds
                    # one unit, so occupying the sea currently blocks the very
                    # lane you built — the largest navigable stretch in a
                    # finished game is about ONE tile. Passing through your own
                    # ocean makes an owned chain the road §07 describes.
                    passable = (not u.units) or (self.OCEAN_PASS_OWN
                                                 and u.owner == p.i)
                    if not passable:
                        continue
                    seen2.add(u.cell)
                    fr.append(u.cell)
                    if not u.units:            # you may only END on open water
                        sea.add(u.cell)
        pool = land | sea
        if not pool:
            return None
        if all_of_them:                    # the search policies want every option
            return pool
        # prefer empty ground you do not already hold — moving is for reach
        def rank(c):
            u = self.m.tiles[c]
            return (0 if not u.units else 1, -u.capacity_for(p.i))
        return sorted(pool, key=rank)[0]

    def _reclaim_for_food(self, p):
        """Gold reallocation (§07): a fortification coin is not sunk — pull it
        back off the map rather than starve. This is the real economic change
        in v0.21, and it is why fortifying is cheaper than it looks."""
        need = p.food()
        for c, t in self.m.tiles.items():
            if p.gold >= need:
                return
            if t.owner == p.i and t.gold:
                take = min(t.gold, need - p.gold)
                t.gold -= take
                p.gold += take
                self.stats["gold_reclaimed"] += take
                self.coins(p, "map", "gain: reclaimed fortification", take)

    def _would_climb(self, p):
        """Would taking a unit from the reserve empty the current band?"""
        j = p.band()
        return p.reserve[j] == 1 and j + 1 < len(BANDS)

    def _next_food(self, p):
        j = p.band()
        return BANDS[min(j + 1, len(BANDS) - 1)][3]

    def _vp_of(self, row):
        r = sorted(c[0] for c in row)
        return vrow_score(r)

    def _endgame(self, seat=None):
        """How close is the TABLE to someone placing their last unit? 0 early,
        1 on the brink.

        The end trigger is the twentieth unit in ~100% of games, so the leader's
        remaining reserve is the game's real clock. A player who reads it can
        spend the early game on the map — where half the score lives and where
        every unit placed also climbs their tier — and switch to banking rank
        only when the row is about to be counted.
        """
        left = min(sum(q.reserve) for q in self.P)
        span = max(1, self.ENDGAME_AT)
        return max(0.0, min(1.0, (span - left) / span))

    def phase_of(self, p):
        """Per-seat phase weight; 0 for seats not playing the phase strategy."""
        if not self.phase_play.get(p.i, self.PHASE_PLAY):
            return None
        return self._endgame()

    def _row_cost(self, p, card, horizon=None):
        """What spending this victory card REALLY costs.

        The row only scores at the very end, so pricing it at today's score is
        wrong — and it is wrong by a lot. A three-card row scores its centre
        slot, so selling from it looks like a ten-point disaster; but the player
        will retire more cards before the game ends, and against the row they
        will ACTUALLY have, the same sale costs about one point.

        Pad the row with the cards still to come and price the sale against
        that. Once the end has triggered there is no more time, and the naive
        price becomes the true one.
        """
        if horizon is None:
            horizon = 0 if self.ended_on else self.ROW_HORIZON
        row = [c[0] for c in p.vrow]
        rest = list(row)
        rest.remove(card[0])
        pad = [self.ROW_PAD_RANK] * horizon
        return vrow_score(row + pad) - vrow_score(rest + pad)

    def _maybe_cash_c(self, p, ahead=False):
        """Spend a victory card for gold when it costs NOTHING to score (§12).

        The row scores its third-highest rank, so with five cards the two
        lowest are free ammunition — drop them and the score does not move.
        The old bot only ever reached for C while starving, which is why C
        looked dead: 0.0-0.7 uses a game against 5-9 for A. This asks the
        question a player would: is this card actually paying for its slot?
        """
        if not self.USE_EFFECT_C_PROACTIVE or not p.vrow:
            return
        # Since the row began scoring 1 per card, NO slot is free any more, so
        # the old "cash it if it costs nothing" test could never fire and C
        # measured dead by construction. A player does not need the slot to be
        # free — they need the coins to be worth more than the point. Cash when
        # broke enough that the research engine or the food bill has stalled.
        while p.vrow:
            low = min(p.vrow, key=lambda c: c[0])
            rest = [c for c in p.vrow if c is not low]
            cost = self._row_cost(p, low)
            gain = effect_c(low[0])
            # Looking AHEAD, the bill to beat is this turn's food plus a coin
            # for research — the shortfall the hand would otherwise cash for.
            need = (p.food() + 1) if ahead else max(1, p.food())
            broke = p.gold < need
            if not broke or gain < cost * self.C_GOLD_PER_POINT:
                return
            p.vrow.remove(low)
            self.removed.append(low)
            p.gold += effect_c(low[0])
            self.coins(p, "map", "gain: effect C", effect_c(low[0]))
            self.stats["effect_c_used"] += 1
            self.stats["effect_c_free"] += 1
            self.stats["gold_in_effect_c"] += effect_c(low[0])

    def _maybe_use_d(self, p):
        """Effect D — CONQUEST. The military option the row does not have.

        Every existing use of a victory card builds your own side: A wins the
        trick, B founds colonies, C pays coins. Attacking, meanwhile, is pure
        denial — it removes a rival unit worth 1 point and puts nothing of yours
        on the ground, which is measurably why aggression never pays.

        D fixes exactly that: take the ground. Remove rival units from tiles
        touching your civilization and SETTLE the tiles you empty, so a strike
        is a two-point swing plus territory plus a step up your tier ladder.

        By rank band: remove 1 / 1 / 2 / 2 units; the top three bands may also
        settle what they empty. Fortifications still absorb a hit.
        """
        # Guard MUST match B's, or this is not a comparison. B only fires with
        # four cards banked; an unguarded D simply drains the row first and
        # measures as 100% of all spending regardless of its merits.
        if not self.USE_EFFECT_D or len(p.vrow) < 4:
            return
        band = None
        for card in sorted(p.vrow, key=lambda c: c[0]):
            kills, may_settle = effect_d(card[0])
            targets = []
            for c, t in self.m.tiles.items():
                if t.owner in (None, p.i) or not t.units:
                    continue
                if any(u.owner == p.i and u.units for u in t.neighbours()):
                    # prefer a thin tile we can actually take over
                    targets.append((len(t.units), t.gold, c))
            if not targets:
                continue
            targets.sort()
            p.vrow.remove(card)
            self.removed.append(card)
            self.stats["effect_d_used"] += 1
            band = band_of(card[0])
            done = 0
            for _, _, c in targets:
                if done >= kills:
                    break
                t = self.m.tiles[c]
                while t.units and done < kills:
                    victim = self.m.remove_unit(c)
                    done += 1
                    if victim is None:
                        self.stats["absorbed_by_fortification"] += 1
                        break
                    self.P[victim].return_unit()
                    self.stats["killed_by_attack"] += 1
                    self.stats["conquest_kill"] += 1
                if (may_settle and not t.units and p.take_unit()):
                    self.m.settle(c, p.i)
                    self._pay_ascension(p)
                    self.stats["conquest_settle"] += 1
            if band is not None:
                self.stats[f"d_band_{band}_used"] += 1
            return

    def _spend_c(self, p, need):
        """Cash victory cards for gold rather than starve. Spends the lowest
        rank first: least valuable to keep, and the row still scores."""
        while p.gold < need and p.vrow:
            card = min(p.vrow, key=lambda c: c[0])
            p.vrow.remove(card)
            self.removed.append(card)
            p.gold += effect_c(card[0])
            self.coins(p, "food", "gain: effect C", effect_c(card[0]))
            self.stats["effect_c_used"] += 1
            self.stats["gold_in_effect_c"] += effect_c(card[0])

    FORTIFY_POLICY = "targeted"       # off | eager | targeted | majority

    def _fortify_candidates(self, p):
        """Tiles worth protecting, best first, with the reason scored.

        A coin is only worth spending where losing the unit actually costs
        something: a tile with ONE unit is surrendered outright when it falls,
        while a stack merely gets shorter. And it is only at risk if a rival
        stands next to it AND can afford that terrain's attack price.
        """
        out = []
        for c, t in self.m.tiles.items():
            if t.owner != p.i or t.gold >= len(t.units):
                continue
            threats = [u for u in t.neighbours()
                       if u.owner is not None and u.owner != p.i]
            if not threats:
                continue
            cost = ATTACK_COST[t.terrain]
            if not any(self.P[u.owner].gold >= cost for u in threats):
                continue                      # nobody next door can pay
            v = len(threats) * 1.0
            if len(t.units) == 1:
                v += 2.0                      # losing this loses the tile
            v -= cost                         # dear ground defends itself
            if self.FORTIFY_POLICY == "majority":
                mine = sum(1 for x in self.m.tiles.values()
                           if x.terrain == t.terrain and x.owner == p.i)
                best = max([sum(1 for x in self.m.tiles.values()
                                if x.terrain == t.terrain and x.owner == q.i)
                            for q in self.P if q.i != p.i] or [0])
                if mine - 1 < best <= mine:   # this unit is holding the majority
                    v += 3.0
            if v > 0:
                out.append((v, c))
        out.sort(reverse=True)
        return out

    def _maybe_fortify(self, p):
        pol = getattr(self, "fort_by_seat", {}).get(p.i, self.FORTIFY_POLICY)
        if pol == "off":
            return
        if pol == "eager":
            if p.gold < 3:
                return
            for c, t in self.m.tiles.items():
                if t.owner == p.i and t.gold < len(t.units) and any(
                        u.owner not in (None, p.i) for u in t.neighbours()):
                    if self.m.fortify(c):
                        p.gold -= 1
                        self.stats["gold_out_fortify"] += 1
                        self.stats["fortified"] += 1
                    return
            return
        # targeted / majority: only out of genuine surplus, and only where it pays
        if p.gold < p.food() + 3:
            return
        cand = self._fortify_candidates(p)
        if not cand:
            return
        v, c = cand[0]
        if self.m.fortify(c):
            p.gold -= 1
            self.coins(p, "map", "spend: fortify", 1)
            self.stats["gold_out_fortify"] += 1
            self.stats["fortified"] += 1

    def _recycle(self, p):
        owed = p.food()
        if self.smart and self.USE_EFFECT_C:
            self._spend_c(p, owed)
        if self.PROPORTIONAL_STARVATION:
            short = max(0, owed - p.gold)
            for _ in range(short):
                cells = [c for c, t in self.m.tiles.items() if t.owner == p.i]
                if not cells:
                    break
                c = random.choice(cells)
                self.m.take_unit_off(c)
                self.stats["starved_back"] += 1
                p.return_unit()
            owed = min(owed, p.gold)          # the debt is settled either way
        else:
            while owed > p.gold:              # return until the BAND drops
                cells = [c for c, t in self.m.tiles.items() if t.owner == p.i]
                if not cells:
                    break
                c = random.choice(cells)
                self.m.take_unit_off(c)
                self.stats["starved_back"] += 1
                p.return_unit()
                owed = p.food()
        self.coins(p, "food", "spend: food", min(owed, p.gold))
        self.stats["gold_out_food"] += min(owed, p.gold)
        p.gold = max(0, p.gold - owed)
        self.stats["recycles"] += 1
        self.stats["food_paid"] += owed
        if self.STARVE_CULLS_STACKS:
            self._cull_overstacks(p)
        # v0.22: take back everything you played, then draw from the SHARED
        # pile up to ten. The ten-card invariant is gone — your deck churns.
        p.hand, p.discard = p.discard, []
        random.shuffle(self.pile)
        while len(p.hand) < 10 and self.pile:
            p.hand.append(self.pile.pop())
            self.stats["drawn_from_pile"] += 1

    def _cull_overstacks(self, p):
        """Famine hits the cities first (per-tier limits only).

        Losing a band lowers what your tiles may hold, so any stack now above
        that limit sheds units back to the reserve. Those units refill the
        reserve, which can drop the band AGAIN — so this loops until stable,
        and the loop is the point: this is the mechanism that can turn one
        missed meal into a collapse. Depth is recorded so the spiral can be
        measured rather than assumed."""
        if self.m.limits is None:
            return
        depth = 0
        while True:
            over = []
            for c, t in self.m.tiles.items():
                if t.owner == p.i:
                    excess = len(t.units) - t.capacity_for(p.i)
                    if excess > 0:
                        over.append((c, excess))
            if not over:
                break
            depth += 1
            if depth > 20:                      # cannot happen; guards a typo
                raise AssertionError("cull did not converge")
            for c, excess in over:
                for _ in range(excess):
                    if self.m.take_unit_off(c) is not None:
                        self.stats["culled_by_famine"] += 1
                        p.return_unit()
        if depth > 1:
            self.stats["cull_cascaded"] += 1
        self.stats["cull_depth_max"] = max(self.stats["cull_depth_max"], depth)

    def _largest_patch(self, seat, terrain):
        """Size, in TILES, of this seat's biggest connected group of `terrain`.

        v0.22 majority rule: adjacency is walked over tiles of that terrain that
        the seat occupies — the same measure as `_one_patch` — but instead of
        disqualifying a split empire it simply takes the largest piece. Whoever
        holds the biggest single stretch of a terrain dominates it.
        """
        mine = {c for c, t in self.m.tiles.items()
                if t.terrain == terrain and t.owner == seat and t.units}
        best, unseen = 0, set(mine)
        while unseen:
            comp, stack = set(), [unseen.pop()]
            while stack:
                c = stack.pop()
                comp.add(c)
                for u in nbrs(*c):
                    if u in unseen:
                        unseen.discard(u)
                        stack.append(u)
            best = max(best, len(comp))
        return best

    def _one_patch(self, seat, terrain):
        """Do all this seat's units on `terrain` sit in a single connected
        group? Connectivity is measured over tiles of that terrain that the
        seat occupies."""
        mine = {c for c, t in self.m.tiles.items()
                if t.terrain == terrain and t.owner == seat and t.units}
        if len(mine) <= 1:
            return True
        seen, stack = {next(iter(mine))}, [next(iter(mine))]
        while stack:
            c = stack.pop()
            for u in nbrs(*c):
                if u in mine and u not in seen:
                    seen.add(u)
                    stack.append(u)
        return seen == mine

    def _check_end(self):
        if self.ended_on:
            return
        if any(p.reserve_empty() for p in self.P):
            self.ended_on = ("last unit placed", self.round)
        elif not self.deck and all(len(st) <= 1 for st in self.grid):
            # v0.22: the market THINNING to a single layer ends the game, not
            # the deck emptying. While the deck lasts, every upgrade adds a card
            # to a stack, so the grid deepens; once it is dry the grid can only
            # be eaten down. One layer left = the last of the ideas.
            self.ended_on = ("market down to a single layer", self.round)
        if self.ended_on:
            self.final_rounds = self.round + 1     # finish this round, then one more

    def finished(self):
        return self.final_rounds is not None and self.round > self.final_rounds

    def score(self):
        out = []
        for p in self.P:
            pop = sum(t.units.count(p.i) for t in self.m.tiles.values())
            row = sorted(c[0] for c in p.vrow)
            vp = vrow_score(row)
            dom = 0
            for t in TER:
                if self.MAJORITY_RULE == "area":
                    # v0.22: dominance is the BIGGEST CONNECTED STRETCH of a
                    # terrain you occupy, counted in tiles. Not most units —
                    # a tall stack on one tile dominates nothing.
                    sizes = {q.i: self._largest_patch(q.i, t) for q in self.P}
                    mine, top = sizes[p.i], max(sizes.values())
                    if mine < self.MAJORITY_MIN_AREA or mine < top:
                        continue
                    level = [q for q in sizes if sizes[q] == top]
                    if len(level) > 1:
                        # A one-tile patch each is the common case, and letting
                        # everyone score it is what made ties EXPLODE. How the
                        # level is broken is the whole design question here.
                        if self.MAJORITY_TIES == "none":
                            continue
                        if self.MAJORITY_TIES == "units":
                            u = {q: sum(tile.units.count(q)
                                        for tile in self.m.tiles.values()
                                        if tile.terrain == t) for q in level}
                            if u[p.i] < max(u.values()):
                                continue
                            if list(u.values()).count(u[p.i]) > 1:
                                self.stats["majority_tied"] += 1
                        else:
                            self.stats["majority_tied"] += 1
                    dom += 3
                    continue
                cnt = Counter()
                for tile in self.m.tiles.values():
                    if tile.terrain == t:
                        for u in tile.units:
                            cnt[u] += 1
                if not (cnt and cnt[p.i] == max(cnt.values()) and cnt[p.i] > 0):
                    continue
                if self.CONNECTED_MAJORITY and not self._one_patch(p.i, t):
                    self.stats["majority_lost_to_split"] += 1
                    continue
                dom += 3
            out.append(dict(seat=p.i, pop=pop, vrow=vp, dom=dom,
                            total=pop + vp + dom, gold=p.gold,
                            band=BANDS[p.band()][0]))
        return out


# --------------------------------------------------------------- policies
def band_of(rank):
    return 0 if rank <= 5 else 1 if rank <= 10 else 2 if rank <= 15 else 3


def effect_a(rank):
    """(cards added to the trick count, does it win ties)."""
    b = band_of(rank)
    return (1 if b < 2 else 2, b in (1, 3))


def effect_b_v22(rank):
    """v0.22 colonies: (tiles, units, same_suit_only, max_steps_out)."""
    b = band_of(rank)
    return [(1, 1, True, 1), (1, 1, True, 2), (2, 1, True, 1), (2, 2, False, 1)][b]


def effect_b(rank):
    """(extra cells, must they match the spent card's own suit)."""
    b = band_of(rank)
    return (1 if b < 2 else 2, b in (0, 2))


VROW_RULE = "centre"      # centre | highest | count  (see vrow_score)


def vrow_score(ranks):
    """Victory-row points (§13).

    "centre" (current): 1 per card, plus the rank in the centre slot once the
    row holds three — i.e. your THIRD-HIGHEST. Every rank-based row rewards
    retiring your best card, which is why the market gets laundered into the
    row instead of feeding melds.

    "highest": 1 per card, plus your single best rank. Retiring a low card is
    then pure profit — it cannot lower the maximum — so the row fills bottom-up.

    "count": 1 per card and nothing else. Rank stops mattering entirely; you
    retire whatever your hand misses least.
    """
    r = sorted(ranks)
    if VROW_RULE == "count":
        return len(r)
    if VROW_RULE == "highest":
        return len(r) + (r[-1] if r else 0)
    if VROW_RULE == "run":
        # 1 per card, plus TWICE your longest unbroken run of ranks in the row.
        # A lineage, not a treasury: consecutive cards are what pays, and the
        # consecutive cards you hold most of are the low ones you started with.
        best = run = 1 if r else 0
        for a_, b_ in zip(r, r[1:]):
            run = run + 1 if b_ == a_ + 1 else 1
            best = max(best, run)
        return len(r) + 2 * best
    return len(r) + (r[len(r) - 3] if len(r) >= 3 else 0)


def effect_d(rank):
    """Victory-card effect D: conquest. (units removed, may settle after)"""
    if rank <= 5:
        return 1, False
    if rank <= 10:
        return 1, True
    if rank <= 15:
        return 2, True
    return 2, True


def effect_c(rank):
    """Victory-card effect C: gold on demand, by rank band (§09)."""
    return 2 if rank <= 5 else 3 if rank <= 10 else 4 if rank <= 15 else 5


def value_card(game, p, cell, card, act):
    """Score ONE card spent on one cell. Higher is better; the scale matters,
    because a card scoring below Game.CASH_THRESHOLD is cashed for a coin
    instead — in v0.21 that comparison is the central decision of every turn.

    Deliberately simple and readable, because a policy nobody can reason about
    produces findings nobody should trust. Every term is a claim about what is
    worth doing, and each can be argued with.
    """
    m = game.m
    if act == "settle":
        v = 3.0                                        # a unit scores and holds ground
        t = m.tiles[cell]
        mine = sum(1 for x in m.tiles.values()
                   if x.terrain == t.terrain and x.owner == p.i)
        best = max([sum(1 for x in m.tiles.values()
                        if x.terrain == t.terrain and x.owner == q.i)
                    for q in game.P if q.i != p.i] or [0])
        if mine <= best:                               # contesting a majority
            v += 1.2
        if t.terrain in ("forest", "mountain"):        # dear to take back off you
            v += 0.6
        return v
    if act == "explore":
        v = 1.0                                        # ground you will need later
        if any(c[1] == card[1] for c in p.hand):       # more of this suit to come
            v += 0.3
        return v
    if act == "attack":
        t = m.tiles[cell]
        v = 1.4 - 0.9 * ATTACK_COST[t.terrain]         # costs gold, places nothing
        if len(t.units) == 1:                          # clearing the tile outright
            v += 1.0
        return v
    return 0.2


def value_placement(*a, **k):
    """Removed in v0.21 along with pattern placement — see value_card()."""
    raise NotImplementedError("v0.20 API; v0.21 scores one card at a time "
                              "— use value_card()")


def smart_bot(game, p, what, options):
    """Choose the meld worth the most: trick weight, plus what its cards can
    actually do. Since cards are spent independently now, a meld is worth
    roughly the sum of its parts — which is exactly why cashing matters.
    """
    m = game.m
    spaces = m.legal_spaces()
    reachable = (reach(m, p.i) if m.civ(p.i)
                 else set(m.tiles) | spaces)
    cache = {}

    def card_value(card):
        if card not in cache:
            opts = card_options(m, card, p.i, p.gold, reachable, spaces)
            cache[card] = max(
                [value_card(game, p, c, card, a) for c, a in opts]
                + [game.CASH_THRESHOLD])          # a card is never worth less than a coin
        return cache[card]

    best, best_v = None, -1e9
    for opt in options:
        kind, payload = opt
        cards = meld_cards(kind, payload)
        v = 0.35 * len(cards)                     # tempo: bigger melds win tricks
        v += sum(card_value(c) for c in cards)
        if v > best_v:
            best, best_v = opt, v
    return best


def pro_bot(game, p, what, options):
    """A stronger meld chooser.

    Three things smart_bot ignores:

    1. THE TRICK IS WORTH A KNOWN AMOUNT. Winning means using every card (or,
       under the bonus rule, one extra); losing means one fewer or a coin. So the
       value of winning is roughly one card's map value — not a flat 0.35/card.
    2. WHETHER YOU CAN WIN IS KNOWABLE. Most cards wins, and every opponent's
       meld limit is public on their board. Playing four when the table can only
       answer with three is a near-certain trick; playing four when someone else
       can also play five is often waste.
    3. CARDS LEFT BEHIND STILL MATTER. Dumping your only pair to play one extra
       card today costs you a bigger meld tomorrow. Value the hand you keep.
    """
    m = game.m
    spaces = m.legal_spaces()
    reachable = (reach(m, p.i) if m.civ(p.i) else set(m.tiles) | spaces)
    cache = {}

    def card_value(card):
        if card not in cache:
            opts = card_options(m, card, p.i, p.gold, reachable, spaces)
            cache[card] = max(
                [value_card(game, p, c, card, a) for c, a in opts]
                + [game.CASH_THRESHOLD])
        return cache[card]

    # what the rest of the table could answer with, from their boards
    rivals = [q.meld_limit() for q in game.P if q.i != p.i]
    top_rival = max(rivals) if rivals else 0

    best, best_v = None, -1e9
    for opt in options:
        kind, payload = opt
        cards = list(meld_cards(kind, payload))
        n = len(cards)
        v = sum(card_value(c) for c in cards)

        # (2) how likely is this to take the trick?
        if n > top_rival:
            win = 0.9
        elif n == top_rival:
            win = 0.45
        else:
            win = 0.12 ** (top_rival - n + 1)
        # (1) the trick is worth about one card's worth of action, plus tempo
        v += win * (1.1 + 0.35 * statistics_mean([card_value(c) for c in cards]))

        # (3) what the remaining hand can still do
        rest = [c for c in p.hand if c not in cards]
        v += game.greed.get(p.i, game.MELD_GREED) * hand_power(rest)

        # feeding matters: if food is short, a fat meld that cashes is fine
        if p.gold < p.food():
            v += 0.25 * n

        if v > best_v:
            best, best_v = opt, v
    return best


def statistics_mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def random_bot(game, p, what, options):
    return random.choice(options)


SIMPLIFICATIONS = """
WHAT IS MODELLED, AND WHAT IS NOT  (v0.21 card-conversion port)

THE v0.21 CHANGE
  melds                 compete for the trick ONLY. No pattern, no shape, no
                        connectivity, no rank-order walk.
  each card             spent independently: settle / explore / attack / gold,
                        on any cell in reach, suit matching terrain
  card order            chosen by the bot, best-first, and the map is re-read
                        between cards -- so explore-then-settle in one turn is
                        modelled, which v0.20 forbade
  reach                 a tile you occupy, or a tile/space adjacent to one
  free moves            MODELLED (USE_MOVES): band number, land across your own
                        network or sea across open Ocean. Replaces shift+drift.
  food                  MODELLED: the band's coins, eaten at recycle
  gold reallocation     MODELLED (USE_RECLAIM) for fortification coins pulled
                        back to cover food. This makes fortifying materially
                        cheaper than in v0.20, where the coin was sunk.
  cashing on purpose    MODELLED (CASH_FOR_FOOD / CASH_THRESHOLD): a card whose
                        best map use scores below the threshold becomes a coin,
                        as does any card while food is uncovered

VICTORY-CARD EFFECTS - a card in the row may be spent on exactly ONE of three,
after which it leaves the game:
  A  card phase   meld counts as +1/+2 cards for the trick; bands 6-10 and
                  16-20 also win ties          -- MODELLED (USE_EFFECT_A)
  B  map phase    settle 1/2 extra units, own suit (1-5, 11-15) or any suit
                  (6-10, 16-20); ONE card per turn  -- MODELLED (USE_EFFECT_B)
  C  any time     2/3/4/5 gold by rank band    -- MODELLED (USE_EFFECT_C)

OTHER RULES
  fortifying          MODELLED (USE_FORTIFY), but the bot policy is too eager
  re-entry when wiped MODELLED
  attack terrain cost MODELLED
  draft, 3p balance   MODELLED
  losing-trick drop   chosen at random among legal drops
  free-move policy    narrow on purpose: move a threatened spare unit, or step
                      off an over-stacked tile. A greedy mover would make the
                      sim measure the bot rather than the game.

CAUTION: every finding in this folder dated before the v0.21 port was measured
on the pattern-placement engine. Numbers about meld shapes, placement rates and
the value of straights DO NOT CARRY OVER.
"""
