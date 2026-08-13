# Tighter rank caps — 11 / 13 / 15 / 17 / 20

**Rule.** The rank cap per tier drops from 13 / 15 / 17 / 20 / none to
**11 / 13 / 15 / 17 / 20**. It remains a buying rule: it applies only at the
moment you take a card from the market.

`pro_bot` in every seat, 40 games per player count, identical seeds either
side. Invariants checked every round at 2, 3 and 4 players.

## It does what it was meant to — at 3 and 4 players

| per game | 2p old → new | 3p old → new | 4p old → new |
|---|---|---|---|
| upgrades | 17.1 → 17.3 | 28.6 → **24.7** | 35.8 → **26.3** |
| mean rank sitting in victory rows | 13.5 → 13.4 | 15.4 → **14.7** | 16.5 → **14.6** |
| rounds | 12.6 → 12.9 | 13.6 → 14.2 | 15.4 → 16.3 |
| mean score | 30.7 → 30.9 | 28.4 → 28.9 | 25.3 → 25.3 |

At four players the tall cards genuinely arrive later: a quarter fewer
purchases, and the average rank a player is holding drops by two full ranks.
Scores are untouched, so this is a pacing change, not a power change — which is
what you want from a thematic fix.

## At two players the caps are decorative, and this is arithmetic not noise

The advanced deck is dealt from **ranks 11–15 at 2p**, 11–18 at 3p, 11–20 at 4p.
So:

| | Tribe 11 | Settlement 13 | Kingdom 15 | Empire 17 | Civilization 20 |
|---|---|---|---|---|---|
| 2p (deck 11–15) | binds | binds | **covers the deck** | decorative | decorative |
| 3p (deck 11–18) | binds | binds | binds | binds | decorative |
| 4p (deck 11–20) | binds | binds | binds | binds | binds |

At two players Kingdom's cap of 15 already reaches the top of the deck, and
Tribe is two units wide — you are out of it by round two. That is why the 2p
column above barely moves: research blocked by the cap is **0.2 per game**
against 9.1 at four players.

**If you want the caps to mean the same thing at every count**, deal the
advanced deck from **ranks 11–20 at all player counts** — the same
recommendation the port findings made for a different reason. Not simulated
here; flagged.

## The bot had to be checked, and the finding survived it

With a cap of 11 facing a grid of tall cards, research becomes a gamble: you
draw blind, and can only buy if the card falls under your cap. The bot happily
fished every turn, wasting **22.9 research actions per game** at 4p and burning
the upgrade deck on cards nobody could take.

That is a bot artifact, so I taught it to look first — research only when
something visible is buyable, or the deck is at least 35% likely to oblige:

| 4 players | old caps | new, bot fishes | new, bot looks first |
|---|---|---|---|
| rounds | 15.4 | 16.8 | 16.3 |
| upgrades | 35.8 | 26.7 | 26.3 |
| blocked by cap | 10.7 | 22.9 | 9.1 |
| declined on purpose | 0 | 0 | 13.3 |
| mean rank in victory rows | 16.5 | 14.5 | 14.6 |
| mean score | 25.3 | 25.3 | 25.3 |

**The headline numbers barely move.** The rule's effect is real; only the waste
was the bot's fault.

## The cost: the market end trigger is now effectively dead

| ends on the last unit placed | old caps | new caps |
|---|---|---|
| 2 players | 92% | 90% |
| 3 players | 80% | **92%** |
| 4 players | 85% | **100%** |

The upgrade deck still drains completely — but it drains **into the grid**
rather than into players' hands, because every blocked or declined purchase
leaves the drawn card stacked on a position. A market that keeps getting deeper
never thins to a single layer, so the trigger you added in this version now
almost never fires.

**This is a designer's call, not a simulation result.** Either:

1. **Accept one clock.** The twentieth unit ends the game; the market-thinning
   rule stays as a rare backstop. Simplest to teach, and one fewer thing for
   players to watch.
2. **Only draw if you can buy.** Check the cap before drawing rather than
   after. Blocked research then costs the deck nothing and the market thins
   again — but it also removes the bluff of burying a rival's target card.
