# Free moves and the sea

## Bots use about a third of their allowance

| 30 games | 2p | 3p | 4p |
|---|---|---|---|
| free moves **used** per game | 22.2 | 46.6 | 55.2 |
| free moves **allowed** per game | 80.0 | 138.8 | 201.5 |
| share of the allowance taken | **28%** | **34%** | **27%** |

The policy is deliberately narrow, and says so in its own docstring:
reinforce a tile a rival can take, or evacuate one already lost. Two-thirds of
the allowance is simply never spent, because nothing meets that bar. So the
headline number is a statement about the bot, not yet about the game.

## A simple movement strategy that should work — and does not

Since dominance became "your largest connected stretch of a terrain", free
moves are the only way to weld two patches into one without spending a card.
Nothing else in the game does that. So: score every legal move by the net
change in the sum of your largest stretches across all four terrains, and take
the best one.

It does what it says — **dominance rises from 3.2 to 3.8 points** — but it does
not win games:

| 4 players, 320 games (chance 25.0% ±4.7%) | wins | its dominance |
|---|---|---|
| CONTROL — reinforce / evacuate | 25.0% | 3.2 |
| join up your terrain | **24.4%** | 3.8 |

**A correction worth recording:** at 160 games this read 32.5% and looked like a
clear win. At 320 it is 24.4%. Half a point of dominance is not enough to move a
31-point score, and the moves spent chasing it are moves not spent defending.

That is the real finding: **movement has no strategy behind it because nothing
it can achieve is worth enough.** Reinforcing saves a unit (1 point). Joining a
patch is worth 3 points but only at the moment of scoring, and rivals can break
it afterwards. Neither justifies planning around.

## The sea is a road nobody can drive on

The rule is *"move a unit standing on Ocean across **unoccupied** Ocean"*. But
Ocean holds exactly one unit, and holding ground is how you score. So the moment
you build a stretch of ocean and settle it, you have blocked your own sea lane.

| 30 games | 2p | 3p | 4p |
|---|---|---|---|
| ocean tiles on the final map | 6.2 | 9.2 | 10.9 |
| of those, **unoccupied** | **1.5** | **1.8** | **2.3** |
| biggest **navigable** stretch of open water | **0.9** | **1.0** | **1.1** |

**The largest continuous run of open sea in a finished game is about one tile.**
Sea movement is a rule with no board to run on. Building a continuous ocean does
not create a road; it creates a wall, because to own it you must fill it.

This is a direct conflict between two rules, not a tuning problem:

- Ocean holds 1 → you cannot pass through your own ocean tile.
- Dominance and population reward occupying tiles → you occupy every ocean tile
  you can reach.

Options, cheapest first:

1. **Let units pass through Ocean tiles you own** — blocked only by *rivals*.
   One clause, and it makes an owned ocean chain into exactly the road the
   rulebook already describes ("the sea is a road rather than a wall").
2. **Ocean holds 2.** Costs the terrain its distinctiveness.
3. **Drop sea movement**, and let Ocean earn its place through the water
   advantage alone.

## The water advantage, by contrast, is working

The first sea move each turn granting a free explore of any terrain fires
**6.2–8.2 times a game** and is worth having:

| | score with | score without |
|---|---|---|
| 3 players | 40.1 | 38.8 |
| 4 players | 32.5 | 30.4 |

Note the irony: the advantage is *triggered* by a sea move, and sea moves are
nearly impossible to make. It fires as often as it does only because the bot
hunts for the one legal sea move each turn specifically to claim it. Fix the
blocking problem and this gets stronger, not weaker.

## Attacks from the sea

Not possible as written, and worth stating plainly: free moves are never attacks
(§07), so a unit can never arrive by sea and strike. Reaching a rival's coast by
sea only positions you to spend a card on them next turn — and since cards act on
any tile adjacent to your civilization anyway, the sea approach buys nothing a
land border does not.

If naval raiding is wanted, it needs its own rule; it is not going to emerge from
the current pieces.
