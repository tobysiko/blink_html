# Map objectives — feasibility review

Scored on the final maps of 30 simulated three-player games (90 player-boards),
under v0.20 rules: touch-two placement, 15 tiles of each terrain, 2/4/6/8 bands.

## 1 · The deck as written

| # | Objective | Pts | Exact wording |
|---|---|---|---|
| 1 | Coastal Control | 1 | Each adjacent plains–ocean pair you occupy both tiles of. A tile may belong to only one pair. |
| 2 | Island Nation | 1 | Each ocean tile you occupy that is adjacent to at least four other ocean tiles. |
| 3 | Breadbasket | 2 | Each cluster of three mutually adjacent plains tiles you occupy. Distinct tiles per cluster. |
| 4 | Highland Lake | 2 | Each ocean tile you occupy whose every neighbour is mountain or forest. |
| 5 | Mountain Fortress | 3 | Each cluster of three mutually adjacent mountain tiles you occupy. Distinct tiles per cluster. |
| 6 | Mountain Range | 3 | Each straight line of three adjacent mountains you occupy. Distinct tiles per range. |
| 7 | Greenway | 3 | Each straight line of four tiles alternating forest and plains. Distinct tiles per line. |
| 8 | Trade Delta | 3 | Each ocean tile you occupy that touches at least one plains, one forest, and one mountain. |
| 9 | Rainforest | 4 | Each cluster of four mutually connected forest tiles you occupy. Distinct tiles per cluster. |
| 10 | Silk Road | 4 | Each straight line of four adjacent plains you occupy. Distinct tiles per road. |
| 11 | Ocean Corridor | 4 | Each straight line of four adjacent oceans you occupy. Distinct tiles per corridor. |
| 12 | River Flow | 4 | Each chain of adjacent tiles running mountain→forest→plains→ocean. The mountain source may be shared; forest, plains and ocean must be distinct. |

## 2 · Feasibility

| Objective | Pts | Scores for | Mean pts | Verdict |
|---|---|---|---|---|
| Trade Delta | 3 | **49%** | 1.90 | works |
| Coastal Control | 1 | **44%** | 0.58 | works |
| River Flow | 4 | 13% | 0.53 | works |
| Mountain Range | 3 | 12% | 0.37 | works |
| Highland Lake | 2 | 10% | 0.20 | works |
| Mountain Fortress | 3 | 8% | 0.23 | very rare |
| Rainforest | 4 | 2% | 0.09 | very rare |
| **Island Nation** | 1 | **0%** | 0.00 | **unreachable** |
| **Breadbasket** | 2 | **0%** | 0.00 | **unreachable** |
| **Greenway** | 3 | **0%** | 0.00 | **unreachable** |
| **Silk Road** | 4 | **0%** | 0.00 | **unreachable** |
| **Ocean Corridor** | 4 | **0%** | 0.00 | **unreachable** |

## 3 · Why — and it is not the objectives' fault

The five failures are **not** an ownership problem. The shapes do not exist on
the map at all, no matter who owns them:

| Shape, anywhere on the map | Occurrences per game |
|---|---|
| A straight line of 4 plains | **0.00** |
| A straight line of 4 oceans | 0.07 |
| Three mutually adjacent plains | 0.03 |
| An ocean tile with 4 ocean neighbours | **0.00** |

**The map has no geography.** Measured over 30 final maps:

- a tile's neighbours share its terrain **22.9%** of the time; pure chance with
  four terrains is 25.0%;
- **61%** of same-terrain regions are a single tile, 23% are two tiles, and
  regions of four or more are 8%.

The explore rule places a tile matching the *played card's suit* at any space
touching two others. Cards arrive in mixed suits, so terrain is interleaved at
random. The result is salt-and-pepper: no mountain ranges, no forests, no seas.
Every objective asking for **sameness** — a line of one terrain, a cluster of
one terrain — is asking the map for something it structurally cannot produce.

Note which two objectives perform best. **Trade Delta** (49%) and **Coastal
Control** (44%) both ask for **variety** — a tile touching three different
terrains, a plains beside an ocean. On a mosaic map, variety is abundant and
sameness is impossible. That is the whole result in one line.

Also worth noting: a player occupies only **8.1 tiles** on average at game end,
on a map of ~28. Any objective needing four specific tiles is asking for half
your holdings in one shape.

**Redundancy:** Mountain Fortress and Mountain Range are near-duplicates (three
mountains, clustered versus in a line); Breadbasket, Silk Road, Rainforest and
Ocean Corridor are the same idea in four terrains. Six of twelve cards are one
mechanism.

## 4 · What to do

There are two coherent directions, and they are mutually exclusive.

### A · Keep the mosaic map, and rewrite the objectives to reward variety

The cheap option. Cut every sameness objective and replace with variety and
adjacency patterns, which the map produces in abundance:

- a tile of yours touching all four terrains
- a connected line of three tiles, each a different terrain
- your units on all four terrains at once
- a tile you occupy whose neighbours are all occupied by rivals (a salient)
- the longest connected run of your own tiles

Keeps Trade Delta, Coastal Control, River Flow and Highland Lake, which already
work. Costs nothing elsewhere in the design.

### B · Give the map geography, then the current deck works

The interesting option, because it addresses something larger. Make exploring
place terrain in regions rather than at random — for example, *a new tile must
match either the card's suit or a terrain it touches*, or draw tiles from the bag
in pairs. Mountains would then form ranges, oceans would form seas, and Silk
Road and Ocean Corridor would become achievable and evocative.

This changes far more than the objectives. It would give the base game a spatial
character it currently lacks — which is the asymmetry actually missing.

### On asymmetry specifically

The objectives cannot supply asymmetry while every player faces the same
undifferentiated mosaic. Right now players differ only in the cards they drafted
and where they happened to start. The axes the game does **not** currently
differentiate on:

1. **Terrain identity** — the four terrains differ only in stack size and attack
   cost. Nothing rewards *being* a mountain power or a sea power.
2. **Shape** — compact versus sprawling civilizations play identically; nothing
   rewards a long coast or a dense core.
3. **Position** — the starting maps are deliberately symmetric, so no player has
   a different problem to solve from their neighbour.

Option B addresses 1 and 2 at once: geography makes terrain identity meaningful
and makes shape worth pursuing. Option A only decorates the existing uniformity.

**Recommendation:** treat this as a question about the *map*, not the objectives.
If the answer is "the map should have regions", do B and the current deck mostly
survives. If the map is meant to stay a mosaic, do A and cut the deck to six
variety cards — but then accept that objectives are flavour, not asymmetry.
