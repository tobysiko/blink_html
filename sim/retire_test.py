# -*- coding: utf-8 -*-
"""Does 'retire only from your hand' change the game? (v0.22 §10)

The old engine let a player retire a card they had just played to the map that
same turn, because it drew from hand + personal discard. That was a free lunch:
one card did map work AND banked its rank in the victory row. Restricting
retirement to the HAND makes research cost a card you could still have played.

Two questions, kept apart:
  A/B   what the rule change does to the shape of the game
  H2H   whether the bot's new retire heuristic is actually any good, because
        a rule that costs something is only measured properly by a player who
        chooses well. Max-rank was fine when retiring was free; it is a
        strategy now.

    python3 retire_test.py [games] [players]
"""
import statistics
import sys

import engine as E


def run(games, n, seed0=0, **flags):
    rounds, totals, vrow, ups, ends, ranks, blocked = [], [], [], [], [], [], 0
    for s in range(games):
        g = E.Game(n, seed=seed0 + s, bot=E.pro_bot)
        g.smart = True
        g.pro = set(range(n))
        for k, v in flags.items():
            setattr(g, k, v)
        g._deal()          # re-deal now that pro/flags are set, so the draft runs
        while not g.finished() and g.round < 80:
            g.play_round()
        sc = g.score()
        rounds.append(g.round)
        totals += [d["total"] for d in sc]
        vrow += [d["vrow"] for d in sc]
        ups.append(g.stats.get("upgrades", 0))
        ends.append(g.ended_on[0] if g.ended_on else "cap")
        if g.stats.get("upgrades"):
            ranks.append(g.stats.get("retire_rank", 0) / g.stats["upgrades"])
        blocked += g.stats.get("upgrade_no_card_to_retire", 0)
    return dict(rounds=statistics.mean(rounds), score=statistics.mean(totals),
                vrow=statistics.mean(vrow), ups=statistics.mean(ups),
                floor=min(totals), spread=max(totals) - min(totals),
                rank=(statistics.mean(ranks) if ranks else 0),
                blocked=blocked / games,
                onunits=sum(e == "last unit placed" for e in ends) / games)


def h2h(games, n, seed0=1000, **flags):
    """One seat plays the new heuristic, the rest play naive max-rank-from-hand.
    Seats rotate so the result is not a seat effect."""
    wins = 0
    for s in range(games):
        for seat in range(n):
            g = E.Game(n, seed=seed0 + s, bot=E.pro_bot)
            g.smart = True
            g.pro = set(range(n))
            for k, v in flags.items():
                setattr(g, k, v)
            naive = [i for i in range(n) if i != seat]
            orig = type(g)._pick_retire

            def pick(self, p, _n=set(naive), _o=orig):
                if p.i in _n and p.hand:
                    return max(p.hand, key=lambda c: c[0])
                return _o(self, p)

            type(g)._pick_retire = pick
            try:
                g._deal()
                while not g.finished() and g.round < 80:
                    g.play_round()
                best = max(g.score(), key=lambda d: (d["total"], d["gold"]))
                wins += int(best["seat"] == seat)
            finally:
                type(g)._pick_retire = orig
    return wins / (games * n)


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    print(f"\nA/B — {games} games, {n} players, pro bots, identical seeds\n")
    old = run(games, n, RETIRE_FROM_HAND_ONLY=False)
    new = run(games, n, RETIRE_FROM_HAND_ONLY=True)
    head = f"{'':26}{'hand + table (old)':>20}{'hand only (new)':>18}"
    print(head)
    print("-" * len(head))
    for key, label, fmt in (
            ("rounds", "rounds per game", "{:.1f}"),
            ("ups", "upgrades per game", "{:.1f}"),
            ("blocked", "research lost, empty hand", "{:.2f}"),
            ("rank", "mean rank retired", "{:.1f}"),
            ("vrow", "victory-row score", "{:.1f}"),
            ("score", "mean final score", "{:.1f}"),
            ("floor", "worst score seen", "{:.0f}"),
            ("spread", "best minus worst", "{:.0f}"),
            ("onunits", "ends on the last unit", "{:.0%}")):
        print(f"{label:26}{fmt.format(old[key]):>20}{fmt.format(new[key]):>18}")

    print(f"\nH2H — new retire heuristic vs naive max-rank, seats rotated")
    w = h2h(max(10, games // 2), n)
    print(f"  new heuristic wins {w:.1%}  (chance is {1/n:.1%}, "
          f"{max(10, games//2)*n} games)")

    print("\nRETIRE_RANK_W sweep — H2H against naive max-rank, seats rotated")
    print("  (0.0 = pure row-gain + hand material; large = effectively max-rank)")
    seeds = max(30, games)
    ci = 1.96 * (( (1/n) * (1 - 1/n) / (seeds * n)) ** 0.5)
    print(f"  chance {1/n:.1%}, 95% CI +/-{ci:.1%} on {seeds*n} games")
    for wt in (0.0, 0.4, 1.2, 4.0):
        w = h2h(seeds, n, RETIRE_RANK_W=wt)
        verdict = ("WORSE than naive" if w < 1/n - ci else
                   "better than naive" if w > 1/n + ci else
                   "indistinguishable from naive")
        print(f"  rank weight {wt:<5} wins {w:>6.1%}   {verdict}")


if __name__ == "__main__":
    main()
