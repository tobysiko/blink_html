# -*- coding: utf-8 -*-
"""How much does the band's free-move allowance actually do?

Two questions the port raised and could not answer:
  1. what ends a v0.21 game — the 20th unit, or the market drying up?
  2. is 1/2/3/4 free moves per turn a quiet convenience or the main engine?

Run: python3 moves_test.py [games]
"""
import sys, statistics
from collections import Counter
import engine as E
from run import check, conservation


def play(n, seed, moves=None, cap=80, verify=False):
    g = E.Game(n, seed=seed, bot=E.smart_bot)
    g.smart = True
    if moves is not None:
        g.MOVE_CAP = moves                 # override the band allowance
    while not g.finished() and g.round < cap:
        g.play_round()
        if verify:
            check(g, f"r{g.round}")
            conservation(g, f"r{g.round}")
    return g


def run(n, games, moves=None):
    rounds, ends, mv, turns, tiles, pop, sc = [], Counter(), [], [], [], [], []
    for s in range(games):
        g = play(n, s, moves)
        rounds.append(g.round)
        ends[g.ended_on[0] if g.ended_on else "never triggered"] += 1
        mv.append(g.stats.get("free_move", 0))
        turns.append(g.round * n)
        tiles.append(len(g.m.terr))
        scores = g.score()
        pop.append(statistics.mean(d["pop"] for d in scores))
        sc.append(statistics.mean(d["total"] for d in scores))
    m = statistics.mean
    return dict(rounds=m(rounds), ends=ends, per_turn=m(mv) / max(1, m(turns)),
                tiles=m(tiles), pop=m(pop), score=m(sc))


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 20

    print("WHAT ENDS A v0.21 GAME\n")
    for n in (2, 3, 4):
        r = run(n, games)
        top = ", ".join(f"{k}: {v}" for k, v in r["ends"].most_common())
        print(f"  {n}p  {r['rounds']:.1f} rounds   {top}")

    print("\n\nFREE-MOVE SENSITIVITY — same seeds, allowance overridden\n")
    print(f"  {'allowance':>12}{'rounds':>9}{'moves/turn':>13}{'tiles':>8}"
          f"{'population':>13}{'score':>8}")
    for label, moves in (("band 1-4", None), ("0 (off)", 0), ("1 flat", 1),
                         ("2 flat", 2)):
        r = run(3, games, moves)
        print(f"  {label:>12}{r['rounds']:>9.1f}{r['per_turn']:>13.2f}"
              f"{r['tiles']:>8.1f}{r['pop']:>13.1f}{r['score']:>8.1f}")

    print("\n\nINVARIANTS under the new placement (3p, every round checked)")
    for s in range(min(games, 10)):
        play(3, s, verify=True)
    print("  ok — ten cards, twenty units, map connected, touch-two, "
          "tiles and cards conserved")


if __name__ == "__main__":
    main()
