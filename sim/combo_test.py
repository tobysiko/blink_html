# -*- coding: utf-8 -*-
"""Combination melds: A/B against the current rules.

Proposal: any two multi-card melds may be played together if they fit within
the meld limit and share no cards. No single cards as components. pair+pair and
3+2 are excluded because "twoset" already covers them, so the new ground is
everything involving a straight.

Same seeds on both sides, so the two columns are the same games under two rules.

  python3 combo_test.py [games] [players]
"""
import sys
from collections import Counter
import engine as E

GAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 60
NP = int(sys.argv[2]) if len(sys.argv) > 2 else 3


def run(combo):
    E.COMBO_MELDS = combo
    st = Counter()
    scores = []
    for gi in range(GAMES):
        g = E.Game(NP, seed=5100 + gi, bot=E.smart_bot)
        g.smart = True
        while not g.finished() and g.round < 80:
            g.play_round()
        st["rounds"] += g.round
        for k, v in g.stats.items():
            if k.startswith(("meld_", "shape_", "limit_")) or k in (
                    "explore", "attack", "cards_to_gold", "cards_played"):
                st[k] += v
        for r in g.score():
            st["pop"] += r["pop"]; st["vrow"] += r["vrow"]; st["dom"] += r["dom"]
            st["total"] += r["pop"] + r["vrow"] + r["dom"]
    return st, scores


base, _ = run(False)
comb, _ = run(True)
E.COMBO_MELDS = False

melds_b = sum(base[f"meld_{i}"] for i in range(1, 6))
melds_c = sum(comb[f"meld_{i}"] for i in range(1, 6))

print(f"\nCombination melds — {NP} players, {GAMES} games each, same seeds\n")
print(f"{'':32s}{'baseline':>12s}{'combo':>12s}{'change':>12s}")


def row(label, b, c, pct=False, dp=1):
    if pct:
        d = f"{c - b:+.1f} pts"
        print(f"  {label:30s}{b:11.1f}%{c:11.1f}%{d:>12s}")
    else:
        d = f"{(c-b)/b*100:+.0f}%" if b else "—"
        print(f"  {label:30s}{b:12.{dp}f}{c:12.{dp}f}{d:>12s}")


row("rounds per game", base["rounds"] / GAMES, comb["rounds"] / GAMES)
row("melds played per game", melds_b / GAMES, melds_c / GAMES)
print()
for i in range(1, 6):
    row(f"melds of {i} cards",
        base[f"meld_{i}"] / melds_b * 100, comb[f"meld_{i}"] / melds_c * 100, pct=True)
print()
row("4+ card melds per game",
    (base["meld_4"] + base["meld_5"]) / GAMES, (comb["meld_4"] + comb["meld_5"]) / GAMES)
row("5 card melds per game", base["meld_5"] / GAMES, comb["meld_5"] / GAMES, dp=2)
print()
print("  meld shapes played (% of all melds)")
kinds = sorted({k[6:] for k in list(base) + list(comb) if k.startswith("shape_")})
for kd in kinds:
    row(f"    {kd}", base[f"shape_{kd}"] / melds_b * 100,
        comb[f"shape_{kd}"] / melds_c * 100, pct=True)
print()
row("cards played per game", base["cards_played"] / GAMES, comb["cards_played"] / GAMES)
row("cards turned to gold per game",
    base["cards_to_gold"] / GAMES, comb["cards_to_gold"] / GAMES)
row("explores per game", base["explore"] / GAMES, comb["explore"] / GAMES)
print()
tot_b, tot_c = base["total"], comb["total"]
row("mean final score", tot_b / (GAMES * NP), comb["total"] / (GAMES * NP))
for k, lbl in (("pop", "population"), ("vrow", "victory row"), ("dom", "dominance")):
    row(f"  {lbl} share", base[k] / tot_b * 100, comb[k] / tot_c * 100, pct=True)
print()
print("  time spent at each meld limit (% of meld decisions)")
tb = sum(base[f"limit_{i}"] for i in range(2, 6))
tc = sum(comb[f"limit_{i}"] for i in range(2, 6))
for i in range(2, 6):
    row(f"    limit {i}", base[f"limit_{i}"] / tb * 100, comb[f"limit_{i}"] / tc * 100, pct=True)
