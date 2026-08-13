import sys, statistics
from collections import Counter
import engine as E
from run import check, conservation

def run(prop, ec, fort, n=3, G=14):
    E.Game.PROPORTIONAL_STARVATION = prop
    E.Game.USE_EFFECT_C = ec
    E.Game.USE_FORTIFY = fort
    tot, L, comp, pops = Counter(), [], Counter(), []
    for s in range(G):
        g = E.Game(n, seed=s, bot=E.smart_bot); g.smart = True
        while not g.finished() and g.round < 80:
            g.play_round()
            if s < 2: check(g, "x"); conservation(g, "x")
        tot += g.stats; L.append(g.round)
        for pl in g.P: tot["held"] += pl.gold
        for d in g.score():
            pops.append(d["pop"])
            for k in ("pop","vrow","dom"): comp[k] += d[k]
    tot["_rounds"] = statistics.median(L)
    tot["_G"] = G
    return tot, comp

def show(label, tot, comp):
    G = tot["_G"]; sc = sum(comp.values())
    inc = (tot['gold_in_lost_trick']+tot['gold_in_unplaceable']+tot['gold_in_other']
           +tot['gold_in_effect_c'])/G
    out = (tot['gold_out_upkeep']+tot['gold_out_upgrade']+tot['gold_out_attack']
           +tot['gold_out_fortify'])/G
    print(f"{label}")
    print(f"   rounds {tot['_rounds']:.0f}   starvation: units returned {tot['starved_back']/G:5.1f}/game")
    print(f"   GOLD in {inc:6.1f}  (effect C {tot['gold_in_effect_c']/G:5.1f})   "
          f"out {out:6.1f}  (upkeep {tot['gold_out_upkeep']/G:4.1f} upgrade {tot['gold_out_upgrade']/G:4.1f} "
          f"attack {tot['gold_out_attack']/G:4.1f} fortify {tot['gold_out_fortify']/G:4.1f})")
    print(f"   UNSPENT at end {tot['held']/G:6.1f}   fortifications {tot['fortified']/G:4.1f} "
          f"(absorbed {tot['absorbed_by_fortification']/G:4.1f} attacks)   effect C used {tot['effect_c_used']/G:4.1f}")
    print(f"   score  pop {100*comp['pop']/sc:2.0f}%  row {100*comp['vrow']/sc:2.0f}%  dom {100*comp['dom']/sc:2.0f}%")
    print()

n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
G = int(sys.argv[2]) if len(sys.argv) > 2 else 14
print(f"{n} PLAYERS, {G} games, smart bots\n")
show("BEFORE  band-cliff starvation, no effects, no fortifying", *run(False, False, False, n, G))
show("AFTER   proportional starvation + effect C + fortifying ", *run(True, True, True, n, G))
