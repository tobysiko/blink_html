# -*- coding: utf-8 -*-
"""Run Blink v0.22 games with random-legal bots and assert the rules hold."""
import sys, statistics
from collections import Counter
import engine as E


def check(g, where):
    m = g.m
    for p in g.P:
        # v0.22: the playing deck is topped back up to ten from the SHARED
        # pile, so it can sit BELOW ten while the pile is dry — but never above.
        tot = len(p.hand) + len(p.discard) + len(p.played)
        assert tot <= 10, f"{where}: seat {p.i} holds {tot} cards, more than 10"
        # unit conservation: 20 units, on the board or in the reserve
        on_map = sum(tl.units.count(p.i) for tl in m.tiles.values())
        assert sum(p.reserve) + on_map == 20, \
            f"{where}: seat {p.i} has {sum(p.reserve)}+{on_map} units"
        assert len(p.vrow) <= 5, f"{where}: victory row over five"
    # v0.22: every meld on the table must satisfy the one meld rule
    for p in g.P:
        if p.played:
            assert E.is_legal_meld(list(p.played)), \
                f"{where}: seat {p.i} played an illegal meld {p.played}"
    m.check_graph()          # links symmetric, no double owners, no stray gold
    tiles = set(m.tiles)
    seen = {next(iter(tiles))}
    stk = [next(iter(tiles))]
    while stk:
        x = stk.pop()
        for y in E.nbrs(*x) & tiles - seen:
            seen.add(y); stk.append(y)
    assert seen == tiles, f"{where}: map is not connected"
    start = set(E.STARTS[g.n][0]) | set(E.STARTS[g.n][1])
    for c in tiles - start:
        assert len(E.nbrs(*c) & tiles) >= 2, f"{where}: {c} touches fewer than two"


def conservation(g, where):
    """Every physical component must be somewhere. Nothing created, nothing lost."""
    # --- TILES: 60, in the bag, the market, or on the map
    tiles = (Counter(g.m.supply)
             + Counter(t.terrain for t in g.m.tiles.values()))
    for t in E.TER:
        assert tiles[t] == E.BAG_EACH, \
            f"{where}: {t} tiles = {tiles[t]}, should be {E.BAG_EACH}"
    assert sum(tiles.values()) == 60, f"{where}: {sum(tiles.values())} tiles, not 60"

    # --- CARDS: every card must be somewhere. v0.22 adds the shared pile,
    # the single upgrade deck and the face-up market grid (stacks).
    seen = Counter()
    for p in g.P:
        for c in list(p.hand) + list(p.discard) + list(p.played) + list(p.vrow):
            seen[c] += 1
    for c in g.removed:              # spent on an effect: out of the game, still real
        seen[c] += 1
    for c in g.pile:                 # shared discard pile
        seen[c] += 1
    for c in g.deck:                 # face-down upgrade deck
        seen[c] += 1
    for stack in g.grid:             # face-up market, each position a stack
        for c in stack:
            seen[c] += 1
    dupes = {c: k for c, k in seen.items() if k > 1}
    assert not dupes, f"{where}: duplicated cards {list(dupes)[:4]}"
    assert sum(seen.values()) == g.card_total, \
        f"{where}: {sum(seen.values())} cards in play, started with {g.card_total}"


def play(n, seed, cap=80):
    g = E.Game(n, seed=seed)
    check(g, "setup")
    conservation(g, "setup")
    while not g.finished() and g.round < cap:
        g.play_round()
        check(g, f"round {g.round}")
        conservation(g, f"round {g.round}")
    return g


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    for n in (2, 3, 4):
        L, bands, comp, tiles, ret, trig, capped = [], Counter(), Counter(), [], [], Counter(), 0
        wins = Counter()
        for s in range(N):
            g = play(n, s)
            if not g.finished():
                capped += 1
            L.append(g.round)
            tiles.append(len(g.m.terr))
            trig[g.ended_on[0] if g.ended_on else "never triggered"] += 1
            sc = g.score()
            best = max(sc, key=lambda d: (d["total"], d["gold"]))
            wins[best["seat"]] += 1
            for d in sc:
                bands[d["band"]] += 1
                comp["pop"] += d["pop"]; comp["vrow"] += d["vrow"]; comp["dom"] += d["dom"]
            for p in g.P:
                ret.append(sum(p.reserve))
        tot = comp["pop"] + comp["vrow"] + comp["dom"]
        print(f"\n{n} PLAYERS   ({N} games, random-legal bots)")
        print(f"  game length        {statistics.mean(L):5.1f} rounds "
              f"(median {statistics.median(L):.0f}, max {max(L)})"
              + (f"   [{capped} hit the {80}-round cap]" if capped else ""))
        print(f"  end trigger        " + ", ".join(f"{k}: {v}" for k, v in trig.most_common()))
        print(f"  final map          {statistics.mean(tiles):5.1f} tiles of 60")
        print(f"  band reached       " + ", ".join(f"{k} {100*v/(N*n):.0f}%"
              for k, v in bands.most_common()))
        print(f"  score comes from   population {100*comp['pop']/tot:.0f}%, "
              f"victory row {100*comp['vrow']/tot:.0f}%, dominance {100*comp['dom']/tot:.0f}%")
        print(f"  seat win share     " + ", ".join(f"seat {k} {100*v/N:.0f}%"
              for k, v in sorted(wins.items())))
