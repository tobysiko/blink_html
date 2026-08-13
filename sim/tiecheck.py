# -*- coding: utf-8 -*-
"""How often would lexicographic tiebreaking actually fire?

A tie only matters if it decides the TRICK, so this measures the contention
group at the top of the ranking, not any two players who happen to match.

The engine's ordering key is
    (-effective_size, -wins_ties, -spent_a, -top_rank, seat)
so a tie that reaches the seat term is one currently settled by play order.
That is exactly the population a lexicographic rule would take over.

  python3 tiecheck.py [games] [players]
"""
import sys, random
from collections import Counter
import engine as E
from engine import meld_cards, meld_size

GAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 40
NP = int(sys.argv[2]) if len(sys.argv) > 2 else 3

st = Counter()


def on_trick(g, order, key, winner):
    st["tricks"] += 1
    rows = []
    for seat, i in enumerate(order):
        p = g.P[i]
        ranks = sorted((c[0] for c in meld_cards(p.kind, p.played)), reverse=True)
        rows.append((key((seat, i))[:4], ranks, p.kind))

    # any two melds anywhere with the same size and same top card
    seen = Counter((len(r), r[0]) for _, r, _ in rows)
    if any(v > 1 for v in seen.values()):
        st["raw_match_any"] += 1

    # the group that actually decides the trick
    best = min(k for k, _, _ in rows)
    group = [(r, kd) for k, r, kd in rows if k == best]
    if len(group) < 2:
        return
    st["decisive_tie"] += 1
    st[f"tie_of_{len(group)}"] += 1
    st[f"tie_size_{len(group[0][0])}"] += 1

    # lexicographic comparison down the sorted-descending rank lists
    kinds = tuple(sorted({kd for _, kd in group}))
    st['shape_' + ('same:' + kinds[0] if len(kinds) == 1 else 'mixed:' + '+'.join(kinds))] += 1
    lists = [r for r, _ in group]
    n = len(lists[0])
    depth = None
    for pos in range(1, n):                     # position 0 is the top card,
        vals = {r[pos] for r in lists}          # already equal by construction
        if len(vals) > 1:
            depth = pos + 1                     # 1-based: 2 = second card
            break
    if depth is None:
        st["equal_all_way"] += 1
        st['eqshape_' + ('same:' + kinds[0] if len(kinds) == 1 else 'mixed:' + '+'.join(kinds))] += 1
        st[f"equal_len_{n}"] += 1
    else:
        st["broken"] += 1
        st[f"broken_at_{depth}"] += 1


for gi in range(GAMES):
    g = E.Game(NP, seed=4200 + gi, bot=E.smart_bot)
    g.smart = True
    g.on_trick = on_trick
    while not g.finished() and g.round < 80:
        g.play_round()

t, T = st["tricks"], GAMES
print(f"\n{NP} players, {GAMES} games, {t} tricks ({t/T:.1f} per game)\n")
print(f"  melds anywhere sharing size + top rank   {st['raw_match_any']:5d}"
      f"   {st['raw_match_any']/t*100:5.1f}% of tricks   {st['raw_match_any']/T:5.2f}/game")
print(f"  ties that DECIDE the trick               {st['decisive_tie']:5d}"
      f"   {st['decisive_tie']/t*100:5.1f}% of tricks   {st['decisive_tie']/T:5.2f}/game")
d = st["decisive_tie"]
if not d:
    print("\n  no decisive ties"); raise SystemExit
print(f"\n  of those {d} decisive ties:")
print(f"    broken by a later card                 {st['broken']:5d}   {st['broken']/d*100:5.1f}%")
for k in sorted(x for x in st if x.startswith("broken_at_")):
    print(f"      first differ at card {k.split('_')[-1]}              "
          f"{st[k]:5d}   {st[k]/d*100:5.1f}%")
print(f"    equal all the way down                 {st['equal_all_way']:5d}"
      f"   {st['equal_all_way']/d*100:5.1f}%")
for k in sorted(x for x in st if x.startswith("equal_len_")):
    print(f"      both melds were {k.split('_')[-1]} card(s)          "
          f"{st[k]:5d}   {st[k]/d*100:5.1f}%")
print("\n  meld size when a decisive tie happens:")
for k in sorted(x for x in st if x.startswith("tie_size_")):
    print(f"    {k.split('_')[-1]} card melds                          "
          f"{st[k]:5d}   {st[k]/d*100:5.1f}%")
print("\n  shapes involved in a decisive tie (equal-all-way in brackets):")
for k in sorted(x for x in st if x.startswith("shape_")):
    nm = k[6:]; eq = st.get("eqshape_" + nm, 0)
    print(f"    {nm:26s} {st[k]:5d}   {st[k]/d*100:5.1f}%   [{eq} equal]")
print("\n  how many players were tied:")
for k in sorted(x for x in st if x.startswith("tie_of_")):
    print(f"    {k.split('_')[-1]} players                             "
          f"{st[k]:5d}   {st[k]/d*100:5.1f}%")
