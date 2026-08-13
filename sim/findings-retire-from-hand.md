# Retire from your hand only — what closing the free lunch did

**Rule.** Research retires a card **from your hand**. Cards already played to
the table are spent and cannot be retired. Previously the engine drew from hand
*plus* personal discard, and in 21 of 30 upgrades in one sample game it retired
a card the player had played to the map **that same turn** — one card doing map
work and banking its rank in the victory row.

`pro_bot` in every seat, 50 games per player count, identical seeds either side.
Invariants and conservation checked every round at 2, 3 and 4 players.

## The bot had to be fixed first

Retiring was free before, so "retire your highest card" was a fine policy. Once
it costs a card you could still have played, it is a real decision, and the
first heuristic I wrote — weigh the row's point gain against `hand_power`, the
same trade the draft makes — **lost to plain max-rank**: 26.7% against a 33.3%
chance baseline.

The reason is that the two things are not commensurate. A hand recycles every
few rounds; the victory row is permanent, and the rank cap makes tall cards
scarce. So rank leads and hand material only breaks ties. With that fixed:

| retire policy (180 games, 3p, chance 33.3% ±6.9%) | wins |
|---|---|
| row gain + hand material, rank ignored | 26.7% |
| rank leads, hand material breaks ties | 32.2% |
| plain max-rank | — (baseline) |

**Honest reading: once rank leads, the extra machinery buys nothing measurable.**
Every weight from 0.4 upward gives the same mean retired rank (12.0), the same
row score and the same win rate, all inside the confidence interval. The
heuristic is kept because it is not *worse* and it degrades sensibly when the
row is nearly full, not because it was shown to be better.

## The rule makes games longer and slightly poorer

| 50 games, pro bots | 2p | 3p | 4p |
|---|---|---|---|
| rounds, hand + table (old) | 10.4 ±0.2 | 11.5 ±0.2 | 13.8 ±0.5 |
| rounds, **hand only** | **12.6 ±0.4** | **13.6 ±0.4** | **15.2 ±0.7** |
| score, old | 32.8 ±0.6 | 28.8 ±1.2 | 28.2 ±1.2 |
| score, **hand only** | **30.7 ±0.9** | 28.0 ±1.2 | **25.5 ±1.2** |

Longer at every player count, and lower-scoring at 2p and 4p (3p is inside the
interval). This is a **useful** direction: the v0.22 port's headline complaint
was that skilled play finished a two-player game in seven and a half rounds.

## The mechanism is the food bill, not the market

| per game, 3 players | old | hand only |
|---|---|---|
| upgrades | 29.9 | 28.8 |
| **hand recycles** | **11.0** | **14.8** |
| **gold spent on food** | **28.1** | **36.0** |
| cards played | 97.8 | 113.6 |
| mean meld size | 2.83 | 2.79 |
| victory-row score | 10.3 | 10.1 |
| mean rank retired | — | 12.0 |

Upgrades barely move. What moves is the **recycle rate: +35%**. Every research
now pulls a card out of the hand, so hands run dry sooner, and each recycle
charges the tier's food. The food bill rises 28% and the whole economy runs
tighter and longer. Meld size is untouched, so the card play itself feels the
same — the tax lands on the treasury.

The victory row survives intact (10.3 → 10.1) at a mean retired rank of 12.0.
Players still build the row; they just pay for it.

## Open question for the table: the all-in turn

**Research is lost about 10 times per game — roughly a quarter of the
opportunities — because the player's hand is empty when the map phase ends.**

That is a direct consequence of the rule, not a bot artifact: the meld leaves
the hand during the card phase, so a player who plays their whole hand has
nothing left to retire, whatever order they take their map actions in.

Three readings, and this needs a designer's decision rather than a simulation:

1. **As written.** Going all-in costs you your research that turn. It is a real
   tension and it is easy to state.
2. **Research before the card phase.** Move the action, and the choice becomes
   "research or hold cards", which is a different and softer decision.
3. **Table only when the hand is empty.** Keeps research always available but
   restores most of the free lunch on exactly the turns it mattered.

Option 1 is what is implemented and what the rulebook now says.

## Also corrected while in there

§04's tier table described the rank cap as "the highest card rank you may
**retire**". It is the highest rank you may **buy from the market** — the cap is
a buying rule, as §10 and the note beside it already said. Fixed.
