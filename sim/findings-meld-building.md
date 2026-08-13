# Is playing for melds a losing strategy?

Yes — and worse than that, **it produces smaller melds, not bigger ones.**

One seat is given a committed meld-building strategy, the other seats stay on
`pro_bot`, seats are rotated so nothing is a seat effect. Two levers, tested
apart:

- **greed** — how much the hand you *keep* is worth when choosing what to play.
  `pro_bot` values it at 0.30. Raising it is what "holding cards back to build
  a bigger meld later" means in practice.
- **retire** — `pro_bot` retires its highest card. The meld player retires
  whatever costs its future melds least, so purchases stay in the deck instead
  of being laundered into the victory row.

## Three players, 105 games per row, chance 33.3% ±9.0%

| one seat changed | wins | points vs rivals | mean meld | |
|---|---|---|---|---|
| **CONTROL — identical to pro_bot** | **33.3%** | **+0.0** | 2.83 | harness is honest |
| retire by meld damage, not rank | 22.9% | −2.5 | 2.88 | **loses** |
| hoard run material, greed 0.8 | 37.1% | +0.7 | 2.82 | no difference |
| hoard run material, greed 1.6 | 19.0% | −6.4 | **2.66** | **loses** |
| hoard run material, greed 3.0 | 1.0% | −19.8 | **2.39** | **collapses** |
| greed 1.6 + meld-damage retire | 11.4% | −9.7 | 2.69 | **loses** |

The control landing exactly on chance with a zero point differential is the
check that matters — without it none of the rest is worth reading.

**Mild patience is free; commitment is fatal.** Resolved over 300 games each:

| greed | wins (±5.3%) | vs rivals | mean meld |
|---|---|---|---|
| 0.5 | 35.3% | +0.8 | 2.85 |
| 0.8 | 34.0% | +0.1 | 2.84 |
| 1.1 | 28.7% | −1.9 | 2.81 |

All three are inside the interval. There is no measurable reward for valuing
your remaining hand above what `pro_bot` already does, and a steep penalty past
about 1.0.

## The punchline: hoarding makes melds *smaller*

Mean meld size falls monotonically as the player tries harder to build one:
**2.83 → 2.82 → 2.66 → 2.39**. The strategy is self-defeating, and the reason
is structural:

**Holding cards back does not build anything.** Your hand is fixed. The run is
either in it or it is not, and playing fewer cards this turn does not make next
turn's hand better — the same ten cards come round again. There is nothing to
build *toward*. So a player "working on a powerful meld" is not accumulating;
they are simply waiting, and paying tempo, map presence and trick wins every
round they wait.

The only thing that can genuinely change your hand is a market purchase — and
`findings-what-upgrades-are-for.md` shows those reach the map about a fifth of
the time.

## What this means for the design

Two documented behaviours now point the same way:

1. Bought cards mostly end up in the victory row, not in melds (65%/21%).
2. Withholding cards to build a meld actively shrinks your melds.

Together they say the **incentive to keep working on powerful melds has no
mechanism behind it.** Meld size is governed by the tier ladder — the limit
climbing 2 → 3 → 4 → 5 → 6 as your reserve empties — and the ladder is driven
by putting units on the map, which is the opposite of holding cards back.

If bigger melds are meant to be something a player *builds toward*, the game
needs a way to improve a hand that does not route through the victory row. The
candidates, cheapest first:

1. **A bought card goes into your hand, not your discard.** Currently it is two
   rounds from being playable, which is most of why it gets retired instead.
2. **Let a player hold cards across a recycle** — a small hand-size allowance
   above ten, so that saving a card actually accumulates something.
3. **Reward run length directly**, not just card count: a meld of four
   consecutive ranks does something a meld of four cards does not.

If instead the game is happy that melds are paced by the tier ladder, then §04
and the tutorial should stop describing melds as something you build, and the
market should be presented as what it is — the victory-row engine.

*(Reproduce: `python3 meld_bot_test.py 35 3`.)*
