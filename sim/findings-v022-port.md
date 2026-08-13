# Porting the simulator to v0.22 — what the new rules did

`pro_bot` in every seat, 40 games per player count, identical seeds against
v0.21. Invariants and conservation checked every round of every game at 2, 3
and 4 players.

## What was ported

- **Melds** — `enumerate_melds` is now brute force over combinations filtered
  by the one rule: the ranks must form an unbroken run. Exact, and cheap (a
  ten-card hand at limit 6 is about a thousand candidates). `is_legal_meld` is
  used by the invariant check, so an illegal meld can never reach the table
  unnoticed.
- **Five tiers** 2/4/6/4/4, with meld limit, free moves, food, **ascension
  coins** and **rank cap** all read off the current tier.
- **Trick** — lexicographic tiebreak (most cards, then highest, then
  next-highest…, then earliest played). Never a tie.
- **Match-discard** — matching the winner's card count and losing costs a card
  to the shared pile.
- **Shared pile** — refill to ten after feeding; the ten-card invariant is gone
  and the check now asserts *at most* ten.
- **Market** — one shuffled deck plus a six-position grid of stacks; draw onto
  a position, buy under your rank cap, refill. One upgrade per turn.
- **Effect B** — colonies: tiles + units + fortifications from the general
  supply, touch-two enforced, reach waived.
- **Water advantage**, **connected majority**, **new end trigger**.

### One bug worth recording

The match-discard rule fired **zero** times on first run. `win_size` was being
read inside the map-phase loop from `self.P[winner].played` — but the winner
acts first and clears that tuple, so every later comparison was against zero.
Captured before the loop instead. A toggle that produces *exactly* zero is
almost always a wiring fault, not a null result — same lesson as the combo-meld
A/B in v0.20.

> **SUPERSEDED — two later rule corrections moved these numbers.** The end
> trigger is now "the market thins to a single layer", not "the upgrade deck
> runs out", and research retires **from the hand only**. Together they take a
> three-player game from 8.7 rounds to 13.6 and flip the ending from the market
> to the twentieth unit. The deck-doubling table below is no longer the
> recommendation. See `findings-retire-from-hand.md`.

## The headline: games are ~40% shorter, and the market is the clock

| | 2p | 3p | 4p |
|---|---|---|---|
| rounds, v0.21 | 13.7 | 13.8 | 16.0 |
| rounds, **v0.22** | **7.5** | **8.7** | **11.0** |
| ends on the upgrade deck | 40/40 | 39/40 | 38/40 |

A seven-and-a-half-round two-player game is very short for a box that claims
60–120 minutes. The twentieth-unit ending fires three times in 120 games.

**It is a property of skilled play, as in v0.21.** Run the same engine with
random-legal bots and the picture inverts: games last 21 / 31 / 34 rounds at
2/3/4 players and end on the twentieth unit in 65 of 75. Random bots upgrade
only about a third of the turns they could. So the market clock fires because
good players research every turn — the better the table, the shorter the game.

**Why:** each upgrade consumes roughly two deck cards — one drawn onto the grid,
one bought and refilled. At one upgrade per player per turn the deck cannot
last. At three players the deck is 30 cards, six of which are locked in the grid
at setup.

### The tuning levers, measured

| setup (3p) | rounds | upgrades | ends on deck |
|---|---|---|---|
| grid 6, deck ×1 (as written) | 8.7 | 25.2 | 98% |
| grid 4, deck ×1 | 9.9 | 27.8 | 88% |
| grid 3, deck ×1 | 10.5 | 28.6 | 65% |
| **grid 6, deck ×2** | **12.2** | 35.2 | **0%** |
| grid 6, deck ×3 | 11.9 | 34.7 | 0% |

**Doubling the deck fixes it outright** — 12.2 rounds and the market never ends
the game, so the expansion race decides it again. Going beyond double adds
nothing. Shrinking the grid helps but only partly, and it also shrinks the
choice the grid exists to provide.

Practical options: deal the upgrade deck from **all ranks 11–20 at every player
count** (which also makes the Empire and Civilization rank caps mean something
below four players — currently they are decorative at 2p and 3p), or simply
print more advanced cards.

## Effect B has eaten the victory row

| | v0.21 | v0.22 |
|---|---|---|
| Effect B used per game | 4.8 | **9.7** |
| Effect C used per game | 1.6 | **0.5** |
| B's share of spent cards | 75% | **96%** |
| victory-row score | 8.3 | 14.5 |

**96% of victory cards spent go to B.** Effect C — take 2–5 gold — has
effectively stopped existing, and A is rare. The rulebook's "one row, three
appetites" is now one appetite: colonies are simply better than coins, because
they deliver tiles, units *and* free fortifications for the same card.

This is the balance flag from the rulebook report, now measured. If the three-way
tension is meant to survive, B needs a cost — the obvious candidate is making the
player pay the fortification coins rather than the supply.

## Ascension is 42% of all gold earned

Not the +55% I estimated from the rulebook — **larger in share terms**.
Across 40 three-player games, ascension coins are **42% of total income**
(52 gold earned per game). One-off rewards now dominate the economy, and food
falls from 40% to 30% of income partly because there are fewer recycles in a
shorter game and partly because there is simply more gold.

## Everything else

| 3 players | v0.21 | v0.22 |
|---|---|---|
| mean score | 26.4 | 29.3 |
| leader minus last | 14.7 | **6.2** |
| last place's score | 19.0 | **26.1** |
| mean meld size | 2.44 | **2.66** |

**The unified meld rule does what it was meant to** — melds get bigger (2.44 →
2.66 cards) because duplicates and runs combine freely.

**Games are much closer**, but read that carefully: a large part of the
narrowing is simply that the game is 40% shorter, leaving less time to diverge.
Fix the deck length and this number should be re-measured before it is trusted.

## Not measured

- **The water advantage never fired** in scored games. The bot now actively
  looks for a sea move to claim it, but Ocean holds one unit and empty adjacent
  Ocean is rare, so the trigger is hard to reach. Whether that is the rule or the
  map is unresolved — flagged, not concluded.
- **The rank cap almost never binds** (one blocked purchase in eight rounds),
  because the deck at 2p and 3p tops out at rank 15 or 18 anyway.
- The objectives module remains un-ported and now also conflicts with the
  connected-majority rule.
