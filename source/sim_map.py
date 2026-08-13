# -*- coding: utf-8 -*-
"""Blink v0.20 — map simulator.

blink_sim.py models the v0.12 design (per-terrain unit tracks, scaling
population limits, defence bonuses) and cannot answer questions about the
current rules. This is a separate, deliberately narrow model of the *map*
only, written to test the four things v0.20 asserts without evidence:

  1. does "a new tile must touch at least two" keep maps compact, or do
     two-wide ribbons appear in practice?
  2. is a 15/15/15/15 tile mix enough - how often does an explore fail for
     want of a matching suit?
  3. do the new starting maps actually delay first contact?
  4. what can each suit actually DO on turn one - settle, explore, or nothing?
     (An earlier version of this file measured settling only and wrongly
     reported a Plains bias. Exploring is open to every suit.)

Simplifications, all conservative: bots play random legal melds, never
attack, never fortify, never upgrade, and always prefer to expand. That
biases *towards* sprawl, so the compactness numbers are a worst case.
"""
import random, itertools, statistics
from collections import Counter

TER = ["plains", "forest", "ocean", "mountain"]
BAG_EACH = 15
HOLDS = {"plains": 3, "forest": 2, "ocean": 1, "mountain": 1}

STARTS = {
    2: ([(1, 0), (2, 0)], [(0, 0), (3, 0)]),
    3: ([(1, 3), (2, 2), (2, 3)], [(0, 3), (2, 1), (3, 4)]),
    4: ([(1, 2), (2, 2), (2, 3), (3, 3)], [(0, 2), (2, 1), (2, 4), (4, 3)]),
}


def nbrs(c, r):
    if r % 2 == 0:
        return {(c-1, r), (c+1, r), (c-1, r-1), (c, r-1), (c-1, r+1), (c, r+1)}
    return {(c-1, r), (c+1, r), (c, r-1), (c+1, r-1), (c, r+1), (c+1, r+1)}


def cube(c, r):
    q = c - (r - (r & 1)) // 2
    return (q, -q - r, r)


def hexdist(a, b):
    A, B = cube(*a), cube(*b)
    return max(abs(A[i] - B[i]) for i in range(3))


class Map:
    def __init__(self, n):
        mts, pls = STARTS[n]
        self.terr = {c: "mountain" for c in mts}
        self.terr.update({c: "plains" for c in pls})
        self.stack = {c: [] for c in self.terr}      # list of owner ids on each tile
        self.starts = list(pls)
        for i, c in enumerate(pls):
            self.stack[c] = [i]
        bag = [t for t in TER for _ in range(BAG_EACH)]
        for c in self.terr.values():
            bag.remove(c)
        random.shuffle(bag)
        self.bag = bag
        self.market = [self.bag.pop() for _ in range(min(2 * n, len(self.bag)))]

    def legal_explore_spaces(self):
        """Empty spaces touching at least two existing tiles."""
        cand = set()
        for c in self.terr:
            cand |= nbrs(*c)
        return {s for s in cand - set(self.terr) if len(nbrs(*s) & set(self.terr)) >= 2}

    def take_tile(self, suit):
        """Market first, then dig the bag. Returns True if a tile was found."""
        if suit in self.market:
            self.market.remove(suit)
            if self.bag:
                self.market.append(self.bag.pop())
            return True
        dug = []
        while self.bag:
            t = self.bag.pop()
            if t == suit:
                self.market.extend(dug)
                return True
            dug.append(t)
        self.market.extend(dug)
        return False

    def mean_neighbours(self):
        return statistics.mean(len(nbrs(*c) & set(self.terr)) for c in self.terr)

    def can_hold(self, c, p):
        """Room for another of p's units? Tiles are single-owner while occupied."""
        st = self.stack[c]
        if st and st[0] != p:
            return False
        return len(st) < HOLDS[self.terr[c]]


