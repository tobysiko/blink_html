# Four rule changes, measured — and why Effect C stays unused

All four implemented, invariants clean at 2, 3 and 4 players. 40 games per
player count with `pro_bot` in every seat, identical seeds, each change also
flipped back on its own so its share of the effect is isolated.

## 1. Dominance = your largest connected stretch

Points go to the biggest connected group of a terrain **you have units on**,
counted in tiles. A stack of five on one tile is a stretch of one.

**The rule as first specified made ties much worse, not better.** Letting every
player at the top level score meant a one-tile patch each — the common case —
scored for everybody:

| 3 players, per game | dominance pts/player (of 12) | terrains tied (of 4) |
|---|---|---|
| old rule: most units + connectivity gate | 0.15 | 0.00 |
| **largest area, level players all score** | 6.20 | **3.55** |
| largest area, level broken by units on that terrain | 4.17 | **0.35** |
| largest area, tied terrain scores for nobody | 2.65 | 0.00 |
| largest area, patch must be 2+ tiles | 3.83 | 1.18 |

**Adopted: level broken by units on that terrain.** Same stretch → whoever has
more units there takes it. It costs nothing to teach, needs no minimum-patch
clause, and it puts the old measure to work as the tiebreak rather than the
main rule. Ties fall from 3.55 to 0.35 per game and dominance settles at
2.0–4.2 points a player — 12–15% of a final score, against population's ~60%
and the victory row's ~20%. A real category, not a dominant one.

## 2. The hand refills the moment it empties

| per game | end-of-turn refill | **immediate** |
|---|---|---|
| research lost to an empty hand, 3p | 11.1 | **0.0** |
| research lost to an empty hand, 4p | 16.5 | **0.0** |
| upgrades, 2p / 3p / 4p | 15.2 / 23.9 / 29.4 | **20.2 / 27.7 / 32.3** |
| rounds, 2p | 13.4 | 12.4 |

This closes the "all-in turn" question outright: playing your whole hand no
longer silently costs you your research, because you pick up ten fresh cards
mid-turn and retire one of those instead. Upgrades rise 10–30%.

## 3. The market is a 3×3 grid

Close to neutral — slightly more choice and slightly more research, no change
to length or ending. Rounds 12.6→12.4 (2p), 13.9→13.3 (3p), 15.4→16.3 (4p);
upgrades up about one per game.

Worth knowing: **a bigger grid works against the market end trigger**, since
thinning to a single layer now means nine positions instead of six.

## 4. The upgrade deck is ranks 11–20 at every player count

| 2 players | deck 11–15 | **deck 11–20** |
|---|---|---|
| victory-row points | 11.8 | **15.4** |
| rounds | 10.7 | 12.4 |
| ends on the last unit | 42% | **100%** |

At two players the old deck topped out at 15, entirely under Kingdom's cap, so
three of the five caps were decorative. The full deck fixes that and adds real
victory-row value.

**The cost is the market clock.** It was still firing in 58% of two-player
games; now it fires in none. Combined with the 3×3 grid and the tight caps,
**the twentieth unit is effectively the game's only ending at every player
count.** That is now a deliberate consequence of three separate decisions
rather than an accident — but if you want two clocks back, the levers are a
smaller grid and a shorter deck, both of which pull against the caps mattering.

## Why Effect C is never chosen

Two reasons, and only the first is the bot's fault.

**It was only ever reached for while starving.** `_spend_c` was called from the
feeding step alone. Given a bot that also asks "is this card paying for its
slot?", usage rises from 0.0–0.7 to 0.7–2.4 per game.

**And there is a free lunch nobody was taking.** The victory row scores its
**third-highest** rank, so with a full row of five your two lowest cards cost
*nothing* to spend:

| row 7 · 9 · 12 · 14 · 16 | scores | after spending the lowest | cost |
|---|---|---|---|
| five cards | 12 | 12 | **0** |
| four cards | 12 | 12 | **0** |
| three cards | 12 | 2 | 10 |

Two free effects sit in every full row, for A and B as much as for C. The
rulebook never says so.

**But even played perfectly, C does not help.** A player who cashes every free
slot wins no more often — 31.1% at three players against a 33.3% chance
baseline, ±9.7%, and 23.3% against 25.0% at four. Victory-row score is
unchanged, gold left over rises from 3.2 to 3.7.

**The reason is that C pays in the one currency that is not scarce.** By the
time you hold three victory cards, ascension coins and cashed cards already
cover food, and games end with 2.5–6.3 gold unspent. A and B convert into
tricks and into units on the map — population is ~60% of the final score. C
converts into more of something you already have.

So C is not mispriced so much as **paying in the wrong thing**. Options: give
it a scarce payout instead of gold (units returned to reserve, a free research,
cards from the shared pile), accept it as the rescue valve it already is — it
does get used when starving — or drop the cards to two effects. Not changed;
your call.

## 5. The victory row scores 1 per card, plus the centre rank

`vrow_score()` is now one function used by the scorer, the retire heuristic and
the effect valuation, so the three copies of this formula cannot drift apart
again.

**It closes the free lunch.** From a full row of 7 · 9 · 12 · 14 · 16, spending
your lowest card used to cost 0 points and now costs 1:

| | centre rank only | **+1 per card** |
|---|---|---|
| row of five, 7·9·12·14·16 | 12 | **17** |
| cost of spending the lowest | **0** | **1** |
| cost of spending the next lowest | **0** | **1** |

| 40 games, pro bots | centre only | +1 per card |
|---|---|---|
| victory-row points, 2p / 3p / 4p | 15.4 / 13.8 / 10.6 | **19.6 / 17.2 / 13.1** |
| cards still in the row at the end | 3.7 / 3.4 / 2.9 | 4.2 / 3.5 / 3.1 |
| population points | 19.6 / 17.6 / 16.4 | unchanged |
| dominance points | 6.2 / 4.2 / 3.2 | unchanged |
| effect A used | 4.8 / 8.2 / 11.3 | 4.8 / 8.2 / 11.6 |
| effect B used | 7.1 / 8.7 / 7.0 | 7.1 / 8.7 / 7.8 |
| **effect C used** | 1.2 / 0.7 / 2.4 | **0.0 / 0.1 / 0.7** |

**A and B are untouched** — a trick won and a colony founded are both worth more
than the one point they now cost. **C dies completely**, because the free slot
was the only thing keeping it alive. This is confirmation rather than a new
problem: C was already returning a currency the player has in surplus, and now
it costs a point to get it.

**Two things worth knowing about the new balance.** Scores rise about 3–4
points, and the victory row becomes roughly **equal to population** as a scoring
source — 44% against 45% at three players, where it was 37% before. The row is
now as big as the map. If that is more weight than the row should carry, the
lever is the per-card point (½ point per card, or 1 point only for cards above
some rank) rather than the centre slot.
