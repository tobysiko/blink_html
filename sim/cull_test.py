# -*- coding: utf-8 -*-
"""Does famine-culling of over-limit stacks cause a death spiral?

Rule under test (per-tier population limits only): when starvation drops your
band, every stack now above your new limit sheds units back to the reserve.
Those units refill the reserve, which can drop the band again — so the cull
loops. This measures whether that loop actually cascades in play, or converges
after one pass.

Also measures the gap the rule leaves open: a band can drop from COMBAT losses
too, and combat does not cull. So a stack can sit over its owner's limit
between famines. If that is common, the rule needs to fire on any band drop,
not just on starvation.

Run: python3 cull_test.py [games] [players]
"""
import sys, statistics
from collections import Counter
import engine as E
from run import check, conservation


def play(n, seed, ladder, cull, cap=80, watch=False):
    E.Game.LIMIT_LADDER = ladder
    E.Game.STARVE_CULLS_STACKS = cull
    g = E.Game(n, seed=seed, bot=E.smart_bot)
    g.smart = True
    over_rounds = 0
    while not g.finished() and g.round < cap:
        g.play_round()
        check(g, f"r{g.round}")
        conservation(g, f"r{g.round}")
        if watch:
            # any tile above its OWNER'S current limit, between famines
            if any(t.units and len(t.units) > t.capacity_for(t.owner)
                   for t in g.m.tiles.values()):
                over_rounds += 1
    E.Game.LIMIT_LADDER = None
    E.Game.STARVE_CULLS_STACKS = True
    return g, over_rounds


def run(n, games, ladder, cull):
    rounds, score, gap, pop, culled, casc, depth, over, starved = \
        [], [], [], [], [], 0, 0, [], []
    for s in range(games):
        g, ov = play(n, s, ladder, cull, watch=True)
        rounds.append(g.round)
        sc = sorted(g.score(), key=lambda d: -d["total"])
        score.append(statistics.mean(d["total"] for d in sc))
        gap.append(sc[0]["total"] - sc[-1]["total"])
        pop.append(statistics.mean(d["pop"] for d in sc))
        culled.append(g.stats.get("culled_by_famine", 0))
        starved.append(g.stats.get("starved_back", 0))
        casc += g.stats.get("cull_cascaded", 0)
        depth = max(depth, g.stats.get("cull_depth_max", 0))
        over.append(100 * ov / max(1, g.round))
    m = statistics.mean
    return dict(rounds=m(rounds), score=m(score), gap=m(gap), pop=m(pop),
                culled=m(culled), starved=m(starved), casc=casc,
                depth=depth, over=m(over))


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    cases = [("gentle, grandfathered", "gentle", False),
             ("gentle, famine culls", "gentle", True),
             ("flat_wide, grandfathered", "flat_wide", False),
             ("flat_wide, famine culls", "flat_wide", True)]

    print(f"Famine culling of over-limit stacks — {n} players, "
          f"seeds 0..{games-1}, identical seeds every row")
    print("invariants and conservation checked every round of every game\n")
    print(f"  {'':26}{'rounds':>8}{'score':>8}{'gap':>7}{'units':>7}"
          f"{'starved':>9}{'culled':>8}{'cascades':>10}{'over-limit':>12}")
    for label, ladder, cull in cases:
        r = run(n, games, ladder, cull)
        print(f"  {label:26}{r['rounds']:>8.1f}{r['score']:>8.1f}{r['gap']:>7.1f}"
              f"{r['pop']:>7.1f}{r['starved']:>9.1f}{r['culled']:>8.1f}"
              f"{r['casc']:>10d}{r['over']:>11.0f}%")

    print("\n  starved  = units returned by missing food, per game (all players)")
    print("  culled   = units shed from over-limit stacks by famine, per game")
    print("  cascades = games where one famine culled, dropped a band, and "
          "culled again")
    print("  over-limit = share of rounds where SOME tile sits above its "
          "owner's current")
    print("               limit — the gap combat leaves, since combat never culls")


if __name__ == "__main__":
    main()