3. **Widen the deck to 11–20 at every count** (above), which makes the caps
   bind everywhere and gives the market more to thin through.

## Units per tier: 2 / 4 / 5 / 5 / 4

Moving one unit from Kingdom to Empire changes exactly one thing — the
Kingdom→Empire boundary falls from the twelfth unit to the **eleventh**. Every
other boundary is where it was (2, 6, 16, 20).

| 40 games per count | 2/4/6/4/4 | 2/4/5/5/4 |
|---|---|---|
| rounds, 2p / 3p / 4p | 12.9 / 14.2 / 16.3 | 12.7 / 14.2 / 16.4 |
| mean score, 2p / 3p / 4p | 30.9 / 28.9 / 25.3 | 30.8 / 28.3 / 25.3 |
| finished still in Kingdom, 3p | 11% | **4%** |
| finished still in Kingdom, 4p | 13% | **10%** |
| reached Empire or better, 3p | 89% | **96%** |

**Neutral on length and score, which is the point.** The one thing it moves is
the number of players who run out of game while still stuck in Kingdom: at
three players that more than halves. Melds of five and the free-move allowance
arrive one unit sooner, and the wider Empire tier gives that stronger position
more room to be enjoyed. Both boards re-laid out cleanly; the layout guards
pass.

## The connected-majority rule, measured against its actual purpose

The rule exists to **reduce ties**, and dominance is deliberately a minor
scoring source — 12 points is a ceiling, not a target, and the map-objectives
module is what makes terrain matter. So the question is not "is dominance
small", it is **what does the rule cost per tie it removes**.

Connectivity is currently measured **over tiles of that terrain only**: you may
walk from one of your Plains to another only through an adjacent Plains you
also occupy. Two Plains three hexes apart in an otherwise solidly connected
empire count as split. Against a looser reading — your units on that terrain
lie inside one connected group of *your territory*, walked through any tile you
hold — and against no rule at all:

| per game, out of 4 terrains | majorities awarded | terrains ending tied |
|---|---|---|
| **2 players** | | |
| no connectivity requirement | 4.20 | 0.20 |
| connected through your territory | 1.38 | **0.00** |
| connected through that terrain *(current)* | 0.05 | 0.00 |
| **3 players** | | |
| no connectivity requirement | 4.40 | 0.38 |
| connected through your territory | 1.18 | **0.10** |
| connected through that terrain *(current)* | 0.25 | 0.03 |
| **4 players** | | |
| no connectivity requirement | 4.40 | 0.38 |
| connected through your territory | 1.95 | **0.07** |
| connected through that terrain *(current)* | 0.17 | 0.00 |

**Ties were never the problem.** With no rule at all, only 0.2–0.4 terrains per
game end tied — one game in three. The current rule buys that down to ~0.03 by
disqualifying about 4.15 majorities per game. It pays roughly twelve majorities
per tie removed.

**The looser reading gets the same tie result for a fraction of the cost.** It
removes essentially all ties (0.38 → 0.07) while still awarding 1.2–2.0
majorities per game — a small, live category worth 1–2 points a player, which
is what a minor scoring source should look like. Scattered empires still fail
it; only the same-terrain-adjacency requirement goes.

The rulebook wording is ambiguous on exactly this point — *"all your units on
that terrain form a single connected group"* does not say **through what** — so
whichever you choose, §13 needs a clause. Not changed; awaiting your call.

*(Method note: an earlier pass of this reported "0.0 majorities lost to the
connected rule". That was wrong — `score()` is what increments the counter and
I read the stat before calling it. Everything above reads it after.)*

## Also fixed while in there

The `market` figure was still the **v0.21 four-suit ladder** — four per-suit
decks each exposing their lowest card — while both the rulebook and the
tutorial described a 2×3 grid. It has been redrawn as one shuffled deck feeding
a six-position grid, with stack depths marked and the over-cap cards crossed
out. The tutorial's caption and its "four cards face up" heading were saying
four where the body said six; both corrected.
