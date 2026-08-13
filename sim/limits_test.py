# -*- coding: utf-8 -*-
"""Variable per-tier population limits, A/B against the fixed terrain limits.

Idea under test: instead of Plains 3 / Forest 2 / Ocean 1 / Mountain 1 for
everyone all game, the limits GROW with the tile owner's band — flat at
Founding, everything stackable by Empire, with Mountain and Ocean staying low
for theme.

The rule that makes this interesting is also the risk: the limit is the TILE
OWNER'S, so a player at Empire holds four on a Plains that a Founding rival
could only hold one on. That is a compounding advantage, and the leader/laggard
gap below is the number that matters most.

Run: python3 limits_test.py [games] [players]
"""
import sys, statistics
from collections import Counter
import engine as E
from run import check, conservation

LADDERS = [("fixed (control)", None), ("flat_wide", "flat_wide"),
           ("gentle", "gentle")]


def play(n, seed, ladder, cap=80, verify=False):
    E.Game.LIMIT_LADDER = ladder
    g = E.Game(n, seed=seed, bot=E.smart_bot)
    g.smart = True
    while not g.finished() and g.round < cap:
        g.play_round()
        if verify:
            check(g, f"r{g.round}")
            conservation(g, f"r{g.round}")
    E.Game.LIMIT_LADDER = None
    return g


def measure(n, games, ladder):
    rounds, mean_sc, gap, pop, tiles, stacks, kills, ends = \
        [], [], [], [], [], [], [], Counter()
    lead_pop, last_pop = [], []
    for s in range(games):
        g = play(n, s, ladder)
        rounds.append(g.round)
        sc = sorted(g.score(), key=lambda d: -d["total"])
        mean_sc.append(statistics.mean(d["total"] for d in sc))
        gap.append(sc[0]["total"] - sc[-1]["total"])
        pop.append(statistics.mean(d["pop"] for d in sc))
        lead_pop.append(sc[0]["pop"])
        last_pop.append(sc[-1]["pop"])
        tiles.append(len(g.m.terr))
        # how much stacking actually happens
        occupied = [len(t.units) for t in g.m.tiles.values() if t.units]
        stacks.append(statistics.mean(occupied) if occupied else 0)
        kills.append(g.stats.get("killed_by_attack", 0))
        ends[g.ended_on[0] if g.ended_on else "never"] += 1
    m = statistics.mean
    return dict(rounds=m(rounds), score=m(mean_sc), gap=m(gap), pop=m(pop),
                tiles=m(tiles), stack=m(stacks), kills=m(kills),
                lead=m(lead_pop), last=m(last_pop), ends=ends)


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    print(f"Per-tier population limits — {n} players, seeds 0..{games-1}, "
          f"same seeds every column\n")
    res = [(name, measure(n, games, lad)) for name, lad in LADDERS]

    rows = [("rounds per game", "rounds", "{:.1f}"),
            ("mean final score", "score", "{:.1f}"),
            ("leader minus last", "gap", "{:.1f}"),
            ("units on map (mean)", "pop", "{:.1f}"),
            ("  leader's units", "lead", "{:.1f}"),
            ("  last place's units", "last", "{:.1f}"),
            ("units per occupied tile", "stack", "{:.2f}"),
            ("tiles on map at end", "tiles", "{:.1f}"),
            ("units killed per game", "kills", "{:.1f}")]
    head = "".join(f"{name:>17}" for name, _ in res)
    print(f"  {'':26}{head}")
    for label, key, fmt in rows:
        cells = "".join(f"{fmt.format(r[key]):>17}" for _, r in res)
        print(f"  {label:26}{cells}")
    print()
    for name, r in res:
        top = ", ".join(f"{k} {v}" for k, v in r["ends"].most_common())
        print(f"  ends · {name:16}{top}")

    print("\n\nINVARIANTS under each ladder (every round checked)")
    for name, lad in LADDERS:
        for s in range(min(games, 6)):
            play(n, s, lad, verify=True)
        print(f"  {name:16} ok — no tile ever exceeds its owner's limit")


if __name__ == "__main__":
    main()
