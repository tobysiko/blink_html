# -*- coding: utf-8 -*-
"""Feasibility check for the map-objective deck against v0.20 rules.

Objectives are scored on the FINAL map of a real simulated game, counting only
tiles the player occupies. Each function returns how many times that objective
scores for that player.
"""
import itertools
from collections import Counter
import engine as E
from engine import nbrs, adjacent

DIR_LINE = [("E", "W"), ("NE", "SW"), ("NW", "SE")]


def line_of(m, cells, n, pred):
    """Straight lines of length n, all satisfying pred, distinct tiles."""
    from engine import step
    found, used = 0, set()
    for start in sorted(cells):
        for d, _ in DIR_LINE:
            run, c = [], start
            while c in cells and pred(c) and len(run) < n:
                run.append(c); c = step(c, d)
            if len(run) >= n:
                seg = tuple(run[:n])
                if not (set(seg) & used):
                    used |= set(seg); found += 1
    return found


def clusters_of(m, cells, n, pred):
    """Groups of n mutually adjacent tiles satisfying pred, distinct tiles."""
    pool = [c for c in cells if pred(c)]
    used, found = set(), 0
    for combo in itertools.combinations(sorted(pool), n):
        if set(combo) & used:
            continue
        if all(b in nbrs(*a) for a, b in itertools.combinations(combo, 2)):
            used |= set(combo); found += 1
    return found


def connected_of(m, cells, n, pred):
    """Groups of n CONNECTED (not mutually adjacent) tiles satisfying pred."""
    pool = {c for c in cells if pred(c)}
    used, found = set(), 0
    for c in sorted(pool):
        if c in used:
            continue
        comp, stack = set(), [c]
        while stack:
            x = stack.pop()
            if x in comp or x in used:
                continue
            comp.add(x)
            for y in nbrs(*x):
                if y in pool and y not in comp:
                    stack.append(y)
        found += len(comp) // n
        used |= comp
    return found


def score_all(m, mine):
    T = lambda c: m.tiles[c].terrain
    out = {}
    # 1 · Coastal Control - adjacent plains-ocean pairs, each tile in one pair
    used, n = set(), 0
    for c in sorted(mine):
        if c in used or T(c) != "plains":
            continue
        for d in sorted(nbrs(*c)):
            if d in mine and d not in used and T(d) == "ocean":
                used |= {c, d}; n += 1; break
    out["Coastal Control"] = n
    # 2 · Island Nation - your ocean tile adjacent to 4+ other ocean tiles
    out["Island Nation"] = sum(
        1 for c in mine if T(c) == "ocean"
        and sum(1 for d in nbrs(*c) if d in m.tiles and T(d) == "ocean") >= 4)
    # 3 · Breadbasket - three mutually adjacent plains
    out["Breadbasket"] = clusters_of(m, mine, 3, lambda c: T(c) == "plains")
    # 4 · Highland Lake - your ocean tile whose every neighbour is mountain or forest
    def lake(c):
        ns = [d for d in nbrs(*c) if d in m.tiles]
        return T(c) == "ocean" and ns and all(T(d) in ("mountain", "forest") for d in ns)
    out["Highland Lake"] = sum(1 for c in mine if lake(c))
    # 5 · Mountain Fortress - three mutually adjacent mountains
    out["Mountain Fortress"] = clusters_of(m, mine, 3, lambda c: T(c) == "mountain")
    # 6 · Mountain Range - straight line of three mountains
    out["Mountain Range"] = line_of(m, mine, 3, lambda c: T(c) == "mountain")
    # 7 · Greenway - straight line of four alternating forest/plains
    from engine import step
    used, n = set(), 0
    for start in sorted(mine):
        for d, _ in DIR_LINE:
            run, c = [], start
            while c in mine and len(run) < 4:
                run.append(c); c = step(c, d)
            if len(run) == 4 and not (set(run) & used):
                ts = [T(x) for x in run]
                if all(t in ("forest", "plains") for t in ts) and \
                   all(ts[i] != ts[i+1] for i in range(3)):
                    used |= set(run); n += 1
    out["Greenway"] = n
    # 8 · Trade Delta - your ocean tile touching plains, forest and mountain
    def delta(c):
        ns = {T(d) for d in nbrs(*c) if d in m.tiles}
        return T(c) == "ocean" and {"plains", "forest", "mountain"} <= ns
    out["Trade Delta"] = sum(1 for c in mine if delta(c))
    # 9 · Rainforest - four connected forest tiles
    out["Rainforest"] = connected_of(m, mine, 4, lambda c: T(c) == "forest")
    # 10 · Silk Road - straight line of four plains
    out["Silk Road"] = line_of(m, mine, 4, lambda c: T(c) == "plains")
    # 11 · Ocean Corridor - straight line of four oceans
    out["Ocean Corridor"] = line_of(m, mine, 4, lambda c: T(c) == "ocean")
    # 12 · River Flow - chain mountain->forest->plains->ocean, source may repeat
    n, usedFPO = 0, set()
    for a in sorted(mine):
        if T(a) != "mountain": continue
        for b in sorted(nbrs(*a) & mine):
            if T(b) != "forest" or b in usedFPO: continue
            for c in sorted(nbrs(*b) & mine):
                if T(c) != "plains" or c in usedFPO: continue
                for d in sorted(nbrs(*c) & mine):
                    if T(d) == "ocean" and d not in usedFPO:
                        usedFPO |= {b, c, d}; n += 1; break
                else: continue
                break
    out["River Flow"] = n
    return out


POINTS = {"Coastal Control":1, "Island Nation":1, "Breadbasket":2, "Highland Lake":2,
          "Mountain Fortress":3, "Mountain Range":3, "Greenway":3, "Trade Delta":3,
          "Rainforest":4, "Silk Road":4, "Ocean Corridor":4, "River Flow":4}

if __name__ == "__main__":
    hits, pts, games, players = Counter(), Counter(), 0, 0
    tilecount = []
    for s in range(30):
        g = E.Game(3, seed=s, bot=E.smart_bot); g.smart = True
        while not g.finished() and g.round < 80:
            g.play_round()
        games += 1
        tilecount.append(len(g.m.tiles))
        for p in g.P:
            players += 1
            mine = {c for c, t in g.m.tiles.items() if t.owner == p.i}
            for k, v in score_all(g.m, mine).items():
                if v: hits[k] += 1
                pts[k] += v * POINTS[k]
    print(f"{games} three-player games, {players} player-boards, "
          f"final maps averaging {sum(tilecount)/len(tilecount):.0f} tiles\n")
    print(f"{'objective':20}{'pts':>5}{'scores for':>12}{'mean pts':>10}{'verdict':>26}")
    for k in POINTS:
        rate = 100*hits[k]/players
        mean = pts[k]/players
        if rate == 0:      v = "UNREACHABLE"
        elif rate < 8:     v = "very rare"
        elif rate > 75:    v = "near-automatic"
        elif rate > 50:    v = "common"
        else:              v = "ok"
        print(f"{k:20}{POINTS[k]:>5}{rate:>11.0f}%{mean:>10.2f}{v:>26}")
