# Purchases land in your hand — and the shared pile, measured

## The change works, but it exposes a deeper problem

A bought card now goes straight into the hand instead of the personal discard.
Retire one, take one, so the ten-card ceiling is untouched.

| 30 games per count | 2p → | 3p → | 4p → |
|---|---|---|---|
| bought card **reached the map** | 21% → **50%** | 21% → **45%** | 26% → **49%** |
| times played, each | 0.38 → 0.65 | 0.38 → 0.60 | 0.47 → 0.67 |
| bought cards played per game | 7.8 → **20.4** | 10.6 → **35.0** | 15.6 → **54.5** |
| never played, never retired | 22% → 11% | 23% → 10% | 21% → 11% |
| **mean meld size** | 3.59 → **3.31** | 3.15 → **2.83** | 2.96 → **2.68** |
| meld as a share of the limit | 89% → 84% | 81% → 73% | 76% → 70% |
| hand recycles per game | 10.1 → 7.6 | 14.7 → 12.0 | 21.9 → 16.4 |
| of purchases played, share played **ALONE** | 9% → **23%** | 11% → **27%** | 16% → **29%** |

Purchases reach the map two to three times as often, and dead cards halve. But
**melds get smaller**, and the last row says why.

## The market sells ranks that cannot join your hand

The starting deck is ranks 3–10. The market sells 11–20. **A rank-15 can never
form a run with a 7.** So a purchase arrives as an isolated card in rank space,
and is played as a one-card meld — which is why the share of purchases played
alone nearly triples, and why average meld size falls even as more bought cards
reach the table.

It only starts to pay once you have bought *several adjacent* high cards. The
rank-cap ladder helps here more than it looks: a Tribe player capped at 11 buys
a card that sits right next to the 10 they already hold, and each tier lets them
extend upward by two. That is the mechanism working as designed — it is just
slow, and a single purchase is always a step backwards for meld length.

Recycles falling (14.7 → 12.0 at three players) is the other half: research used
to remove a card from your hand, and now it does not, so hands last longer and
churn less.

## Retiring your purchase is no longer punished

Under the old rule, keeping your purchases — retiring by meld damage rather than
by rank — **lost**: 22.9% against a 33.3% chance baseline. It now sits at
**37.3% ±5.3% over 300 games**, which overlaps chance.

**Correction to something I said mid-session:** a first pass over 105 games read
43.8% and I called it a win. At 300 games it is 37.3% ±5.3% — indistinguishable
from the house bot, not better than it. The honest claim is that the meld-
friendly retire went from *clearly bad* to *free*, which is still the direction
you wanted, but it is not yet an edge.

Hoarding is still bad, and unchanged: greed 3.0 wins 1.0% of its games. Waiting
does not build a hand, whatever the purchase rule.

## The shared pile is a trickle, not a reservoir

It is fully implemented — fed only by the match-discard, drawn from only at a
recycle. It is also almost always nearly empty:

| 40 games | 2p | 3p | 4p |
|---|---|---|---|
| cards in it, mean across all rounds | **0.4** | **0.9** | **1.3** |
| biggest it ever got in a game | 1.9 | 3.5 | 5.3 |
| rounds where it sat **empty** | **69%** | **51%** | **41%** |
| cards added per game | 3.6 | 8.6 | 11.8 |
| cards drawn out per game | 3.5 | 8.3 | 11.4 |

In ≈ out, every game: it is a pass-through, not a store. At two players it holds
nothing at all for two rounds in three and never reaches three cards.

**§09 currently oversells it** — *"cards you lose flow into the shared pile, and
cards other players lost flow back to you. A hand you drafted carefully will
drift, and what it drifts toward is whatever the table has been throwing away."*
At 3.6 cards moved per game at two players, against a ten-card hand, the drift
is barely there. Either the language should be toned down, or the pile needs
more inflow to be the mixing mechanism it is described as.

The viewer now shows the pile's contents — face down at the table, so this is a
designer's X-ray — with a bar chart of its size across every round of the game,
the current round highlighted. It sits under the market.
