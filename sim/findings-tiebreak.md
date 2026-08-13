# Would lexicographic tiebreaking ever fire?

Measured with `sim/tiecheck.py` over 6,250 tricks. A tie only counts here if it
**decides the trick** — two players level after effective meld size, Effect A's
"wins ties", and top rank, so the winner is currently settled by play order.
Two players tying for second place is not a tie that matters.

## How often

| | 2 players | 3 players | 4 players |
|---|---|---|---|
| tricks measured | 2,155 | 2,223 | 1,872 |
| any two melds sharing size + top rank | 5.8% · **1.04/game** | 9.2% · **1.70/game** | 15.8% · **2.95/game** |
| ties that **decide** the trick | 4.8% · **0.86/game** | 3.3% · **0.62/game** | 2.9% · **0.54/game** |

Roughly **one decisive tie every one to two games**, and it barely moves with
player count. More players means more matching melds but also more ways to be
beaten outright before the tie matters.

## How deep the comparison would have to go

| of the decisive ties | 2p | 3p | 4p | all |
|---|---|---|---|---|
| broken by the **second** card | 10 (9.7%) | 21 (28.4%) | 14 (25.9%) | 45 (19.5%) |
| broken by the **third** card | 9 (8.7%) | 5 (6.8%) | 2 (3.7%) | 16 (6.9%) |
| **equal all the way down** | 84 (81.6%) | 48 (64.9%) | 38 (70.4%) | **170 (73.6%)** |

**Lexicographic tiebreaking resolves about a quarter of the ties it is aimed at.**
Nothing is ever broken below the third card. Three-quarters of the time you
would still fall through to play order, so the existing rule cannot be retired —
it would become a third tier rather than a replacement.

Net effect: the rule changes the winner in roughly **0.16–0.22 tricks per game**,
about **one game in five**.

## Why so much stays equal — this is the real finding

Break the 3-player ties down by the shapes involved:

| shapes tied | ties | resolved by a later card |
|---|---|---|
| straight vs straight | 37 | **0 of 37** |
| single vs single | 10 | **0 of 10** |
| set vs straight | 11 | 11 of 11 |
| straight vs two-set | 10 | 10 of 10 |
| two-set vs two-set | 6 | 5 of 6 |

The pattern is almost perfectly clean: **a later card breaks the tie if and only
if the two melds are different shapes.**

That is structural, not luck. A straight's length and top card pin every rank in
it — a straight of three topped by 9 *is* 7-8-9, in every suit combination. So
two straights that tie on size and top card are always the identical run and can
never be separated by looking further down. Same for singles: there is no second
card. Together those are 47 of 74 ties, and all 47 are immune.

## What the rule would actually mean at the table

Since it only separates melds of *different* shapes, and a set's second card
equals its top card while a straight's is one lower:

> **Lexicographic tiebreaking means sets and two-pair beat straights of the same
> size and top card.**

That is a design statement, not a neutral tiebreak. It makes the set family
quietly stronger — and sets are already the shape that clusters on the map,
where straights must walk a path. Worth deciding on its merits rather than as a
tidiness fix.

## If the goal is to retire "whoever played earlier"

It does not achieve that: 74% of decisive ties survive it. Options that would:

- **Highest single card of a different suit**, or a fixed suit order as the final
  tier. Total, and it never falls through.
- **Split the trick** — both tied players place their melds. Removes the
  arbitrariness entirely, at the cost of a rule about simultaneous placement.
- **Leave it.** At 0.6 decisive ties a game and a stated rule that resolves them,
  play order is not obviously worse than a rule that fires once in five games and
  favours one meld family while doing it.

## Method note

`engine.py` gained a two-line instrumentation hook after the trick is ranked:

```python
if getattr(self, "on_trick", None):
    self.on_trick(self, order, key, winner)
```

It is inert unless a caller sets `on_trick`, so default behaviour is unchanged.
`tiecheck.py` uses it to read every player's meld and the engine's own ordering
key, so the tie definition here is the engine's, not a reimplementation of it.
