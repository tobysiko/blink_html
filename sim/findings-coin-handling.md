# Coin handling at the table

20 three-player games, median 18 rounds, current v0.20 rules. One "movement" =
one reach for the bank, so taking 3 gold at once counts as one.

## Volume

| Event | Per game | Per player per game | Coins moved |
|---|---|---|---|
| gain: unused cards | 36.2 | 12.1 | 36.2 |
| spend: upgrade | 21.7 | 7.2 | 21.7 |
| spend: upkeep | 10.8 | 3.6 | 17.4 |
| gain: effect C | 4.0 | 1.3 | 15.2 |
| spend: attack | 3.5 | 1.2 | 4.8 |
| spend: fortify | 2.1 | 0.7 | 2.1 |
| gain: held back | 0.2 | 0.1 | 0.2 |
| **TOTAL** | **78.5** | **26.2** | **97.7** |

- **4.3 coin movements per round** across the whole table
- **1.45 per player per round**
- **Peak gold held by any one player: mean 4.0, maximum 5**

## The headline for components

**86% of all movements are a single coin.** Only 4% move four or more. Peak
holding never exceeded 5 in 20 games.

That means:
- **denominations are unnecessary** — 1-value coins only;
- **each player needs about 6 coins**, not a pile. A 40-coin supply is roughly
  twice what three players ever hold at once;
- there is no counting-out, no making change, no stacks to audit.

## The fiddly moments

Consecutive movements by the same player within one round:

| | share |
|---|---|
| a single movement | 47.5% |
| two in a row | 34.4% |
| three in a row | 12.3% |
| four or more | 5.4% |

The recurring sequences:

| Per game | Sequence |
|---|---|
| 7.15 | gain unused cards → spend on upgrade |
| 3.40 | gain unused cards → spend on upkeep |
| 1.45 | gain unused cards → upgrade → upkeep |
| 1.35 | gain unused cards → upgrade → upgrade |
| 1.25 | gain unused cards → fortify |
| 1.05 | effect C → upkeep |

**Over half of all coin gains are immediately spent by the same player in the
same round.** The commonest is take-then-upgrade, seven times a game.

## Assessment

The volume is fine — 4.3 movements a round across three players is less than one
per player per turn, and every movement is a single coin with no change to make.

The waste is in the round trip. Roughly **11 of the 36 gains per game are taken
from the bank and returned within the same round**, most often to buy an upgrade
that costs exactly one coin — the same coin that just arrived.

Two cheap fixes worth testing at the table:

1. **Net it.** Let a player who is about to spend simply not take the gain: "I'd
   take one for my unused card and pay one to upgrade" becomes no coins moving
   at all. Purely a table convention; no rules change.
2. **Batch the take.** Gains from unused cards all arrive at the same moment in
   the map phase, so they are already one movement. Upkeep is likewise one. The
   only genuinely repeated movement is the upgrade, which happens 7.2 times per
   player per game — worth checking at a real table whether upgrading feels
   coin-heavy or fine.

Nothing here suggests the economy is unworkable physically. The one number to
watch in playtest is the upgrade: it is the most frequent single-coin spend, and
it is the one a player repeats several times in a turn.
