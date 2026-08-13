# -*- coding: utf-8 -*-
"""Is playing for melds all game a losing strategy?

`findings-what-upgrades-are-for.md` showed that only about a fifth of bought
cards ever reach the map: the market is a victory-row engine in practice. The
obvious question is whether that is the game telling us something, or just the
house bot being lazy. So: give ONE seat a committed meld-building strategy,
leave the other seats on `pro_bot`, rotate the seats, and count wins.

The meld-first player differs in three ways:

  greed      how much the hand you KEEP is worth when choosing a meld. pro_bot
             values it at 0.30; the meld player hoards run material instead of
             spending it, which is what "building toward a bigger meld" means.
  retire     pro_bot retires its highest card, which is usually the one it just
             bought. The meld player retires whatever costs its future melds
             least, whatever the rank — so purchases stay in the deck.
  cash       pro_bot converts a card to a coin whenever the map is worth less
             than CASH_THRESHOLD. The meld player holds on for longer.

    python3 meld_bot_test.py [seeds] [players]
"""
import statistics as st
import sys

import engine as E


def play(n, seed, seat, **policy):
    g = E.Game(n, seed=seed, bot=E.pro_bot)
    g.smart = True
    g.pro = set(range(n))
    if seat is not None:
        if "greed" in policy:
            g.greed[seat] = policy["greed"]
        if "retire_w" in policy:
            # "retire by meld damage" means the row is ignored outright, so
            # both row terms go to zero, not just the rank one.
            g.retire_w[seat] = policy["retire_w"]
            g.gain_w[seat] = policy.get("gain_w", policy["retire_w"])
    g._deal()
    if seat is not None and "cash" in policy:
        g.CASH_THRESHOLD = policy["cash"]      # table-wide; used only in sweeps
    while not g.finished() and g.round < 80:
        g.play_round()
    return g


def h2h(seeds, n, **policy):
    """Seats rotated so a result is never a seat effect."""
    wins = 0
    melds, rivals = [], []
    for s in range(seeds):
        for seat in range(n):
            g = play(n, 6000 + s, seat, **policy)
            sc = g.score()
            best = max(sc, key=lambda d: (d["total"], d["gold"]))
            wins += int(best["seat"] == seat)
            tot = sum(g.stats.get(f"meld_{i}", 0) for i in range(1, 8))
            wsum = sum(i * g.stats.get(f"meld_{i}", 0) for i in range(1, 8))
            if tot:
                melds.append(wsum / tot)
            me = [d for d in sc if d["seat"] == seat][0]
            others = [d for d in sc if d["seat"] != seat]
            rivals.append(me["total"] - st.mean([d["total"] for d in others]))
    games = seeds * n
    share = wins / games
    ci = 1.96 * ((1 / n) * (1 - 1 / n) / games) ** 0.5
    return share, ci, st.mean(melds) if melds else 0, st.mean(rivals)


def main():
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    ns = [int(sys.argv[2])] if len(sys.argv) > 2 else [2, 3, 4]
    # The two levers are tested apart, and the first row is a CONTROL: a seat
    # given pro_bot's own settings must land on chance, or the harness is lying.
    CASES = [
        ("CONTROL — identical to pro_bot", {}),
        ("retire by meld damage, not rank", dict(retire_w=0.0)),
        ("hoard run material  (greed 0.8)", dict(greed=0.8)),
        ("hoard run material  (greed 1.6)", dict(greed=1.6)),
        ("hoard run material  (greed 3.0)", dict(greed=3.0)),
        ("both: greed 1.6 + meld-damage retire",
         dict(greed=1.6, retire_w=0.0)),
    ]
    for n in ns:
        print(f"\n{n} PLAYERS — one seat changed, {n-1} pro_bots, "
              f"{seeds * n} games, chance {1/n:.1%}")
        print(f"  {'':38}{'wins':>8}{'vs rivals':>12}{'meld':>7}   verdict")
        for label, policy in CASES:
            share, ci, meld, edge = h2h(seeds, n, **policy)
            if share > 1 / n + ci:
                v = "BEATS pro_bot"
            elif share < 1 / n - ci:
                v = "LOSES"
            else:
                v = "no measurable difference"
            print(f"  {label:38}{share:>8.1%}{edge:>+12.1f}{meld:>7.2f}   {v}")
        print(f"  (95% CI on every win share: +/-{1.96*((1/n)*(1-1/n)/(seeds*n))**0.5:.1%})")


if __name__ == "__main__":
    main()
