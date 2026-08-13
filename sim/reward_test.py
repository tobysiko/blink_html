# -*- coding: utf-8 -*-
"""Every trick-reward structure, head to head, same seeds, pro bots.

The question: what should winning a trick be worth, and what (if anything)
should losing one pay?

Structures compared
  dock          CURRENT RULE. Winner spends every card; everyone else spends
                one fewer and takes 1 gold for the card left out.
  none          Control nobody had tested: everyone spends their whole meld and
                the trick is worth nothing but initiative.
  bonus         Winner spends one extra card from hand (1 gold if hand empty).
                Losers get nothing beyond keeping all their cards.
  bonus+1last   ...and the player whose meld ranked LAST takes 1 gold.
  bonus+2last   ...2 gold.
  bonus+1all    ...1 gold to every non-winner.

Run: python3 reward_test.py [games] [players...]
"""
import sys, statistics, math
import engine as E

STRUCTURES = [
    # label,        WINNER_BONUS_CARD, GIVE_BONUS_CARD, consolation, gold
    ("dock (current)",  False, True,  "none", 1),
    ("none",            True,  False, "none", 1),
    ("bonus",           True,  True,  "none", 1),
    ("bonus +1 last",   True,  True,  "last", 1),
    ("bonus +2 last",   True,  True,  "last", 2),
    ("bonus +1 all",    True,  True,  "all",  1),
]


def measure(n, games, wbc, gbc, consol, amt, cap=80):
    gaps, lasts, leads, rep, cashed, food, rounds = [], [], [], [], [], [], []
    for s in range(games):
        E.Game.WINNER_BONUS_CARD = wbc
        E.Game.GIVE_BONUS_CARD = gbc
        E.Game.LOSER_CONSOLATION = consol
        E.Game.CONSOLATION_GOLD = amt
        g = E.Game(n, seed=s, bot=E.pro_bot)
        g.smart = True
        g.pro = set(range(n))
        g._deal()
        prev, same, tot = None, 0, 0
        while not g.finished() and g.round < cap:
            g.play_round()
            tot += 1
            if prev is not None and g.leader == prev:
                same += 1
            prev = g.leader
        sc = sorted(g.score(), key=lambda d: -d["total"])
        gaps.append(sc[0]["total"] - sc[-1]["total"])
        lasts.append(sc[-1]["total"])
        leads.append(sc[0]["total"])
        rep.append(same / max(1, tot - 1))
        st = g.stats
        played = max(1, st.get("cards_played", 0))
        cashed.append(100 * st.get("cards_to_gold", 0) / played)
        gi = sum(v for k, v in st.items() if k.startswith("gold_in"))
        food.append(100 * st.get("food_paid", 0) / max(1, gi))
        rounds.append(g.round)
    E.Game.WINNER_BONUS_CARD = False
    E.Game.GIVE_BONUS_CARD = True
    E.Game.LOSER_CONSOLATION = "none"
    E.Game.CONSOLATION_GOLD = 1
    m = statistics.mean
    ci = lambda x: 1.96 * statistics.stdev(x) / math.sqrt(len(x))
    return dict(gap=m(gaps), gap_ci=ci(gaps), last=m(lasts), last_ci=ci(lasts),
                lead=m(leads), rep=100 * m(rep), cashed=m(cashed),
                food=m(food), rounds=m(rounds))


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    counts = [int(a) for a in sys.argv[2:]] or [3]

    for n in counts:
        print(f"\n{n} PLAYERS — {games} games, pro bots, identical seeds "
              f"(chance repeat {100/n:.0f}%)\n")
        print(f"  {'structure':16}{'gap':>13}{'last place':>14}"
              f"{'leader':>8}{'repeat':>8}{'cashed':>8}{'food':>7}{'rds':>6}")
        for label, wbc, gbc, consol, amt in STRUCTURES:
            r = measure(n, games, wbc, gbc, consol, amt)
            print(f"  {label:16}{r['gap']:>6.1f} ±{r['gap_ci']:<5.1f}"
                  f"{r['last']:>7.1f} ±{r['last_ci']:<5.1f}{r['lead']:>8.1f}"
                  f"{r['rep']:>7.0f}%{r['cashed']:>7.0f}%{r['food']:>6.0f}%"
                  f"{r['rounds']:>6.1f}")
    print("\n  gap    = leader minus last place (lower is a closer game)")
    print("  repeat = same player wins consecutive tricks (snowball measure)")
    print("  cashed = share of cards turned into gold — the central decision")


if __name__ == "__main__":
    main()
