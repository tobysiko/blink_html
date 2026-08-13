# Why plains are explored least — diagnosis

## The deck is not the problem

Cards played per game, by suit: **plains 21.6, forest 20.0, ocean 20.6,
mountain 20.6.** The deck is 80 cards, one of every (rank, suit), and it plays
out evenly. The bag holds 15 of each terrain.

## Nor is it the bot

Bots prefer settling to exploring, which any player would — a settle places a
unit that scores and claims ground, an explore places neither. The placement
policy actually gives forest and mountain settles a *bonus*, which would push
mountain explores down, not up. The imbalance appears despite that.

## The cause is stack capacity

| Suit | Settles/game | Explores/game | Tile holds |
|---|---|---|---|
| plains | **16.3** | **2.3** | 3 |
| forest | 13.9 | 6.8 | 2 |
| ocean | 10.1 | 6.3 | 1 |
| mountain | 12.7 | 7.7 | 1 |

A plains tile absorbs **three** cards before it is full; a mountain absorbs
**one**. Players also begin standing on plains. So a plains card almost always
finds a plains tile with room and settles; a mountain card finds every mountain
already full and must create a new one.

Capacity used on the final map confirms it: plains 60%, forest 72%, ocean 81%,
**mountain 90%**.

**The consequence is that the map's terrain mix diverges from the bag's.** Equal
supply, unequal absorption: a finished map holds about **10.5 mountains, 6.2
ocean, 5.9 forest, 5.2 plains**. Mountains nearly exhaust their 15 while a third
of the plains never leave the bag.

This is emergent, not a bug — and arguably thematic, since dense terrain needs
fewer tiles to hold the same people. But it is worth deciding deliberately,
because it drives which objectives are reachable. If you want the map to mirror
the bag, the lever is stack capacity, not deck composition.

## One thing that *was* a bug: the market grew without bound

§06 says that when digging the bag for a suit, the tiles you pass go **face up
into the market**. Nothing ever removes them, so the market inflates and clogs
with whatever nobody wants:

| | market at game end |
|---|---|
| rulebook as written | **12.5 tiles** — plains 5.7, forest 3.4, ocean 3.0, mountain 0.4 |
| dug tiles returned to the bag | **6.0 tiles** — plains 3.2, forest 1.1, ocean 1.6, mountain 0.2 |

A market stated as "twice the player count" ends at double that, two-fifths of
it the least-wanted terrain, sprawling across the table. §04's "refill back up to
twice the player count" cannot shrink it.

**Fixed in the engine** (`MARKET_KEEPS_DUG = False`): dug tiles go back into the
bag, which is reshuffled. The market stays at exactly 2n all game. **This needs a
one-line rulebook change to §06.**

## Effect on the objectives

Re-run with the market fixed, 62 games:

| Objective | Before | After |
|---|---|---|
| Highland Rivers | 45% | 42% |
| River Delta | 52% | 39% |
| Mountain Fortress | 19% | 29% |
| Coastal Chain | 42% | 23% |
| Mountain Range | 26% | **10%** |
| Deep Wood | 13% | **6%** |

Everything got harder, because a clogged market was quietly making rare suits
easier to find face up. Mountain Range and Deep Wood have fallen below the
useful range and now want either a point rise or replacement.

Also fixed: a dead line in the placement policy — an explore bonus that tested
`m.tiles[cell]` for a cell that is by definition *not* a tile, so it never fired.
