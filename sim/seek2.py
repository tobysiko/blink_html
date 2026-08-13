# -*- coding: utf-8 -*-
import random
from collections import Counter
import engine as E
from engine import nbrs, meld_cards, meld_size, piece_placements
from obj2 import CANDIDATES, frontier

def bonus(game, p, plan):
    obj = game.goal.get(p.i)
    if not obj: return 0.0
    terr = CANDIDATES[obj][1]
    m, v = game.m, 0.0
    for cell, card, act in plan:
        t = card[1] if act == "explore" else (m.tiles[cell].terrain if cell in m.tiles else None)
        if t in terr:
            v += 5.0
            v += 2.5 * sum(1 for d in nbrs(*cell) if d in m.tiles
                           and m.tiles[d].terrain in terr and m.tiles[d].owner == p.i)
    return v

base = E.value_placement
E.value_placement = lambda g, p, pl: base(g, p, pl) + bonus(g, p, pl)

def bot(game, p, what, options):
    if len(options) > 14:
        r = sorted(options, key=lambda o: -meld_size(*o))
        options = r[:8] + random.sample(r[8:], 6)
    best, bv = None, -1e9
    for opt in options:
        cards = meld_cards(*opt)
        v = 0.35 * len(cards)
        civ = game.m.civ(p.i) or (set(game.m.tiles) | game.m.legal_spaces())
        for piece, ordered in game._split(opt[0], list(cards)):
            pl = piece_placements(game.m, piece, ordered, civ, p.i, p.gold, cap=12)
            v += max((E.value_placement(game, p, x) for x in pl), default=0.2*len(piece))
        if v > bv: best, bv = opt, v
    return best

names = list(CANDIDATES)
done, tries = Counter(), Counter()
G = 62
for s in range(G):
    g = E.Game(3, seed=s, bot=bot); g.smart = True
    random.seed(s)
    g.goal = {i: names[(s*3+i) % len(names)] for i in range(3)}
    while not g.finished() and g.round < 80: g.play_round()
    for p in g.P:
        o = names[(s*3+p.i) % len(names)]
        tries[o] += 1
        mine = {c for c, t in g.m.tiles.items() if t.owner == p.i}
        hit = frontier(g.m, mine, p.i) if o == "Frontier" else CANDIDATES[o][0](g.m, mine)
        if hit: done[o] += 1
print(f"THREE-TILE CANDIDATES — seeking bots, {G} three-player games\n")
print(f"{'objective':20}{'tried':>7}{'achieved':>10}{'verdict':>16}")
for o in names:
    r = 100*done[o]/max(tries[o],1)
    v = "too easy" if r >= 75 else "good" if r >= 30 else "hard" if r >= 12 else "cut"
    print(f"{o:20}{tries[o]:>7}{r:>9.0f}%{v:>16}")
