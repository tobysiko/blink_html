import sys, statistics
from collections import Counter
import engine as E
from run import check, conservation

def run(pol, G=14, n=3):
    E.Game.FORTIFY_POLICY = pol
    tot, L, comp = Counter(), [], Counter()
    for s in range(G):
        g = E.Game(n, seed=s, bot=E.smart_bot); g.smart = True
        while not g.finished() and g.round < 80:
            g.play_round()
            if s < 2: check(g, "x"); conservation(g, "x")
        tot += g.stats; L.append(g.round)
        for pl in g.P: tot["held"] += pl.gold
        for d in g.score():
            for k in ("pop", "vrow", "dom"): comp[k] += d[k]
    G3 = G
    f = tot["fortified"] / G3
    a = tot["absorbed_by_fortification"] / G3
    inc = (tot['gold_in_lost_trick'] + tot['gold_in_unplaceable']
           + tot['gold_in_other'] + tot['gold_in_effect_c']) / G3
    out = (tot['gold_out_upkeep'] + tot['gold_out_upgrade']
           + tot['gold_out_attack'] + tot['gold_out_fortify']) / G3
    sc = sum(comp.values())
    print(f"{pol:10}{statistics.median(L):>7.0f}{f:>9.1f}{a:>10.1f}"
          f"{(f/a if a else float('inf')):>9.1f}{tot['gold_out_fortify']/G3:>9.1f}"
          f"{tot['killed_by_attack']/G3:>8.1f}{tot['gold_out_upgrade']/G3:>10.1f}"
          f"{tot['held']/G3:>9.1f}{inc:>7.0f}{out:>6.0f}"
          f"   {100*comp['pop']/sc:.0f}/{100*comp['vrow']/sc:.0f}/{100*comp['dom']/sc:.0f}")

print("3 PLAYERS, 14 games — fortification policies\n")
print(f"{'policy':10}{'rounds':>7}{'fortifs':>9}{'absorbed':>10}{'coins/hit':>9}"
      f"{'gold@fort':>9}{'kills':>8}{'gold@upg':>10}{'unspent':>9}{'in':>7}{'out':>6}   pop/row/dom")
for pol in ("off", "eager", "targeted", "majority"):
    run(pol)
