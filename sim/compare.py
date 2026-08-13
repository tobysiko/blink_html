# -*- coding: utf-8 -*-
import statistics
from collections import Counter
import engine as E
from run import check

def play(n, seed, bot, cap=80):
    g = E.Game(n, seed=seed, bot=bot)
    g.bot = bot
    check(g, "setup")
    while not g.finished() and g.round < cap:
        g.play_round()
        check(g, f"r{g.round}")
    return g

print("SAME POLICY IN EVERY SEAT — how long is a game, and does anyone grow?\n")
print(f"{'policy':10}{'players':>8}{'rounds':>9}{'in Founding at end':>21}{'tiles':>8}")
for name, bot in (("random", E.random_bot), ("greedy", E.greedy_bot), ("turtle", E.turtle_bot)):
    for n in (2, 3, 4):
        L, fnd, tl = [], 0, []
        for s in range(40):
            g = play(n, s, bot)
            L.append(g.round); tl.append(len(g.m.terr))
            fnd += sum(1 for p in g.P if p.band() == 0)
        print(f"{name:10}{n:>8}{statistics.median(L):>9.0f}{100*fnd/(80*n):>20.0f}%{statistics.mean(tl):>8.0f}")

print("\n\nHEAD TO HEAD — seat 0 greedy, seat 1 turtle, seat 2 random (3 players)\n")
res = Counter(); tot = Counter(); comp = {0: Counter(), 1: Counter(), 2: Counter()}
for s in range(150):
    g = play(3, s, E.mixed([E.greedy_bot, E.turtle_bot, E.random_bot]))
    sc = g.score()
    best = max(sc, key=lambda d: (d["total"], d["gold"]))
    res[best["seat"]] += 1
    for d in sc:
        tot[d["seat"]] += d["total"]
        for k in ("pop", "vrow", "dom"):
            comp[d["seat"]][k] += d[k]
names = {0: "greedy", 1: "turtle", 2: "random"}
for i in (0, 1, 2):
    c = comp[i]
    print(f"  {names[i]:8} wins {100*res[i]/150:4.0f}%   mean score {tot[i]/150:5.1f}"
          f"   (population {c['pop']/150:4.1f}, victory row {c['vrow']/150:4.1f},"
          f" dominance {c['dom']/150:4.1f})")
