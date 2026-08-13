# Why Effect C is dead — the third card is load-bearing

Your correction was right and it broke my explanation. I had said C loses to
cashing a hand card because "cashing costs a card, C costs a point". But cashing
a hand card is also a point — the unit you did not place. Measured:

| voluntary cashes | 2p | 3p | 4p |
|---|---|---|---|
| mean map value the cashed card gave up | 3.00 | 3.02 | 3.11 |
| share that would have **settled a unit** | 59% | 55% | 57% |

The bot is not skimming worthless cards. It cashes cards worth about 3 on its
own scale, and **well over half of them would have put a unit on the map.** Per
victory point, cashing pays 1 gold and C pays 2–5. C should be the better deal.

## The real reason: the row scores nothing until the third card

`vrow_score` = 1 per card, plus the centre slot once you hold three. That makes
the third card carry the entire centre-slot rank:

| row | scores | after selling the lowest | **cost** |
|---|---|---|---|
| 16 | 1 | 0 | 1 |
| 12 · 16 | 2 | 1 | 1 |
| **9 · 12 · 16** | **12** | **2** | **10** |
| 7 · 9 · 12 · 16 | 13 | 12 | 1 |
| 5 · 7 · 9 · 12 · 16 | 14 | 13 | 1 |

**Selling out of a three-card row costs about ten points.** Selling out of a
four or five-card row costs one. C pays 2–5 gold either way.

And rows are small:

| final row size | 2p | 3p | 4p |
|---|---|---|---|
| mean | 3.5 | 3.1 | **2.8** |
| **rows of 4+ — where C is cheap** | 45% | **21%** | **16%** |

At three and four players, **four rows in five sit exactly on the cliff.** C is
not underpriced; it is unavailable, because the only card a player could afford
to sell is one they almost never have.

## This also explains the rest of the row's behaviour

- **Effect B fires at 5–7 per game** and the bot guards it at `vrow >= 4` — the
  same threshold. B is used precisely when the row is off the cliff.
- **A is used most**, and A is the only effect that does not touch the row's
  size at all in the bot's accounting until it resolves.
- The "two lowest cards are free to spend" property I found earlier only holds
  for a **full** row. At three cards there is no free ammunition at all.

## Correction to what I told you earlier

I said C was dead because gold is always printable from the hand, and separately
that ascension was the first lever to pull. Both were wrong:

- Cashing is **not** cheap — it costs a settle more than half the time.
- Removing ascension raised total income (players cashed more) and did not
  revive C, because C's problem was never the price of gold.

The single fact that explains C is the **cliff at three cards.**

## What would actually change it

1. **Remove the cliff.** Score the centre slot at any row size — with one or two
   cards, score the lowest one you hold. The row then has no step in it, selling
   always costs about one point, and C becomes a live option at every row size.
   This is a one-line change to `vrow_score` and it makes the row's value legible
   to a player, which the current step does not.
2. **Move the threshold to two cards.** Smaller change, same direction: the
   cliff moves to a size players do reach.
3. **Leave it and drop C** — which is the recommendation from
   `findings-card-effects.md`, replacing it with **D · Conquest**. Nothing about
   this finding argues against that; if anything the cliff is a second reason C
   never earns its space on the card face.

Worth noting that option 1 is worth considering **regardless of C**, because the
cliff currently makes a three-card row worth 12 and a two-card row worth 2. That
is a very large discontinuity for a player to discover at scoring time.
