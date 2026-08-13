# -*- coding: utf-8 -*-
"""How much does the starting hand decide the game?

The worry: one player is dealt most of the top ranks and the draft cannot undo
it, because keeping several of them is legal.

Two channels matter, and they are NOT the same:
  MELDABILITY  pairs and runs let you play more cards, and the trick goes to
               the most cards. This is the trick-winning channel.
  RANK         only breaks ties in a trick — but it is a scoring channel, since
               the victory row scores its CENTRE rank.

Measures the correlation of each against final score, then tests fixes:
  equal_top    deal the top ranks round-robin so everyone gets the same number
  mirrored     every player gets an identical hand (perfect symmetry, control)

Run: python3 hand_test.py [games] [players]
"""
import sys, statistics, math, random
from collections import Counter
import engine as E


def meldability(hand):
    """Largest meld playable from this hand, ignoring the band limit — the
    honest measure of 'can I win tricks with this'."""
    ranks = sorted(c[0] for c in hand)
    best = 1
    cnt = Counter(ranks)
    best = max(best, max(cnt.values()))                 # biggest set
    uniq = sorted(set(ranks))
    run = 1
    for i in range(1, len(uniq)):                       # longest run
        run = run + 1 if uniq[i] == uniq[i - 1] + 1 else 1
        best = max(best, run)
    # two-set melds: best pair of sets
    twos = sorted((v for v in cnt.values() if v >= 2), reverse=True)
    if len(twos) >= 2:
        best = max(best, twos[0] + twos[1])
    return best


def top_ranks(hand, n):
    """Cards at the top two ranks of the starting deck for this count."""
    hi = 10
    return sum(1 for c in hand if c[0] >= hi - 1)


def corr(xs, ys):
    n = len(xs)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sx, sy = statistics.pstdev(xs), statistics.pstdev(ys)
    if sx == 0 or sy == 0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (n * sx * sy)


def equalise_top(game, n):
    """Redeal so the top two ranks are shared out as evenly as possible."""
    hands = [p.hand for p in game.P]
    pool = [c for h in hands for c in h]
    hi = [c for c in pool if c[0] >= 9]
    rest = [c for c in pool if c[0] < 9]
    random.shuffle(hi); random.shuffle(rest)
    new = [[] for _ in range(n)]
    for k, c in enumerate(hi):                 # round-robin the top ranks
        new[k % n].append(c)
    for h in new:                              # fill to ten from the rest
        while len(h) < 10:
            h.append(rest.pop())
    for i, p in enumerate(game.P):
        p.hand = new[i]


def mirror(game, n):
    """Every player gets the SAME ten cards (different suits where possible).
    A control, not a proposal: it removes deal luck entirely."""
    base = list(game.P[0].hand)
    pool = [c for p in game.P for c in p.hand]
    for i, p in enumerate(game.P):
        want = [r for r, _ in base]
        h = []
        for r in want:
            match = next((c for c in pool if c[0] == r), None)
            if match is None:
                match = pool[0]
            pool.remove(match)
            h.append(match)
        p.hand = h


def play(n, seed, fix=None):
    g = E.Game(n, seed=seed, bot=E.smart_bot)
    g.smart = True
    if fix:
        fix(g, n)
    start = [(meldability(p.hand),
              sum(c[0] for c in p.hand),
              top_ranks(p.hand, n)) for p in g.P]
    while not g.finished() and g.round < 80:
        g.play_round()
    sc = {d["seat"]: d for d in g.score()}
    return start, [sc[i]["total"] for i in range(n)], g


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    print(f"{n} players, {games} games\n")
    print("DOES THE STARTING HAND PREDICT THE RESULT?\n")
    meld, ranksum, tops, finals = [], [], [], []
    best_hand_wins = 0
    for s in range(games):
        start, totals, _ = play(n, s)
        for k, (m, r, t) in enumerate(start):
            meld.append(m); ranksum.append(r); tops.append(t)
            finals.append(totals[k])
        # did the player with the most meldable hand win?
        bm = max(range(n), key=lambda k: start[k][0])
        if totals[bm] == max(totals):
            best_hand_wins += 1
    print(f"  correlation with final score")
    print(f"    meldability (largest meld in hand) {corr(meld, finals):>7.2f}")
    print(f"    sum of ranks                       {corr(ranksum, finals):>7.2f}")
    print(f"    number of 9s and 10s               {corr(tops, finals):>7.2f}")
    print(f"\n  the most meldable starting hand won {100*best_hand_wins/games:.0f}% "
          f"of games (chance = {100/n:.0f}%)")

    print("\n\nDOES EQUALISING THE TOP RANKS CHANGE ANYTHING?\n")
    print(f"  {'':22}{'mean score':>12}{'spread':>9}{'top-rank spread':>18}")
    for label, fix in (("as dealt (current)", None),
                       ("top ranks shared out", equalise_top),
                       ("identical hands", mirror)):
        gaps, means, tspread = [], [], []
        for s in range(games):
            start, totals, _ = play(n, s, fix)
            gaps.append(max(totals) - min(totals))
            means.append(statistics.mean(totals))
            t = [x[2] for x in start]
            tspread.append(max(t) - min(t))
        print(f"  {label:22}{statistics.mean(means):>12.1f}"
              f"{statistics.mean(gaps):>9.1f}{statistics.mean(tspread):>18.1f}")
    print("\n  spread = leader minus last place, final score")
    print("  top-rank spread = most 9s/10s held minus fewest, at the start")


if __name__ == "__main__":
    main()