def run(n=3, rounds=12, seed=0):
    random.seed(seed)
    m = Map(n)
    civ = {i: {c} for i, c in enumerate(m.starts)}
    explore_fail = 0
    explore_try = 0
    contact_round = None

    for rnd in range(1, rounds + 1):
        limit = 2 if rnd <= 3 else 3
        for p in range(n):
            mine = civ[p]
            frontier = set(mine)
            for c in mine:
                frontier |= nbrs(*c)
            for _ in range(limit):
                suit = random.choice(TER)
                targets = [s for s in frontier if s in m.terr
                           and m.terr[s] == suit and m.can_hold(s, p)]
                if targets:
                    c = random.choice(targets)
                    m.stack[c].append(p)
                    mine.add(c)
                    continue
                spaces = m.legal_explore_spaces() & frontier
                if spaces:
                    explore_try += 1
                    if m.take_tile(suit):
                        c = random.choice(sorted(spaces))
                        m.terr[c] = suit
                        m.stack[c] = []
                    else:
                        explore_fail += 1
            civ[p] = mine
        if contact_round is None:
            for a, b in itertools.permutations(range(n), 2):
                tgt = m.starts[b]
                if any(hexdist(x, tgt) <= limit for x in civ[a]):
                    contact_round = rnd
                    break
    return dict(tiles=len(m.terr), mean_nbrs=m.mean_neighbours(),
                explore_fail=explore_fail,
                explore_try=explore_try, contact=contact_round,
                bag_left=len(m.bag))


if __name__ == "__main__":
    for n in (2, 3, 4):
        res = [run(n, seed=s) for s in range(120)]
        mn = statistics.mean(r["mean_nbrs"] for r in res)
        tf = sum(r["explore_fail"] for r in res)
        tt = sum(r["explore_try"] for r in res)
        ct = [r["contact"] for r in res if r["contact"]]
        bl = statistics.mean(r["bag_left"] for r in res)
        tl = statistics.mean(r["tiles"] for r in res)
        print(f"\n{n} players  ({len(res)} games, 12 rounds)")
        print(f"  final map           {tl:5.1f} tiles, {bl:4.1f} left in bag")
        print(f"  mean neighbours     {mn:5.2f}  (2.0 = one-wide ribbon, "
              f"3.0 = two-wide, 4.5+ = blob)")
        print(f"  explore failures    {tf:5d} of {tt} attempts "
              f"({100*tf/max(tt,1):.1f}% - no tile of that suit anywhere)")
        print(f"  rival start first reachable: round {statistics.median(ct):.0f} median"
              if ct else "  rival start never reachable")
    print("\n" + "="*66)
    print("TURN ONE - what can a card of each suit actually do?")
    print("Settling puts a UNIT on the map: population, band progress, ground.")
    print("Exploring puts a TILE on the map: no unit, no progress, no score -")
    print("but it is how the terrain your later cards need comes into being.")
    print("="*66)
    t1 = Counter()
    for n in (2, 3, 4):
        for sd in range(400):
            random.seed(sd)
            m = Map(n)
            for p, start in enumerate(m.starts):
                frontier = {start} | nbrs(*start)
                spaces = m.legal_explore_spaces() & frontier
                for suit in TER:
                    settle = any(c in m.terr and m.terr[c] == suit and m.can_hold(c, p)
                                 for c in frontier)
                    explore = bool(spaces) and (suit in m.market or suit in m.bag)
                    t1[(suit, "settle")] += settle
                    t1[(suit, "explore")] += explore
                    t1[(suit, "dead")] += (not settle and not explore)
                    t1[("n", suit)] += 1
                t1["spaces"] += len(spaces)
                t1["players"] += 1
    print(f"\n  {'suit':10}{'can settle':>12}{'can explore':>13}{'dead':>8}")
    for suit in TER:
        N = t1[("n", suit)]
        print(f"  {suit:10}{100*t1[(suit,'settle')]/N:11.0f}%"
              f"{100*t1[(suit,'explore')]/N:12.0f}%{100*t1[(suit,'dead')]/N:7.0f}%")
    print(f"\n  legal explore spaces next to a start: "
          f"{t1['spaces']/t1['players']:.2f} on average")
    print("\n  No suit is dead on turn one. The asymmetry is not playability -")
    print("  it is what you get: a unit that scores and advances your board, or")
    print("  a tile that scores nothing and can be settled by a neighbour too.")
