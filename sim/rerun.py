# -*- coding: utf-8 -*-
"""Which findings survive bots that actually decide where to put things?"""
import sys, time, statistics
from collections import Counter
import engine as E
from run import check, conservation

def play(n, seed, bot, smart, cap=80, verify=False):
    g = E.Game(n, seed=seed, bot=bot); g.smart = smart
    while not g.finished() and g.round < cap:
        g.play_round()
        if verify:
            check(g, f"r{g.round}"); conservation(g, f"r{g.round}")
    return g

def profile(n, bot, smart, games, label):
    L, st, bands, comp, tiles = [], Counter(), Counter(), Counter(), []
    for s in range(games):
        g = play(n, s, bot, smart, verify=(s < 5))
        L.append(g.round); st += g.stats; tiles.append(len(g.m.tiles))
        for d in g.score():
            bands[d["band"]] += 1
            for k in ("pop", "vrow", "dom"): comp[k] += d[k]
    tot = sum(comp.values())
    print(f"  {label:22} rounds {statistics.median(L):4.0f}   "
          f"settle {st['settle']/games:5.1f}  kills {st['killed_by_attack']/games:5.1f}  "
          f"explore {st['explore']/games:5.1f}   "
          f"score: pop {100*comp['pop']/tot:2.0f}% row {100*comp['vrow']/tot:2.0f}% "
          f"dom {100*comp['dom']/tot:2.0f}%   Empire {100*bands['Empire']/(games*n):3.0f}%")

t0 = time.time()
print("BOTS THAT CHOOSE WHERE TO PLAY (smart) vs BOTS THAT DO NOT\n")
for n in (2, 3, 4):
    print(f"{n} players")
    profile(n, E.greedy_bot, False, 25, "greedy, random place")
    profile(n, E.smart_bot,  True,  25, "smart, chosen place")
print(f"\n[{time.time()-t0:.0f}s]")

print("\nHEAD TO HEAD, 3 players — smart vs greedy vs turtle\n")
res = Counter(); tot = Counter()
G = 60
for s in range(G):
    g = E.Game(3, seed=s, bot=E.mixed([E.smart_bot, E.greedy_bot, E.turtle_bot]))
    g.smart = True
    while not g.finished() and g.round < 80: g.play_round()
    sc = g.score()
    res[max(sc, key=lambda d: (d["total"], d["gold"]))["seat"]] += 1
    for d in sc: tot[d["seat"]] += d["total"]
for i, nm in enumerate(("smart", "greedy", "turtle")):
    print(f"  {nm:8} wins {100*res[i]/G:4.0f}%   mean score {tot[i]/G:5.1f}")
