# -*- coding: utf-8 -*-
"""Three band layouts, current ruleset, 14 three-player games each."""
import statistics
from collections import Counter
import engine as E
from run import check, conservation

BASE = list(E.BANDS)

def run(caps, G=14):
    E.BANDS = [(BASE[i][0], caps[i], BASE[i][2], BASE[i][3]) for i in range(4)]
    tot, L, comp = Counter(), [], Counter()
    for s in range(G):
        g = E.Game(3, seed=s, bot=E.smart_bot); g.smart = True
        while not g.finished() and g.round < 80:
            g.play_round()
            if s < 2: check(g, "x"); conservation(g, "x")
        tot += g.stats; L.append(g.round)
        for pl in g.P: tot["held"] += pl.gold
        for d in g.score():
            for k in ("pop", "vrow", "dom"): comp[k] += d[k]
    melds = sum(tot[f"meld_{k}"] for k in range(1, 6))
    lim = sum(tot[f"limit_{k}"] for k in range(2, 6))
    sc = sum(comp.values())
    P = G * 3
    return dict(
        rounds=statistics.median(L),
        p5=tot["meld_5"] / P, p4=tot["meld_4"] / P,
        m4=100 * tot["meld_4"] / melds, m5=100 * tot["meld_5"] / melds,
        at4=100 * tot["limit_4"] / lim, at5=100 * tot["limit_5"] / lim,
        upkeep=tot["gold_out_upkeep"] / G, starved=tot["starved_back"] / G,
        held=tot["held"] / G, kills=tot["killed_by_attack"] / G,
        pop=100 * comp["pop"] / sc, row=100 * comp["vrow"] / sc, dom=100 * comp["dom"] / sc)

LAY = [("4/6/8/2  current", [4, 6, 8, 2]),
       ("5/5/5/5  equal",   [5, 5, 5, 5]),
       ("3/6/7/4  middle",  [3, 6, 7, 4]),
       ("2/4/6/8  proposed",[2, 4, 6, 8])]

res = [(n, run(c)) for n, c in LAY]
print("14 three-player games each — current ruleset")
print("(A declared blind, B in the map phase, proportional starvation, targeted fortify)\n")
print(f"{'layout':20}{'rounds':>8}{'melds of 5':>12}{'melds of 4':>12}{'BIG total':>11}"
      f"{'time@lim5':>11}{'upkeep':>9}{'unspent':>9}   score pop/row/dom")
for n, r in res:
    print(f"{n:20}{r['rounds']:>8.0f}{r['p5']:>12.2f}{r['p4']:>12.2f}"
          f"{r['p4']+r['p5']:>11.2f}{r['at5']:>10.0f}%{r['upkeep']:>9.1f}{r['held']:>9.1f}"
          f"   {r['pop']:.0f}/{r['row']:.0f}/{r['dom']:.0f}")
print("\n(melds of 4 and 5 are PER PLAYER PER GAME)")
print()
print(f"{'layout':20}{'% of all melds that are 4 cards':>34}{'5 cards':>10}")
for n, r in res:
    print(f"{n:20}{r['m4']:>33.1f}%{r['m5']:>9.1f}%")
