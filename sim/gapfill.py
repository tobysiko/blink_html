# -*- coding: utf-8 -*-
import statistics
from collections import Counter
import engine as E
from run import check, conservation

def run(shift, drift, hold, disc=False, G=14):
    E.Game.USE_SHIFT, E.Game.USE_DRIFT = shift, drift
    E.Game.USE_HOLD_BACK, E.Game.DISCONNECT_PENALTY = hold, disc
    tot, L, comp = Counter(), [], Counter()
    for s in range(G):
        g = E.Game(3, seed=s, bot=E.smart_bot); g.smart = True
        while not g.finished() and g.round < 80:
            g.play_round()
            if s < 2: check(g, "x"); conservation(g, "x")
        tot += g.stats; L.append(g.round)
        for pl in g.P: tot["held"] += pl.gold
        for d in g.score():
            for k in ("pop", "vrow", "dom"): comp[k] += d[k]
    sc = sum(comp.values())
    return dict(r=statistics.median(L), up=tot["gold_out_upkeep"]/G,
                st=tot["starved_back"]/G, sh=tot["shifted"]/G,
                dr=tot["drifted"]/G, hb=tot["held_back"]/G,
                cul=tot["culled"]/G, settle=tot["settle"]/G,
                pop=100*comp["pop"]/sc, row=100*comp["vrow"]/sc, dom=100*comp["dom"]/sc,
                held=tot["held"]/G, kills=tot["killed_by_attack"]/G)

rows = [("none of the three (before)", (False, False, False)),
        ("+ shift only",               (True,  False, False)),
        ("+ shift + drift",            (True,  True,  False)),
        ("all three",                  (True,  True,  True))]
print("14 three-player games each — 2/4/6/8 bands, current ruleset\n")
print(f"{'configuration':28}{'rounds':>7}{'upkeep':>8}{'starved':>9}{'shifts':>8}"
      f"{'drifts':>8}{'held':>7}{'settles':>9}   pop/row/dom")
for label, (a, b, c) in rows:
    r = run(a, b, c)
    print(f"{label:28}{r['r']:>7.0f}{r['up']:>8.1f}{r['st']:>9.1f}{r['sh']:>8.1f}"
          f"{r['dr']:>8.1f}{r['hb']:>7.1f}{r['settle']:>9.1f}   "
          f"{r['pop']:.0f}/{r['row']:.0f}/{r['dom']:.0f}")
print()
r = run(True, True, True, disc=True)
print(f"{'all three + DISCONNECT PENALTY':28}{r['r']:>7.0f}{r['up']:>8.1f}{r['st']:>9.1f}"
      f"{r['sh']:>8.1f}{r['dr']:>8.1f}{r['hb']:>7.1f}{r['settle']:>9.1f}   "
      f"{r['pop']:.0f}/{r['row']:.0f}/{r['dom']:.0f}    (units culled {r['cul']:.1f}/game)")
print("\n  NOTE: the disconnect penalty is NOT a rule - §06 says splitting your")
print("  civilization is allowed, and §07 says drift may break it into pieces.")
