import random, math, sys
import engine as E
from obj2 import CANDIDATES
names = sys.argv[1].split(","); N = int(sys.argv[2])
hit = {n: 0 for n in names}; tot = 0
for g in range(N):
    game = E.Game(3, seed=9000 + g, bot=E.smart_bot)
    while not game.finished() and game.round < 80: game.play_round()
    for p in game.P:
        mine = {c for c, t in game.m.tiles.items() if t.owner == p.i}
        tot += 1
        for n in names: hit[n] += CANDIDATES[n][0](game.m, mine)
tot //= len(names) if False else 1
for n in names:
    k, s = hit[n], tot
    r = k / s; se = math.sqrt(r * (1 - r) / s) * 1.96
    print(f"  {n:16s} {s:4d} samples   {r*100:5.1f}%   95% CI [{max(0,(r-se))*100:.0f}–{(r+se)*100:.0f}]")
