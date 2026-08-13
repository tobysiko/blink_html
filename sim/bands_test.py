# -*- coding: utf-8 -*-
"""Would redistributing units across the bands get players to meld 5?"""
import sys, statistics
from collections import Counter
import engine as E

LAYOUTS = {
    "4/6/8/2  current": [4, 6, 8, 2],
    "4/6/6/4":          [4, 6, 6, 4],
    "3/5/6/6":          [3, 5, 6, 6],
    "2/4/6/8":          [2, 4, 6, 8],
    "5/5/5/5":          [5, 5, 5, 5],
}

def run(caps, G=10):
    E.BANDS = [(E.BANDS[i][0], caps[i], E.BANDS[i][2], E.BANDS[i][3]) for i in range(4)]
    tot, L = Counter(), []
    for s in range(G):
        g = E.Game(3, seed=s, bot=E.smart_bot); g.smart = True
        while not g.finished() and g.round < 80: g.play_round()
        tot += g.stats; L.append(g.round)
    melds = sum(tot[f"meld_{k}"] for k in range(1, 6))
    lim = sum(tot[f"limit_{k}"] for k in range(2, 6))
    return dict(rounds=statistics.median(L),
                m4=100*tot["meld_4"]/melds, m5=100*tot["meld_5"]/melds,
                big=100*(tot["meld_4"]+tot["meld_5"])/melds,
                at5=100*tot["limit_5"]/lim, at4=100*tot["limit_4"]/lim,
                starved=tot["starved_back"]/G, upkeep=tot["gold_out_upkeep"]/G)

BASE = list(E.BANDS)
print(f"{'bands':18}{'rounds':>8}{'time at limit 4':>17}{'at limit 5':>12}"
      f"{'melds of 4':>12}{'of 5':>7}{'upkeep paid':>13}")
for name, caps in LAYOUTS.items():
    E.BANDS = list(BASE)
    r = run(caps)
    print(f"{name:18}{r['rounds']:>8.0f}{r['at4']:>16.0f}%{r['at5']:>11.0f}%"
          f"{r['m4']:>11.1f}%{r['m5']:>6.1f}%{r['upkeep']:>13.1f}")
