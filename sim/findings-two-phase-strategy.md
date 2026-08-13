# "Grow population first, switch to card VPs near the end"

Half right, and the half that fails is the interesting one.

Implemented as a per-seat strategy: the leader's remaining reserve is the game's
clock (the twentieth unit ends ~100% of games), so `phase` runs 0 → 1 as the
table approaches it. Early, the player cashes far fewer cards and weights the
victory row far less; late, both revert.

Measured as **points scored above the average rival**, paired on the same seed
and seat — a much lower-variance signal than win rate at 3–4 players. The
control scoring exactly +0.00 is the check that the harness is honest.

| 3 players, 300 games each | edge vs rivals | game length |
|---|---|---|
| CONTROL — pro_bot as now | +0.00 ±1.41 | 14.9 |
| map-first, **switch** at 6 units left | +0.99 ±1.51 | 14.3 |
| map-first, **never switches** | **+1.02 ±1.50** | 14.3 |

| 4 players, 300 games | edge vs rivals |
|---|---|
| CONTROL | +0.00 ±1.77 |
| map-first, then rank | −0.44 ±1.74 |

## The switch contributes nothing

+0.99 with the switch, **+1.02 without it.** Every bit of the (small, and not
statistically significant) benefit comes from the map-first bias. The phase
transition itself is worth zero.

## Why — and this is a design finding, not a bot finding

**The two scoring tracks do not compete.** Since purchases started landing in
the hand, research is card-neutral: you retire one card and take one back. So
banking rank costs you no cards, and therefore no population. Population is
limited by your reserve and the tier ladder; the row is limited by gold and the
market. They draw on different pools.

The single place they touch is **cashing** — a card turned into a coin is a
settle you did not make, 55–59% of the time. But the bot's existing thresholds
already handle that trade about as well as the phase logic does, which is why
biasing it earns a point and timing it earns nothing.

So there is no "when do I switch" decision in v0.22, because there is nothing to
switch *between*. A player can pursue both tracks at once at almost no cost.

## If you want that decision to exist

It needs a real cost on one side. Candidates, cheapest first:

1. **Make research cost a card net.** Retire one, take one, *and* the taken card
   goes to your discard rather than your hand — which is what it did before this
   session. That reintroduces the tension, at the price of the purchase problem
   we just fixed.
2. **Make retiring cost a placement.** Research is a map-phase action; it could
   consume one of the cards you would otherwise spend on the map.
3. **Cap research by tier**, so climbing the ladder for melds and free moves is
   also what unlocks banking rank — making the two tracks sequential rather than
   parallel.

Option 3 is the one I would look at: it uses machinery already on the board, and
it turns "grow first, then bank" from a strategy the player *can* follow into
one the rules make them follow.

## The practical answer for the bot

Set the map-first bias on and leave the phase switch off — it is a point of
score at three players, nothing at four, and neither is significant. It is not
worth complicating `pro_bot` for. `PHASE_PLAY` defaults to off; the constants
are `ENDGAME_AT`, `PHASE_CASH_EARLY`, `PHASE_ROW_EARLY`.
