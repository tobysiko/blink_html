# -*- coding: utf-8 -*-
"""Why does a v0.21 game end? Gold in, gold out, and the market clock.

The port threw up one result big enough to need its own check: in v0.21 every
game ends because a suit's advanced deck ran dry, not because anyone placed
their twentieth unit. This measures the chain that would explain it —
cards cashed -> gold -> upgrades -> the market drains.

Run: python3 econ_check.py [games]
"""
import sys, statistics, pathlib, importlib.util
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def measure(E, n, games, cap=80):
    out = Counter()
    rounds, upg, gold_in, cashed, ends = [], [], [], [], Counter()
    for s in range(games):
        g = E.Game(n, seed=s, bot=E.smart_bot)
        g.smart = True
        while not g.finished() and g.round < cap:
            g.play_round()
        st = g.stats
        rounds.append(g.round)
        upg.append(st.get("upgrades", 0))
        played = max(1, st.get("cards_played", 0))
        cashed.append(100 * st.get("cards_to_gold", 0) / played)
        gi = sum(v for k, v in st.items() if k.startswith("gold_in"))
        gold_in.append(gi)
        ends[g.ended_on[0] if g.ended_on else "never triggered"] += 1
    m = statistics.mean
    return dict(rounds=m(rounds), upgrades=m(upg), gold_in=m(gold_in),
                cashed=m(cashed), ends=ends,
                upg_per_round=m(upg) / max(1e-9, m(rounds)))


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    v21 = load("e21", HERE / "engine.py")
    v20 = load("e20", HERE.parent.parent / "v0.20" / "sim" / "engine.py")

    print(f"smart bots, seeds 0..{games-1}, same seeds both sides\n")
    for n in (2, 3, 4):
        print(f"{n} PLAYERS")
        print(f"  {'':26}{'v0.20':>10}{'v0.21':>10}")
        A, B = measure(v20, n, games), measure(v21, n, games)
        for label, key, fmt in (("rounds", "rounds", "{:.1f}"),
                                ("cards cashed %", "cashed", "{:.0f}%"),
                                ("gold earned", "gold_in", "{:.0f}"),
                                ("upgrades bought", "upgrades", "{:.1f}"),
                                ("upgrades per round", "upg_per_round", "{:.2f}")):
            print(f"  {label:26}{fmt.format(A[key]):>10}{fmt.format(B[key]):>10}")
        for tag, r in (("v0.20", A), ("v0.21", B)):
            top = ", ".join(f"{k} {v}" for k, v in r["ends"].most_common())
            print(f"  ends {tag:20}{top}")
        print()

    print("The advanced deck holds 5 ranks per suit at 2p, 8 at 3p, 10 at 4p.")
    print("A suit runs dry when its whole ladder has been bought.")


if __name__ == "__main__":
    main()
