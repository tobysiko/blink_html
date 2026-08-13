# -*- coding: utf-8 -*-
"""Objective completion rates under v0.21, for the twelve cards that ship.

The objective SCORER is engine-independent — it reads a finished map and asks
whether three tiles you occupy form the required chain. So the shipped deck can
be measured under the new rules even though the seeking bots were never ported.

These are PASSIVE rates: nobody is trying. A player who wants the objective will
beat them, so read a passive rate as the floor.

Run: python3 obj_v21.py [games] [players]
"""
import sys, math, pathlib, importlib.util
import engine as E
from obj2 import _chain

HERE = pathlib.Path(__file__).resolve().parent

# the twelve chains that ship, keyed exactly as build_module.py's DECK
DECK = [
    ("Foothills",        ("mountain", "forest", "plains")),
    ("Watershed",        ("mountain", "plains", "ocean")),
    ("Highland Rivers",  ("mountain", "forest", "ocean")),
    ("Fjord",            ("mountain", "ocean", "mountain")),
    ("Mountain Pass",    ("plains", "mountain", "plains")),
    ("Coastal Chain",    ("plains", "ocean", "plains")),
    ("Clearing",         ("forest", "plains", "forest")),
    ("Mountain Lookout", ("ocean", "mountain", "ocean")),
    ("Riverbank",        ("plains", "forest", "ocean")),
    ("Timberline",       ("forest", "mountain", "forest")),
    ("River Delta",      ("ocean", "plains", "forest")),
    ("Sheltered Water",  ("forest", "ocean", "forest")),
]


def load_other():
    p = HERE.parent.parent / "v0.20" / "sim" / "engine.py"
    spec = importlib.util.spec_from_file_location("e20", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["e20"] = mod
    spec.loader.exec_module(mod)
    return mod


def rates(Eng, games, n, cap=80):
    hits = {name: 0 for name, _ in DECK}
    samples = 0
    tiles = 0
    for s in range(games):
        g = Eng.Game(n, seed=9000 + s, bot=Eng.smart_bot)
        g.smart = True
        while not g.finished() and g.round < cap:
            g.play_round()
        tiles += len(g.m.terr)
        for p in g.P:
            mine = {c for c, t in g.m.tiles.items() if t.owner == p.i}
            samples += 1
            for name, seq in DECK:
                hits[name] += _chain(g.m, mine, seq)
    return hits, samples, tiles / games


def ci(k, s):
    r = k / s
    se = math.sqrt(r * (1 - r) / s) * 1.96
    return r * 100, max(0.0, r - se) * 100, min(1.0, r + se) * 100


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    new, s_new, t_new = rates(E, games, n)
    old, s_old, t_old = rates(load_other(), games, n)

    print(f"Passive objective rates, {n} players, {games} games "
          f"({s_new} player-samples per side)")
    print(f"Map at end: v0.20 {t_old:.0f} tiles, v0.21 {t_new:.0f} tiles\n")
    print(f"  {'objective':18}{'v0.20':>8}{'v0.21':>8}   95% CI (v0.21)")
    for name, _ in DECK:
        a, _, _ = ci(old[name], s_old)
        b, lo, hi = ci(new[name], s_new)
        print(f"  {name:18}{a:>7.0f}%{b:>7.0f}%   [{lo:.0f}-{hi:.0f}]")
    ma = sum(old.values()) / (s_old * len(DECK)) * 100
    mb = sum(new.values()) / (s_new * len(DECK)) * 100
    print(f"\n  {'mean':18}{ma:>7.0f}%{mb:>7.0f}%")
    print("\nPassive = nobody is trying. A player chasing one beats these.")


if __name__ == "__main__":
    main()
