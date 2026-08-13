import sys, statistics
from collections import Counter
import engine as E
from run import check, conservation

def run(a, b, G=14):
    E.Game.USE_EFFECT_A, E.Game.USE_EFFECT_B = a, b
    tot, L, comp, wins_by_a = Counter(), [], Counter(), Counter()
    for s in range(G):
        g = E.Game(3, seed=s, bot=E.smart_bot); g.smart = True
        while not g.finished() and g.round < 80:
            g.play_round()
            if s < 2: check(g, "x"); conservation(g, "x")
        tot += g.stats; L.append(g.round)
        for pl in g.P: tot["held"] += pl.gold; tot["scored_rows"] += len(pl.vrow)
        sc = g.score()
        for d in sc:
            for k in ("pop", "vrow", "dom"): comp[k] += d[k]
    return tot, L, comp

def show(label, tot, L, comp):
    G = 14; sc = sum(comp.values())
    a, b, c = tot["effect_a_used"]/G, tot["effect_b_used"]/G, tot["effect_c_used"]/G
    kept = tot["scored_rows"]/G
    spent = a + b + c
    inc = (tot['gold_in_lost_trick']+tot['gold_in_unplaceable']
           +tot['gold_in_other']+tot['gold_in_effect_c'])/G
    out = (tot['gold_out_upkeep']+tot['gold_out_upgrade']
           +tot['gold_out_attack']+tot['gold_out_fortify'])/G
    print(f"{label}")
    print(f"   rounds {statistics.median(L):.0f}   gold in {inc:5.1f}  out {out:5.1f}  "
          f"unspent {tot['held']/G:5.1f}   kills {tot['killed_by_attack']/G:4.1f}")
    print(f"   victory-row cards per game: kept to score {kept:4.1f} | "
          f"spent A {a:4.1f} | B {b:4.1f} | C {c:4.1f}"
          + (f"   (A mean rank {tot['effect_a_rank']/max(tot['effect_a_used'],1):.1f}, "
             f"B cells {tot['effect_b_cells']/G:.1f})" if spent else ""))
    print(f"   score  pop {100*comp['pop']/sc:2.0f}%  row {100*comp['vrow']/sc:2.0f}%  "
          f"dom {100*comp['dom']/sc:2.0f}%")
    print()

print("3 PLAYERS, 14 games, targeted fortification\n")
show("C only  (previous state)", *run(False, False))
show("A + B + C  (all three live)", *run(True, True))
