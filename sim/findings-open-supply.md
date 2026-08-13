# The tile supply is open — no bag, no face-up tile market

## What changed

The bag and the face-up tile market are gone. All unused tiles sit in four open
piles by terrain; a player exploring simply takes the tile they need, until that
terrain runs out. Implemented and verified: conservation holds at 2, 3 and 4
players — 60 tiles, 15 of each, always accounted for between the supply and the
map.

**This deletes four rules at once:** the bag, the market of twice-the-player-count,
the refill step at the end of every round, and the dig-through-the-bag fallback
when a suit was missing. §06's explore paragraph drops from three sentences to
one. It also removes the market-inflation bug entirely rather than patching it —
there is no longer anything that can grow.

**And it fixes a naming collision.** "Market" now means exactly one thing: the
four face-up advanced cards. It previously meant the tile market as well, which
made §03, §04 and §06 ambiguous on a first read.

## Effect on the terrain question

| Suit | Settles | Explores | Holds | Tiles left of 15 |
|---|---|---|---|---|
| plains | 14.3 | 2.4 | 3 | 9.6 |
| forest | 12.3 | 6.4 | 2 | 8.6 |
| ocean | 8.2 | 5.2 | 1 | 9.8 |
| mountain | 11.2 | 6.7 | 1 | **5.3** |

The plains/mountain gap **remains**, because it was never about the bag — it is
stack capacity. A plains tile absorbs three cards, a mountain one, so plains
cards settle and mountain cards must create new ground. Mountains still run
lowest, though "ran out" now happens only 0.1 times a game rather than being
masked by an inflating market.

If you want the map's terrain mix to match the supply, the lever is stack
capacity. Nothing about the supply mechanism will do it.

## Effect on the objectives

Achievement rates are healthier than under either previous version, because a
tile you need is now always reachable:

| Objective | Bag + market | Dug tiles returned | **Open supply** |
|---|---|---|---|
| Highland Rivers | 45% | 42% | **52%** |
| Coastal Chain | 42% | 23% | **42%** |
| Mountain Range | 26% | 10% | **35%** |
| Mountain Fortress | 19% | 29% | **32%** |
| River Delta | 52% | 39% | **32%** |
| Deep Wood | 13% | 6% | **10%** |

Five of six now sit between 32% and 52% — a good band for a goal you push toward
and sometimes miss. **Deep Wood at 10% is the outlier** and wants either a rise
to 6 points or replacing; a forest triangle needs three forest tiles you occupy,
and forest holds two units, so it is the one pattern where capacity works against
the shape.
