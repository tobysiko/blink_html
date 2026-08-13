# -*- coding: utf-8 -*-
"""v0.20 vs v0.21: the same seeds through both engines, smart bots.

Run from either sim folder:  python3 port_check.py [games]

Loads the OTHER version's engine by path, so the two rule sets are compared
directly rather than by quoting numbers from different runs. Any metric that
depends on meld shape is deliberately absent — in v0.21 a meld shape has no
consequence on the map, so the comparison is about tempo and economy.
"""
import sys, statistics, pathlib, importlib.util
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
OTHER = {"v0.20": "v0.21", "v0.21": "v0.20"}[HERE.parent.name]
OTHER_ENGINE = HERE.parent.parent / OTHER / "sim" / "engine.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def play(E, n, seed, cap=80):
    g = E.Game(n, seed=seed, bot=E.smart_bot)
    g.smart = True
    while not g.finished() and g.round < cap:
        g.play_round()
    return g


def measure(E, n, games):
    rounds, scores, spread, pop, row, dom = [], [], [], [], [], []
    cashed, settled, explored, attacked, moves = [], [], [], [], []
    for s in range(games):
        g = play(E, n, s)
        rounds.append(g.round)
        sc = g.score()
        tot = sorted(d["total"] for d in sc)
        scores.append(statistics.mean(tot))
        spread.append(tot[-1] - tot[0])
        pop.append(statistics.mean(d["pop"] for d in sc))
        row.append(statistics.mean(d["vrow"] for d in sc))
        dom.append(statistics.mean(d["dom"] for d in sc))
        st = g.stats
        played = max(1, st.get("cards_played", 0))
        cashed.append(100 * st.get("cards_to_gold", 0) / played)
        settled.append(st.get("settle", 0))
        explored.append(st.get("explore", 0))
        attacked.append(st.get("killed_by_attack", 0))
        moves.append(st.get("free_move", 0) + st.get("shifted", 0)
                     + st.get("drifted", 0))
    m = statistics.mean
    return dict(rounds=m(rounds), score=m(scores), spread=m(spread),
                pop=m(pop), row=m(row), dom=m(dom), cashed=m(cashed),
                settle=m(settled), explore=m(explored), attack=m(attacked),
                moves=m(moves))


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    mine = load("engine_here", HERE / "engine.py")
    theirs = load("engine_other", OTHER_ENGINE)
    a_name, b_name = HERE.parent.name, OTHER
    if a_name > b_name:                      # always print older version first
        mine, theirs = theirs, mine
        a_name, b_name = b_name, a_name

    print(f"{a_name} vs {b_name} — smart bots, seeds 0..{games-1}, same seeds both sides\n")
    rows = [("rounds per game", "rounds", "{:.1f}"),
            ("mean final score", "score", "{:.1f}"),
            ("score spread (top-bottom)", "spread", "{:.1f}"),
            ("  from population", "pop", "{:.1f}"),
            ("  from victory row", "row", "{:.1f}"),
            ("  from dominance", "dom", "{:.1f}"),
            ("cards cashed for gold %", "cashed", "{:.0f}%"),
            ("units settled per game", "settle", "{:.1f}"),
            ("tiles explored per game", "explore", "{:.1f}"),
            ("units killed per game", "attack", "{:.1f}"),
            ("unit moves per game", "moves", "{:.1f}")]
    for n in (2, 3, 4):
        A, B = measure(mine, n, games), measure(theirs, n, games)
        print(f"{n} PLAYERS")
        print(f"  {'':28}{a_name:>10}{b_name:>10}{'change':>12}")
        for label, key, fmt in rows:
            a, b = A[key], B[key]
            d = "" if not a else f"{100*(b-a)/a:+.0f}%"
            print(f"  {label:28}{fmt.format(a):>10}{fmt.format(b):>10}{d:>12}")
        print()


if __name__ == "__main__":
    main()
