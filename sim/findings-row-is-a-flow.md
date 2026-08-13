# The row scores at the end — so my bot was pricing it wrong

You said the middle card only scores at the very end, and players have plenty of
time to ignore it. That is exactly right, and it was a bug in the bot, not a
property of the game.

`_vp_of` priced the victory row **as if scoring happened today**. So a
three-card row looked like it scored 12, and selling from it looked like a
ten-point disaster. But the player will retire more cards before the game ends,
and against the row they will *actually* have at scoring time, the same sale
costs about one point:

| selling the 9 from a row of 9 · 12 · 16 | cost |
|---|---|
| priced as if the game ended now | **10** |
| priced with 1 more card still to come | **1** |
| 2 more | 1 |
| 3 more | 1 |

One further card collapses the whole cliff. The row is a **flow**, not a stock —
players retire roughly nine cards a game and finish holding three.

## Fixing it brings C back

Two things were wrong, and they are worth separating:

1. **An arbitrary guard.** `_maybe_cash_c` refused to sell below three cards
   outright. That alone was blocking most of C.
2. **The pricing.** Once selling is allowed, the today-price still forbids it
   from a three-card row.

| Effect C uses per game | 2p | 3p | 4p |
|---|---|---|---|
| original bot (guard + today-pricing) | 0.5 | 0.9 | 0.8 |
| guard removed, still priced today | 0.8 | 3.5 | 7.6 |
| **priced against the end** | **2.9** | **5.8** | **8.7** |

And the substitution you would expect appears — the player stops burning hand
cards for coins:

| | 2p | 3p | 4p |
|---|---|---|---|
| hand cards cashed, today → end pricing | 19.7 → **14.6** | 27.2 → **23.6** | 36.0 → **28.5** |

Five to eight fewer cards a game converted to coins. That is the trade you
identified: a victory card at 2–5 gold is better value than a hand card at 1
gold, once the victory card is priced honestly.

## But it is not an edge

| one seat prices its row at the end, rest price it today | wins |
|---|---|
| 3 players, 210 games (chance 33.3% ±6.4%) | 37.6% |
| 4 players, 208 games (chance 25.0% ±5.9%) | 26.4% |

Both inside the interval. Table scores are flat too: 44.1 → 43.7, 38.8 → 38.3,
30.6 → 30.6. **C is now used, but it is not yet worth using.** Cards saved from
cashing do not translate into population — 19.2 → 18.9, 17.8 → 18.0, 16.9 →
15.8 — because the constraint on population is the reserve and the tier ladder,
not the supply of cards.

## What this changes about the earlier advice

- The **cliff at three cards is much less serious than I said.** It only bites
  in the final round or two, when there is no time left to refill. It is still
  worth smoothing for legibility — a player reading the board mid-game cannot
  easily tell what their row is worth — but it is not the reason C is dead.
- **C's real problem is what it pays, not what it costs.** Even priced
  correctly, and even used 6–9 times a game, it does not move the result. Gold
  is not the binding constraint; the reserve and the tier ladder are.

That strengthens rather than weakens the recommendation in
`findings-card-effects.md`: **replace C with D · Conquest.** An effect that
returns gold cannot matter in an economy where gold is not what is scarce. An
effect that takes ground and empties your reserve acts directly on what is.

*(`ROW_HORIZON` defaults to 2 and is now used by the retire heuristic as well as
by C. Set it to 0 to reproduce the old myopic behaviour.)*
