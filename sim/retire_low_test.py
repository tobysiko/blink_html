# -*- coding: utf-8 -*-
"""How do you get players to retire their WEAK cards first?

Today they do the opposite. The row scores its third-highest rank, so the best
card you hold is the best thing to retire — and since your best card is usually
the one you just bought, the market gets laundered into the victory row instead
of feeding your melds.

Four candidate rules, measured on the thing that actually matters: **the rank
of the cards that end up in the row**, and whether purchases stop being dumped.

  centre      what the game does now: 1/card + third-highest rank
  highest     1/card + your single best rank. A low card cannot lower the max,
              so retiring one is pure profit and the row fills bottom-up.
  count       1/card and nothing else. Rank stops mattering at all.
  ascending   scoring unchanged, but each retirement must OUTRANK the last, so
              the row is built from the bottom up by construction.
  under cap   scoring unchanged, but you may only retire at or below your
              tier's rank cap — the printed number, reused as "outgrown".

A note on the bot. `_pick_retire` normally carries a fixed bias toward high
rank (RETIRE_RANK_W), which was tuned for the current scoring and would prejudge
every alternative. These runs set it to zero and let the bot optimise each rule's
ACTUAL scoring function via `_vrow_gain`, so each rule is played on its merits.

    python3 retire_low_test.py [games] [players]
"""
import statistics as st
import sys

import engine as E

RULES = [
    ("centre — as now",      dict()),
    ("highest rank in row",  dict(rule="highest")),
    ("count only, no rank",  dict(rule="count")),
    ("ascending retirement", dict(RETIRE_ASCENDING=True)),
    ("only at/below cap",    dict(RETIRE_UNDER_CAP=True)),
    ("ascending + cap",      dict(RETIRE_ASCENDING=True, RETIRE_UNDER_CAP=True)),
    ("retire your lowest (no choice)", dict(RETIRE_LOWEST_N=1)),
    ("retire one of your lowest 2", dict(RETIRE_LOWEST_N=2)),
    ("retire one of your lowest 3", dict(RETIRE_LOWEST_N=3)),
    ("retire one of your lowest 4", dict(RETIRE_LOWEST_N=4)),
    ("row scores its longest RUN", dict(rule="run")),
]


def run(games, n, rule="centre", **flags):
    E.VROW_RULE = rule
    first, allr, purch_ret, purch_play = [], [], 0, 0
    blocked = 0
    scores, vrows, melds = [], [], []
    for sd in range(games):
        g = E.Game(n, seed=sd, bot=E.pro_bot)
        g.smart = True
        g.pro = set(range(n))
        g.retire_w = {i: 0.0 for i in range(n)}   # let the rule drive the choice
        for k, v in flags.items():
            setattr(g, k, v)
        cls = type(g)
        o_up, o_pl = cls._maybe_upgrade, cls._place
        bought, retired_seq, played_bought = set(), {i: [] for i in range(n)}, set()

        def _up(self, p, _o=o_up):
            nh, vb = len(p.hand), len(p.vrow)
            _o(self, p)
            if len(p.vrow) > vb:
                retired_seq[p.i].append(p.vrow[-1][0])
            if len(p.hand) >= nh and p.hand:
                bought.add(p.hand[-1])
            return None

        def _pl(self, p, cs, _o=o_pl):
            for c in cs:
                if c in bought:
                    played_bought.add(c)
            melds.append(len(cs))
            return _o(self, p, cs)

        cls._maybe_upgrade, cls._place = _up, _pl
        try:
            g._deal()
            while not g.finished() and g.round < 80:
                g.play_round()
        finally:
            cls._maybe_upgrade, cls._place = o_up, o_pl
        blocked += g.stats.get("retire_blocked", 0)
        for i in range(n):
            if retired_seq[i]:
                first.append(retired_seq[i][0])
                allr += retired_seq[i]
        for p in g.P:
            purch_ret += sum(1 for c in p.vrow if c in bought)
        purch_play += len(played_bought)
        sc = g.score()
        scores += [d["total"] for d in sc]
        vrows += [d["vrow"] for d in sc]
    E.VROW_RULE = "centre"
    tot_ret = max(1, len(allr))
    return dict(first=st.mean(first) if first else 0,
                mean=st.mean(allr) if allr else 0,
                purch_share=purch_ret / tot_ret,
                played=purch_play / games,
                meld=st.mean(melds), vrow=st.mean(vrows),
                score=st.mean(scores), blocked=blocked / games)


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    ns = [int(sys.argv[2])] if len(sys.argv) > 2 else [2, 3, 4]
    for n in ns:
        print(f"\n{'='*94}\n{n} PLAYERS  ({games} games)")
        print(f"  {'rule':24}{'1st retired':>12}{'mean rank':>11}"
              f"{'row = bought':>14}{'bought played':>15}{'meld':>7}{'score':>7}")
        for label, cfg in RULES:
            r = run(games, n, **cfg)
            print(f"  {label:24}{r['first']:>12.1f}{r['mean']:>11.1f}"
                  f"{r['purch_share']:>14.0%}{r['played']:>15.1f}"
                  f"{r['meld']:>7.2f}{r['score']:>7.1f}")


if __name__ == "__main__":
    main()
