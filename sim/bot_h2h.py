# -*- coding: utf-8 -*-
"""Is pro_bot actually better than smart_bot? Head to head, seats rotated.

A bot is only "better" if it beats the other one at the table. This seats one
pro against the rest and rotates which seat it occupies, so seat order and deal
luck cancel out. Anything short of a clear margin means the new policies are
noise dressed up as improvement.

Run: python3 bot_h2h.py [games] [players]
"""
import sys, statistics, math
from collections import Counter
import engine as E


def play(n, seed, pro_seats, cap=80):
    def mixed(game, p, what, options):
        return (E.pro_bot(game, p, what, options) if p.i in pro_seats
                else E.smart_bot(game, p, what, options))
    g = E.Game(n, seed=seed, bot=mixed)
    g.smart = True
    g.pro = set(pro_seats)
    g._deal()                       # redeal so the pro seat drafts properly
    while not g.finished() and g.round < cap:
        g.play_round()
    return g


def h2h(n, games, n_pro=1):
    wins = 0
    pro_sc, smart_sc = [], []
    for s in range(games):
        for rot in range(n):                     # rotate which seat is pro
            pro_seats = {(rot + k) % n for k in range(n_pro)}
            g = play(n, s, pro_seats)
            sc = {d["seat"]: d["total"] for d in g.score()}
            top = max(sc.values())
            best = [k for k, v in sc.items() if v == top]
            if all(b in pro_seats for b in best):
                wins += 1
            elif any(b in pro_seats for b in best):
                wins += 0.5                      # shared win
            for k, v in sc.items():
                (pro_sc if k in pro_seats else smart_sc).append(v)
    total = games * n
    return wins / total, statistics.mean(pro_sc), statistics.mean(smart_sc), total


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    print(f"pro_bot vs smart_bot — {n} players, {games} seeds x {n} seat "
          f"rotations\n")
    for n_pro in range(1, n):
        rate, ps, ss, total = h2h(n, games, n_pro)
        exp = 100 * n_pro / n
        se = 100 * math.sqrt(rate * (1 - rate) / total)
        print(f"  {n_pro} pro vs {n-n_pro} smart")
        print(f"    pro side wins   {100*rate:>5.1f}%  ±{1.96*se:.1f}   "
              f"(chance {exp:.0f}%)")
        print(f"    mean score      pro {ps:.1f}   smart {ss:.1f}")
    print("\n  A better bot must beat chance by more than the interval.")


if __name__ == "__main__":
    main()
