# Getting players to retire their weak cards first

Nine candidate rules, 30 games each at three players, `pro_bot` in every seat.
The bot's fixed bias toward high rank is switched off for these runs so that
each rule is played on its own scoring function rather than on the one it was
tuned for.

## First: half the problem already fixed itself

Before purchases went into the hand, **65%** of the victory row was market
cards. It is now **32%**. Moving the buy destination did most of the work.

And players already start low: **the first card retired averages rank 6.0**,
because early on there is nothing else — your hand is 3–10 and you own no
purchases yet. The problem is not the first retirement, it is that the *mean*
climbs to 12.0 as the game goes on.

## The nine rules

| rule | 1st retired | mean rank retired | row = bought | bought cards played | meld | score |
|---|---|---|---|---|---|---|
| **centre — as now** | 6.0 | 12.0 | 32% | 21.2 | 2.94 | 38.6 |
| highest rank in row | **9.4** | 11.8 | 33% | 18.8 | 2.90 | 43.5 |
| count only, no rank | 6.1 | 10.5 | 31% | 21.7 | 2.97 | 25.2 |
| ascending retirement | 6.0 | 10.3 | **46%** | 15.7 | 3.03 | 24.0 |
| only at/below rank cap | 6.0 | 11.9 | 33% | 21.2 | 2.94 | 38.7 |
| ascending + cap | 6.0 | 10.3 | 46% | 15.6 | 3.03 | 24.1 |
| **retire your lowest, no choice** | **4.6** | **8.3** | **23%** | **27.4** | 2.96 | 33.7 |
| **retire one of your lowest 2** | **4.6** | **8.6** | **24%** | **27.9** | 2.83 | 34.5 |
| retire one of your lowest 3 | 4.9 | 9.3 | 25% | 27.7 | 2.87 | 35.1 |
| retire one of your lowest 4 | 4.9 | 9.9 | 27% | 26.6 | 2.83 | 36.3 |
| row scores its longest run | 6.0 | 10.3 | 30% | 25.1 | 2.89 | 29.5 |

## What works: restrict the choice, don't rewrite the scoring

**"You may retire one of your N weakest cards."** No scoring change at all — it
is a legality rule, one line, and it reads naturally at the table: *research
sheds something you have outgrown.*

N is a dial between effect and agency:

| N | mean rank retired | row = bought | purchases reaching the map | player still chooses? |
|---|---|---|---|---|
| 1 | 8.3 | 23% | 27.4 | no |
| **2** | **8.6** | **24%** | **27.9** | **barely — but yes** |
| 3 | 9.3 | 25% | 27.7 | yes |
| 4 | 9.9 | 27% | 26.6 | yes |
| off | 12.0 | 32% | 21.2 | yes |

**N = 2 or 3 looks like the sweet spot.** Nearly all the effect of N = 1 — mean
retired rank falls from 12.0 to 8.6, the row stops being a dumping ground for
purchases, and 32% more bought cards reach the map — while leaving a real
decision on the table. N = 1 removes the decision entirely for almost no extra
gain.

The cost is honest and small: the row scores less because it now holds low
cards, so mean scores fall from 38.6 to about 34.5. If the row should stay
where it is, the per-card point can absorb it.

## What does not work, and why

**"Row scores your highest rank" backfires.** It was meant to make low cards
free to retire, since a low card cannot lower a maximum. In practice players
lead with their *best* card to set the maximum early — the first retirement
jumps from rank 6.0 to **9.4**, the worst of any rule tested. Order does not
matter to the final score, so the myopic play is to bank the big one first.

**"Ascending retirement" makes the laundering worse, not better.** Forcing each
retirement to outrank the last means later retirements *must* be high — and the
only high cards you own are purchases. The share of the row that came from the
market rises from 32% to **46%**. It also blocks so many retirements that scores
collapse to 24.0.

**"Only at or below your rank cap" does nothing.** 11.9 against 12.0. By the
time you hold tall cards you are at a tall tier with a tall cap, so the
constraint never binds.

**"Count only" and "longest run"** both pull the mean rank down to ~10.3–10.5
but cost 9–13 points of score, and neither touches the purchase share. The run
rule is the more interesting of the two — a row as a lineage rather than a
treasury — but it competes with melds for the same run-building instinct.

## Recommendation

Add one sentence to §10: **"The card you retire must be one of the two lowest
in your hand."** Nothing else changes — the row still scores 1 per card plus its
centre slot, and the figure still works.

Not implemented as a default; the toggle is `RETIRE_LOWEST_N`.

*(Reproduce: `python3 retire_low_test.py 30 3`.)*
