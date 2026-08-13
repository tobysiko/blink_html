# The 2/4/6/8 band distribution — what it means and what it would cost

## What the numbers refer to

Yes — they are the **unit capacities of the four reserve bands on the player
board**, top to bottom. Each band carries a meld limit and an upkeep, and your
*current band* is the topmost one that still holds units. Because you always
draw from that band, **a band's unit count is how many placements you spend at
that meld limit before moving down.**

### Current — 4 / 6 / 8 / 2

| Band | Units | Meld limit | Upkeep |
|---|---|---|---|
| Founding | **4** | 2 | free |
| Growth | **6** | 3 | 1 |
| Expansion | **8** | 4 | 2 |
| Empire | **2** | 5 | 3 |

So you play your first 4 placements at meld limit 2, the next 6 at limit 3, the
next 8 at limit 4 — and only your **last 2** at limit 5. Placing that final unit
also ends the game, so Empire is a sliver at the very end rather than a phase.

### Proposed — 2 / 4 / 6 / 8

Same 20 units, monotonically increasing instead of rising then collapsing:
2 at limit 2, 4 at limit 3, 6 at limit 4, **8 at limit 5**.

## Why the simulation favoured it

Re-measured against the **current** ruleset — A declared blind, B in the map
phase, proportional starvation, targeted fortification — 12 three-player games
each. (The earlier figures predated effects A and B, which shortened games on
their own; these supersede them.)

| bands | rounds | time at limit 4 | at limit 5 | melds of 4 | of 5 | per player: 4s | 5s | upkeep paid |
|---|---|---|---|---|---|---|---|---|
| **4/6/8/2** (now) | 20 | 22% | **2%** | 7.9% | **0.3%** | 1.56 | **0.06** | 13.8 |
| 3/5/6/6 | 20 | 31% | 11% | 12.1% | 1.0% | 2.42 | 0.19 | 19.3 |
| **2/4/6/8** | 18 | 41% | **19%** | 16.9% | **2.6%** | 3.03 | **0.47** | 22.8 |

The decisive column is the last-but-one. Under the current bands a player plays
a five-card meld **0.06 times per game** — about once every sixteen games. At a
three-player table, most groups would never see a straight of five or a full
house at all. Under 2/4/6/8 it is 0.47 per player, so roughly one appears at the
table each game: rare enough to feel like an event, common enough to exist.

Four-card melds roughly double as well, 1.56 → 3.03 per player.

## What would actually change

**On the board.** The four bands print different slot counts: 2, 4, 6, 8 instead
of 4, 6, 8, 2. `board_a4.py` regenerates from one constant. The visual shape
inverts — the widest row moves from third to last.

**The endgame gets bigger, the opening gets sharper.** Your final 8 placements
happen at meld limit 5 instead of your final 2, so the game builds to a genuine
crescendo. But you leave Founding after only **2** placements — round one or two
— so the gentle opening at meld limit 2 essentially disappears, and upkeep
starts almost immediately.

**Upkeep rises 65%**, 13.8 → 22.8 gold a game, because you reach the expensive
bands sooner and sit at Empire's 3 gold for your last eight placements rather
than your last two. That is the real cost, and it is not small.

**Games get shorter**, 20 → 18 rounds — on top of the shortening that effects A
and B already caused (28 → 18 before this change). If both land, a three-player
game runs around 16 rounds. That may now be too short rather than too long.

**Documents to change:** §04's band table, the player-board figure caption, the
quick reference's "Reserve bands" entry, and the tutorial — which currently
teaches the first rounds at meld limit 2 and would need rewriting, since under
2/4/6/8 that phase is over almost before it starts.

## The caveat that matters

The band is the binding constraint on meld size only **35%** of the time; the
hand binds the other 65%, because a hand is played from ten cards down to zero
and nearly 40% of meld decisions happen with three or fewer cards left. That
ceiling is why even 2/4/6/8 only reaches 2.6% five-card melds rather than
something like 20%.

So 2/4/6/8 is a real improvement to a real problem — the top of the ladder is
currently decoration — but it buys time *at* the limit rather than hands capable
of using it. If the goal is for the full house to become a shape players build
toward, the lever is the hand and the market, not the reserve.
