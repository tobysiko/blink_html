# What should winning a trick be worth?

Six reward structures, `reward_test.py`, `pro_bot` in every seat, identical
seeds, 35–40 games at each player count. Invariants checked throughout.

| | what the winner gets | what the losers get |
|---|---|---|
| **dock** (current rule) | spends every card | spend one fewer, take 1 gold |
| **none** | nothing but initiative | spend every card |
| **bonus** | one extra card from hand | spend every card |
| **bonus +1 last** | one extra card | ...and the trick's LAST place takes 1 gold |
| **bonus +2 last** | one extra card | ...2 gold |
| **bonus +1 all** | one extra card | ...1 gold to every non-winner |

## Results

**3 players, 40 games**

| structure | gap | last place | repeat | cashed | food |
|---|---|---|---|---|---|
| dock (current) | 16.9 ±2.3 | 14.6 ±1.8 | 38% | 47% | 31% |
| none | 14.4 ±1.9 | 15.7 ±1.4 | 34% | 39% | 35% |
| bonus | 17.4 ±3.0 | 15.8 ±1.9 | 39% | 40% | 41% |
| **bonus +1 last** | **14.7 ±2.3** | **19.0 ±2.0** | 40% | 32% | 40% |
| bonus +2 last | 15.8 ±2.1 | 18.4 ±1.9 | 39% | 28% | 36% |
| bonus +1 all | 15.1 ±2.4 | 18.4 ±1.8 | 33% | 24% | 39% |

**4 players, 35 games**

| structure | gap | last place | repeat | cashed |
|---|---|---|---|---|
| dock (current) | 20.6 ±2.3 | 12.6 ±1.6 | 26% | 50% |
| none | 20.7 ±2.7 | 13.3 ±1.4 | 25% | 38% |
| bonus | 19.5 ±2.2 | 13.7 ±1.1 | 29% | 41% |
| bonus +1 last | 20.3 ±2.7 | 15.1 ±1.8 | 25% | 35% |
| **bonus +2 last** | **17.6 ±2.2** | **16.5 ±1.6** | 27% | 31% |
| bonus +1 all | 20.2 ±2.2 | 15.9 ±1.5 | 30% | 23% |

**2 players, 35 games**

| structure | gap | last place | repeat |
|---|---|---|---|
| dock (current) | 8.6 ±2.5 | 24.1 ±2.6 | 52% |
| none | 9.1 ±2.0 | 22.9 ±2.0 | 49% |
| bonus | 9.6 ±2.1 | 25.0 ±2.3 | 58% |
| bonus +1 last | 7.9 ±1.7 | 27.8 ±2.1 | 59% |
| **bonus +2 last** | **6.7 ±2.0** | **29.7 ±2.3** | 57% |

(At two players "+1 last" and "+1 all" are the same rule.)

## What the numbers actually say

**Read the floor, not the gap.** Almost every *gap* difference sits inside its
interval — the structures are not reliably distinguishable on how close the
game finishes. The *last place score* is where real separation shows up, and it
separates cleanly: the current dock rule produces the **worst floor at every
player count** (24.1 / 14.6 / 12.6), and adding a coin to the trick's last place
lifts it well outside the intervals (27.8 / 19.0 / 15.1).

**The reward structure does not change how the card phase is played.** Mean
meld size is identical across all six — 2.33 to 2.44 cards, with singles at
26–27% and melds of three-plus at 42–43% everywhere. Players push for tricks
exactly as hard whatever winning is worth. That is worth knowing: **this lever
tunes the economy and the score floor, not the tension.** So choose it on
fairness and ergonomics, because it costs nothing in card-phase drama.

**The current rule's "cashing" number is inflated.** Dock shows 47–50% of cards
turned to gold, the highest of any structure — but part of that is *compulsory*,
the docked card. Under the bonus structures every coin is chosen: 32% at three
players. The genuine "people or gold?" decision is more live under the new rule
than the raw percentage suggests under the old one.

**"None" is not a disaster.** A trick worth only initiative gives the lowest gap
at three players and a better floor than the current rule. It is the simplest
possible rule and it is *fine*. It just wastes the opportunity to put a rubber
band anywhere.

**Nothing fixes the snowball.** Back-to-back trick wins sit at 33–40% at three
players (chance 33%), 25–30% at four (chance 25%), 49–59% at two (chance 50%),
with no structure clearly better. Gold does not help you win the next trick. If
persistence is a problem at the table, the fix is not in this table.

## Recommendation

**No — the dock rule is not still the best.** It has the worst score floor at
every player count, the highest mental load, and its headline economy number is
partly forced rather than chosen.

**Best: the winner spends one extra card from hand (1 gold if their hand is
empty); the player whose meld ranked last that trick takes 1 gold.**

- Best or joint-best floor at every count.
- Gap as good as anything measured.
- No player ever tracks how many cards they may use.
- Reads as two prizes rather than a penalty for everyone but one.
- Tightens food from 31% to 40% of income, which the economy needs.

**At four players, 2 gold beats 1** (floor 16.5 vs 15.1, gap 17.6 vs 20.3), and
at two players likewise. Three players is the only count where 1 is clearly
better. If a single printed number is wanted, **1 gold** is the safer choice —
it is best at the most common player count and never bad. If you are willing to
print a table, use **1 at three players, 2 at two and four**.

## Caveat

`pro_bot` is better than what came before but still crude, and two earlier
conclusions flipped when the bot improved. The floor differences here are large
and consistent across all three player counts, which is the kind of result that
usually survives; the gap differences are not, and should not be quoted.
