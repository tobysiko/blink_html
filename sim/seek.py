# -*- coding: utf-8 -*-
"""Can a player DELIBERATELY build an objective inside a normal game?

Each seat is dealt a secret objective and plays a bot that biases both its meld
choice and its placement toward building it, while still playing the base game.
"""
import statistics, random
from collections import Counter
import engine as E
from engine import nbrs, adjacent, meld_cards, meld_size, piece_placements
from objectives import score_all, POINTS

# objective -> terrains it wants, and whether it wants them CLUMPED together
WANTS = {
    "Coastal Control":   (("plains", "ocean"), True),
    "Island Nation":     (("ocean",), True),
    "Breadbasket":       (("plains",), True),
    "Highland Lake":     (("ocean", "mountain", "forest"), True),
    "Mountain Fortress": (("mountain",), True),
    "Mountain Range":    (("mountain",), True),
    "Greenway":          (("forest", "plains"), True),
    "Trade Delta":       (("ocean", "plains", "forest", "mountain"), True),
    "Rainforest":        (("forest",), True),
    "Silk Road":         (("plains",), True),
    "Ocean Corridor":    (("ocean",), True),
    "River Flow":        (("mountain", "forest", "plains", "ocean"), True),
}


def objective_bonus(game, p, plan):
    obj = game.goal.get(p.i)
    if not obj:
        return 0.0
    terr, clump = WANTS[obj]
    m, v = game.m, 0.0
    for cell, card, act in plan:
        t = card[1] if act == "explore" else (m.tiles[cell].terrain
                                              if cell in m.tiles else None)
        if t in terr:
            v += 5.0
            if clump:
                near = sum(1 for d in nbrs(*cell)
                           if d in m.tiles and m.tiles[d].terrain in terr
                           and m.tiles[d].owner == p.i)
                v += 2.5 * near
    return v


def seeking_bot(game, p, what, options):
    if len(options) > 14:
        ranked = sorted(options, key=lambda o: -meld_size(*o))
        options = ranked[:8] + random.sample(ranked[8:], 6)
    best, bv = None, -1e9
    for opt in options:
        kind, payload = opt
        cards = meld_cards(kind, payload)
        v = 0.35 * len(cards)
        civ = game.m.civ(p.i) or (set(game.m.tiles) | game.m.legal_spaces())
        for piece, ordered in game._split(kind, list(cards)):
            pl = piece_placements(game.m, piece, ordered, civ, p.i, p.gold, cap=12)
            v += max((E.value_placement(game, p, x) + objective_bonus(game, p, x)
                      for x in pl), default=0.2 * len(piece))
        if v > bv:
            best, bv = opt, v
    return best


_orig = E.Game._place
def _place(self, p, cards):
    """Same as the engine, but placements are ranked with the objective bonus."""
    self._obj_mode = True
    _orig(self, p, cards)
E.value_placement_base = E.value_placement
def vp(game, p, plan):
    return E.value_placement_base(game, p, plan) + objective_bonus(game, p, plan)
E.value_placement = vp


def run(G=30, seeking=True):
    done, tries, rounds_at = Counter(), Counter(), Counter()
    objs = list(WANTS)
    for s in range(G):
        g = E.Game(3, seed=s, bot=seeking_bot if seeking else E.smart_bot)
        g.smart = True
        random.seed(s)
        g.goal = {i: objs[(s * 3 + i) % len(objs)] for i in range(3)} if seeking else {}
        while not g.finished() and g.round < 80:
            g.play_round()
        for p in g.P:
            obj = objs[(s * 3 + p.i) % len(objs)]
            tries[obj] += 1
            mine = {c for c, t in g.m.tiles.items() if t.owner == p.i}
            if score_all(g.m, mine)[obj]:
                done[obj] += 1
    return done, tries


if __name__ == "__main__":
    d1, t1 = run(30, seeking=True)
    E.value_placement = E.value_placement_base
    d0, t0 = run(30, seeking=False)
    print("CAN A PLAYER DELIBERATELY BUILD IT?  30 three-player games each\n")
    print(f"{'objective':20}{'pts':>5}{'passive':>10}{'seeking':>10}{'verdict':>22}")
    for o in WANTS:
        pas = 100*d0[o]/max(t0[o],1); seek = 100*d1[o]/max(t1[o],1)
        if seek >= 70:   v = "trivial"
        elif seek >= 30: v = "achievable"
        elif seek >= 10: v = "hard"
        else:            v = "not buildable"
        print(f"{o:20}{POINTS[o]:>5}{pas:>9.0f}%{seek:>9.0f}%{v:>22}")
