# -*- coding: utf-8 -*-
"""Reward the trick winner instead of docking everyone else.

Base rule (v0.21 §04): the winner spends every card; everyone else spends ONE
FEWER and takes 1 gold for the card they left out.

Proposed: everyone spends their whole meld. The WINNER spends one EXTRA card
from hand on top — or takes 1 gold if their hand is already empty.

The relative gap between winner and loser is the same either way (one card).
What changes is the absolute level, and two things worth measuring fall out:

  1. the losers' consolation gold disappears — free income the economy
     currently leans on. Does food finally bite?
  2. the winner burns hand cards faster, so they recycle sooner and pay food
     more often. The reward carries its own cost.

Run: python3 bonus_test.py [games] [players]
"""
import sys, statistics
from collections import Counter
import engine as E
from run import check, conservation


def play(n, seed, bonus, cap=80, verify=False):
    E.Game.WINNER_BONUS_CARD = bonus
    g = E.Game(n, seed=seed, bot=E.smart_bot)
    g.smart = True
    while not g.finished() and g.round < cap:
        g.play_round()
        if verify:
            check(g, f"r{g.round}")
            conservation(g, f"r{g.round}")
    E.Game.WINNER_BONUS_CARD = False
    return g


def measure(n, games, bonus):
    out = Counter()
    rounds, score, gap, pop, gold, food, starved = [], [], [], [], [], [], []
    recyc, cashed, upg, wins_spread = [], [], [], []
    for s in range(games):
        g = play(n, s, bonus)
        rounds.append(g.round)
        sc = sorted(g.score(), key=lambda d: -d["total"])
        score.append(statistics.mean(d["total"] for d in sc))
        gap.append(sc[0]["total"] - sc[-1]["total"])
        pop.append(statistics.mean(d["pop"] for d in sc))
        st = g.stats
        gold.append(sum(v for k, v in st.items() if k.startswith("gold_in")))
        food.append(st.get("food_paid", 0))
        starved.append(st.get("starved_back", 0))
        recyc.append(st.get("recycles", 0))
        played = max(1, st.get("cards_played", 0))
        cashed.append(100 * st.get("cards_to_gold", 0) / played)
        upg.append(st.get("upgrades", 0))
        out["bonus_card"] += st.get("bonus_card", 0)
        out["bonus_gold"] += st.get("bonus_gold", 0)
    m = statistics.mean
    return dict(rounds=m(rounds), score=m(score), gap=m(gap), pop=m(pop),
                gold=m(gold), food=m(food), starved=m(starved),
                recyc=m(recyc), cashed=m(cashed), upg=m(upg),
                bc=out["bonus_card"] / games, bg=out["bonus_gold"] / games)


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    print(f"Winner bonus card vs losers docked a card — {n} players, "
          f"seeds 0..{games-1}, identical seeds\n")
    A = measure(n, games, False)
    B = measure(n, games, True)

    rows = [("rounds per game", "rounds", "{:.1f}"),
            ("mean final score", "score", "{:.1f}"),
            ("leader minus last", "gap", "{:.1f}"),
            ("units on map (mean)", "pop", "{:.1f}"),
            ("gold earned per game", "gold", "{:.0f}"),
            ("food paid per game", "food", "{:.1f}"),
            ("units starved per game", "starved", "{:.2f}"),
            ("hand recycles per game", "recyc", "{:.1f}"),
            ("cards cashed for gold %", "cashed", "{:.0f}%"),
            ("upgrades bought", "upg", "{:.1f}")]
    print(f"  {'':28}{'base rule':>12}{'winner bonus':>14}{'change':>10}")
    for label, key, fmt in rows:
        a, b = A[key], B[key]
        d = "" if not a else f"{100*(b-a)/a:+.0f}%"
        print(f"  {label:28}{fmt.format(a):>12}{fmt.format(b):>14}{d:>10}")
    print(f"\n  bonus cards played per game: {B['bc']:.1f}")
    print(f"  bonus taken as gold (hand empty): {B['bg']:.1f}")
    print(f"  food as a share of income: base {100*A['food']/A['gold']:.0f}%, "
          f"bonus {100*B['food']/B['gold']:.0f}%")

    print("\n\nINVARIANTS with the bonus card (every round checked)")
    for s in range(min(games, 8)):
        play(n, s, True, verify=True)
    print("  ok — ten cards per player, twenty units, tiles and cards conserved")


if __name__ == "__main__":
    main()
