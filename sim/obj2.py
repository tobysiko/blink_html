# -*- coding: utf-8 -*-
"""Candidate three-tile objective set. Every pattern is exactly three tiles
the player OCCUPIES, so all sit inside the ~7-tile explore budget."""
import itertools
from engine import nbrs

def _chain(m, mine, seq):
    """Three occupied tiles a-b-c, adjacent in order, terrains matching seq."""
    T = lambda c: m.tiles[c].terrain
    for a in mine:
        if T(a) != seq[0]: continue
        for b in nbrs(*a) & mine:
            if T(b) != seq[1]: continue
            for c in (nbrs(*b) & mine) - {a}:
                if T(c) == seq[2]:
                    return 1
    return 0

def _line_seq(m, mine, seq):
    """Three occupied tiles in a STRAIGHT line, terrains matching seq in order."""
    from engine import step
    T = lambda c: m.tiles[c].terrain
    for a in mine:
        if T(a) != seq[0]: continue
        for d in ("E", "W", "NE", "NW", "SE", "SW"):
            b, c = step(a, d), step(step(a, d), d)
            if b in mine and c in mine and T(b) == seq[1] and T(c) == seq[2]:
                return 1
    return 0


def _connected3(m, mine, terrain):
    """Three tiles of one terrain you occupy, connected in ANY arrangement."""
    pool = {c for c in mine if m.tiles[c].terrain == terrain}
    seen = set()
    for c in pool:
        if c in seen: continue
        comp, stack = set(), [c]
        while stack:
            x = stack.pop()
            if x in comp: continue
            comp.add(x); seen.add(x)
            for y in nbrs(*x):
                if y in pool and y not in comp: stack.append(y)
        if len(comp) >= 3: return 1
    return 0


def _hub(m, mine, centre, arm, touching):
    """A centre tile with two arm-terrain neighbours you also occupy.
    touching=True  -> the two arms must touch each other (a triangle)
    touching=False -> the two arms must NOT touch (the centre separates them)"""
    import itertools as _it
    T = lambda c: m.tiles[c].terrain
    for c in mine:
        if T(c) != centre: continue
        arms = [d for d in nbrs(*c) & mine if T(d) == arm]
        for a, b in _it.combinations(arms, 2):
            if (b in nbrs(*a)) == touching:
                return 1
    return 0


def _view(m, mine, centre, arm, touching=None, own_arms=False):
    """A centre tile YOU occupy, with two arm-terrain neighbours. The arms need
    not be yours unless own_arms. touching: True/False/None (do not care)."""
    import itertools as _it
    T = lambda c: m.tiles[c].terrain
    for c in mine:
        if T(c) != centre: continue
        pool = [d for d in nbrs(*c) if d in m.tiles and T(d) == arm
                and (not own_arms or d in mine)]
        for a, b in _it.combinations(pool, 2):
            if touching is None or (b in nbrs(*a)) == touching:
                return 1
    return 0


def _triangle(m, mine, pred):
    T = lambda c: m.tiles[c].terrain
    for combo in itertools.combinations(sorted(mine), 3):
        if all(b in nbrs(*a) for a, b in itertools.combinations(combo, 2)) \
           and pred([T(x) for x in combo]):
            return 1
    return 0

def _line3(m, mine, terrain):
    from engine import step
    T = lambda c: m.tiles[c].terrain
    for a in mine:
        if T(a) != terrain: continue
        for d in ("E", "NE", "SE"):
            b, c = step(a, d), step(step(a, d), d)
            if b in mine and c in mine and T(b) == terrain and T(c) == terrain:
                return 1
    return 0

CANDIDATES = {
    "Lookout-open": (lambda m, s: _view(m, s, "mountain", "ocean", touching=True),
                     ("mountain", "ocean")),
    "chain-OMO":    (lambda m, s: _chain(m, s, ("ocean", "mountain", "ocean")),
                     ("mountain", "ocean")),
    "chain-MFP":    (lambda m, s: _chain(m, s, ("mountain", "forest", "plains")),
                     ("mountain", "forest", "plains")),
    "chain-MPO":    (lambda m, s: _chain(m, s, ("mountain", "plains", "ocean")),
                     ("mountain", "plains", "ocean")),
}

def frontier(m, mine, seat):
    """Three of your tiles, each touching a tile a rival occupies."""
    n = 0
    for c in mine:
        if any(m.tiles[d].owner not in (None, seat)
               for d in nbrs(*c) if d in m.tiles):
            n += 1
    return 1 if n >= 3 else 0
