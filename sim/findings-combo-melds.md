# Combination melds — simulated

**The rule as tested.** Any two multi-card melds may be played together if they
fit within your meld limit and share no cards. No single cards as components.
`twoset` already covers pair+pair and 3+2, so the new ground is everything
involving a straight: pair+run, run+run, triple+run.

Implemented behind `engine.COMBO_MELDS`. Invariants and component conservation
hold at 2, 3 and 4 players with it on. Each component lands as its own piece —
a run walks in rank order, a set clusters — so a combination meld lands in two
separate places on the map.

Same seeds on both sides: the two columns are the same games under two rules.

## It does make big melds real

| 3 players, 40 games | baseline | combo |
|---|---|---|
| melds of 4 cards | 12.5% | **15.5%** |
| melds of 5 cards | 1.2% | **2.7%** |
| 4+ card melds per game | 7.5 | **9.6** (+28%) |
| **5-card melds per game** | **0.65** | **1.43** (+119%) |
| time at meld limit 5 | 7.4% | **10.4%** |

At 4 players the effect is larger still: 5-card melds go 0.55 → 1.68 per game,
and 4+ card melds 8.4 → 12.4 (+48%).

Combination melds are **12% of everything played**, so they are not a curiosity —
they become a standard part of the vocabulary immediately.

Put beside the earlier band finding, the top of the ladder is now genuinely
reachable. Under 4/6/8/2 bands a five-card meld appeared 0.06 times per player
per game; 2/4/6/8 raised that to 0.47; combinations take it to roughly 1.4–1.7
per game at the table.

## It does not accelerate the game

| | baseline | combo |
|---|---|---|
| rounds per game, 3p | 18.3 | 17.6 (−4%) |
| rounds per game, 4p | 18.4 | 18.1 (−1%) |
| cards played per game | 118.9 | 118.4 (−0%) |

**Between −1% and −4%.** The reason is that the end trigger is a player placing
their twentieth unit, and combination melds do not create units — they only let
you place the ones you have in bigger batches. Cards played per game is flat, so
the same amount of game happens; it happens in marginally fewer, larger rounds.

If shortening the game is a goal, this is not the lever.

## Three things worth weighing before adopting it

**1. It eats the straight.** Straights fall from 45.3% of melds to 37.0%, and
two-set from 9.5% to 5.7%. Combinations do not add to the repertoire so much as
absorb the middle of it: a run of two that used to be played alone is now half
of something bigger.

**2. It loosens the map constraint, which is the game's signature.** A straight
of four must walk four connected cells in rank order with terrain matching each
suit. Split as 2+2, it becomes two easy two-cell placements that need not touch
each other. So the rule does not only make big melds *available* — it makes big
melds *easy to place*, by letting a player sidestep the discipline that makes a
long run interesting. That is the substantive design question here, more than
the numbers.

**3. Singles go up, slightly but consistently** — 33.2% → 34.5% at 3p, 36.8% →
38.6% at 4p. Sweeping four or five cards into one meld strips a hand of its
combinable material faster, leaving unmatched dregs. The distribution gets more
polarised: more big melds *and* more singles, fewer of the twos and threes in
between.

## What does not change

Mean final score 22.0 → 21.6, and the score split barely moves — population
50.4% → 51.4%, victory row 27.0% → 26.3%, dominance 22.6% → 22.3%. Cards turned
to gold falls 4%, explores are flat. It is not a power creep; it is a
redistribution of which shapes get played.

## Implementation note

`_split` originally read the components from instance state set during
placement. `smart_bot` calls `_split` while *evaluating* options, before that
state exists, so every combination scored as unplaceable and no bot ever chose
one — the first A/B run came back byte-identical to baseline. The components are
now passed in as an argument. Worth remembering: a toggle that produces exactly
zero change is more often a wiring fault than a null result.
