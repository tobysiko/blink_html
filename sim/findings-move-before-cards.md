# Moving before you play — the sequencing you spotted

The engine ran free moves **after** the meld landed, so a unit always arrived
once the shooting was over. Moving first is a different rule: a free move
extends your **reach** for this turn's cards. March or sail up to a neighbour
for nothing, then play the card that kills.

Implemented as `MOVE_TIMING` (after | before) plus a `strike` move policy that
scores every legal move by how many rival units it brings within range of a
card actually in hand.

## Timing alone does nothing. Timing plus intent changes the game.

| 30 games | 2p | 3p | 4p |
|---|---|---|---|
| **kills — moves after (as now)** | 7.5 | 13.0 | 21.0 |
| kills — moves before, same defensive policy | 8.0 | 12.4 | 21.3 |
| **kills — moves before + strike policy** | **9.7** | **20.2** | **36.2** |
| free moves used, after → before+strike | 22 → 34 | 47 → 68 | 55 → **108** |
| gold spent attacking | 3.6 → 7.1 (3p) | | 9.4 → 15.8 (4p) |
| rounds | 12.2 → 13.1 | 14.6 → 17.6 | 16.2 → 19.3 |
| units on the map at the end | 19.2 → 19.1 | 17.7 → 17.6 | 16.1 → 14.8 |

**Kills rise 29% at two players, 55% at three, 72% at four**, and free-move
usage roughly doubles — from about a third of the allowance to most of it. This
is the answer to "do the bots use their moves": they did not, because there was
nothing worth moving *for*. Give movement an offensive purpose and it gets used.

Note the control: **moves before, with the old defensive policy, is flat.** The
timing change on its own is worth nothing. It is the combination that matters,
which is why this never showed up in any earlier measurement.

## But it does not make you win

| 3 players, 180 games each (chance 33.3% ±6.9%) | wins |
|---|---|
| CONTROL — defensive, moves after | 33.3% |
| strike policy, moves before | 31.7% |
| strike + sail through your own sea | 31.7% |

A player who plays this way kills far more and wins no more often. Attacking
costs a card and 1–2 gold, removes a rival unit worth 1 point, and does not put
a unit of your own on the ground — your reserve is untouched. It is a
denial move in a game scored on your own material.

So the change is a **lever on the game's temperature, not on who wins**. That is
arguably the more useful kind: it makes aggression *possible* and *legible*
without making it dominant. If v0.22 feels too peaceful at the table, this is
the single cleanest switch — one clause about when free moves happen.

The cost is length: three and four-player games run 3 rounds longer, because
killed units return to the reserve and have to be re-placed.

## The sea, again

`OCEAN_PASS_OWN` — sail through ocean tiles you own, still ending on open water
— is implemented and adds nothing measurable here (31.7% either way). It fixes
the *blocking* problem described in `findings-movement-and-ocean.md`, but the
sea route is not what makes strikes work; land reach is. The ocean's value
remains the water advantage, not the road.

Worth keeping the clause anyway, because "your own ships block your own lane" is
the kind of rule that makes a player at the table feel the game is broken even
when it costs them nothing.

## What is toggled, and what is still off

- `MOVE_TIMING = "after"` — **unchanged**, the rule as written.
- `MOVE_POLICY = "threat"` — the bot's defensive policy, unchanged.
- `OCEAN_PASS_OWN = False`, `MOVE_POLICY = "strike"` — available, off.

Nothing adopted; all four are switches waiting on your call.

*(Attacks still cannot be made by a moving unit — §07 says free moves are never
attacks, and that is unchanged. The strike pattern is move-then-spend-a-card,
which is legal today and simply never worth doing in the current order.)*
