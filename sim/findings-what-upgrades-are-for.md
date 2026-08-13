# What is a purchased card actually for?

Every (rank, suit) in Blink is unique, so a bought card can be followed by
identity from the moment it is taken to whatever it ends up doing. 30 games per
player count, `pro_bot` in every seat.

## The answer: it feeds the victory row

| of every card bought | 2p | 3p | 4p |
|---|---|---|---|
| **ever played to the map** | 21% | 21% | 26% |
| **ended in the victory row** | **67%** | **65%** | **64%** |
| played *and* later retired | 10% | 9% | 11% |
| never played, never retired | 22% | 23% | 21% |
| times played, on average | 0.38 | 0.38 | 0.47 |

And from the other end:

| | 2p | 3p | 4p |
|---|---|---|---|
| share of victory-row cards that were **market purchases** | 67% | 65% | 64% |
| rounds from buying to retiring (median) | 2 | 2 | 3 |
| mean rank bought / mean rank retired | 15.1 / 12.9 | 15.0 / 12.4 | 15.2 / 12.2 |

**Two-thirds of everything in the victory row came from the market, and it got
there about two rounds after being bought.** The loop is: pay a gold and retire
a card to take a rank-15; it reaches your hand at the next recycle; your next
research retires *that* card into the row. The market is, in practice, a
rank-laundering machine for the victory row.

## The intent to build melds is there — the execution is not

**61–64% of purchases matched or sat adjacent to a rank the player already
held.** The bot buys for meld fit, deliberately: `_buy_value` scores a card by
how well it completes or extends a run, and rank barely enters it. So this is
not a bot that ignores melds; it is a bot whose meld purchases never arrive.

Two things get in the way.

**1. The meld limit binds about half the time.**

| | 2p | 3p | 4p |
|---|---|---|---|
| melds played **at** the tier's meld limit | 63% | 52% | 45% |
| melds short of the limit (the hand was the constraint) | 37% | 48% | 55% |
| mean meld size as a share of the limit | 89% | 81% | 76% |

When you are already playing the maximum your tier allows, a better card cannot
make the meld longer. That is most often true at two players and least often at
four.

**2. The retire choice is rank-led, and your newest card is your tallest.**
A rank-15 bought into a hand of 3–10 is, by construction, the highest card you
hold. The next time you research, it is the obvious thing to retire. Melds grow
over a game — 2.74 → 3.19 cards at four players — but that is the tier ladder
lifting the limit from 2 to 6, not the deck getting better.

## What this means

The fantasy the rulebook sells — *"you buy better cards to play bigger melds"* —
is not what the game does. The market is the victory-row engine, and melds are
governed by the tier ladder. That may be perfectly fine; it is a coherent game
either way. But the two should agree.

If purchases *should* reach the map, the levers are:

1. **The bought card goes into your hand, not your discard.** It is currently
   two rounds away from being usable, which is most of the reason it gets
   retired instead of played.
2. **A cooling-off rule** — a card bought this hand cannot be retired until it
   has been picked up once. Forces at least one chance to play it.
3. **Decouple the two.** Retiring and buying are currently one action; if
   retiring came from the *starting* deck only, purchases would have nowhere to
   go but the map.

If the market is *meant* to be the victory-row engine, §10 should say so
plainly, and the meld-building language in §04 and the tutorial should be
softened to match.
