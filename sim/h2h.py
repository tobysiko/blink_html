import sys
from collections import Counter
import engine as E
res, tot = Counter(), Counter()
G = int(sys.argv[1])
for s in range(G):
    g = E.Game(3, seed=s, bot=E.mixed([E.smart_bot, E.greedy_bot, E.turtle_bot]))
    g.smart = True
    while not g.finished() and g.round < 80: g.play_round()
    sc = g.score()
    res[max(sc, key=lambda d: (d["total"], d["gold"]))["seat"]] += 1
    for d in sc: tot[d["seat"]] += d["total"]
print(f"HEAD TO HEAD, 3 players, {G} games")
for i, nm in enumerate(("smart", "greedy", "turtle")):
    print(f"  {nm:8} wins {100*res[i]/G:4.0f}%   mean score {tot[i]/G:5.1f}")
