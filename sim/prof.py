import sys, statistics
from collections import Counter
import engine as E
from run import check, conservation

def play(n, seed, bot, smart, cap=80, verify=False):
    g = E.Game(n, seed=seed, bot=bot); g.smart = smart
    while not g.finished() and g.round < cap:
        g.play_round()
        if verify: check(g, f"r{g.round}"); conservation(g, f"r{g.round}")
    return g

def profile(n, bot, smart, games, label):
    L, st, bands, comp = [], Counter(), Counter(), Counter()
    for s in range(games):
        g = play(n, s, bot, smart, verify=(s < 3))
        L.append(g.round); st += g.stats
        for d in g.score():
            bands[d["band"]] += 1
            for k in ("pop","vrow","dom"): comp[k] += d[k]
    tot = sum(comp.values())
    print(f"  {label:22} rounds {statistics.median(L):4.0f}   "
          f"settle {st['settle']/games:5.1f}  kills {st['killed_by_attack']/games:5.1f}  "
          f"explore {st['explore']/games:5.1f}   "
          f"pop {100*comp['pop']/tot:2.0f}% row {100*comp['vrow']/tot:2.0f}% dom {100*comp['dom']/tot:2.0f}%"
          f"   Empire {100*bands['Empire']/(games*n):3.0f}%")

n = int(sys.argv[1]); G = int(sys.argv[2])
print(f"{n} players")
profile(n, E.greedy_bot, False, G, "greedy, random place")
profile(n, E.smart_bot,  True,  G, "smart, chosen place")
