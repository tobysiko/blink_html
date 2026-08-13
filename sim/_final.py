import statistics as st, engine as E
def h2h(seeds,n,timing,policy,**flags):
    wins=0; kills=[]
    for s in range(seeds):
        for seat in range(n):
            g=E.Game(n,seed=11000+s,bot=E.pro_bot); g.smart=True; g.pro=set(range(n))
            g.MOVE_TIMING=timing; g.move_policy={seat:policy}
            for k,v in flags.items(): setattr(g,k,v)
            g._deal()
            while not g.finished() and g.round<80: g.play_round()
            sc=g.score(); best=max(sc,key=lambda d:(d["total"],d["gold"]))
            wins+=int(best["seat"]==seat)
            kills.append(g.stats.get("killed_by_attack",0))
    games=seeds*n
    return wins/games, 1.96*((1/n)*(1-1/n)/games)**0.5, st.mean(kills)
for n in (3,4):
    print(f"\n{n} PLAYERS — one seat's movement policy, 240 games (chance {1/n:.1%})")
    for lab,t,pol,fl in (
        ("CONTROL: defensive, moves after","after","threat",{}),
        ("strike, but moves AFTER (no reach)","after","strike",{}),
        ("strike, moves BEFORE","before","strike",{}),
        ("strike, moves BEFORE + open sea","before","strike",dict(OCEAN_PASS_OWN=True))):
        sh,ci,k = h2h(int(240/n),n,t,pol,**fl)
        v = "BEATS pro_bot" if sh>1/n+ci else "loses" if sh<1/n-ci else "no measurable difference"
        print(f"  {lab:38} wins {sh:>6.1%} +/-{ci:.1%}  table kills {k:>5.1f}   {v}")
