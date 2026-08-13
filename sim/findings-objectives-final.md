# Final objective set — three-tile patterns only

Seeking bots, 62 three-player games, ~31 samples per objective.

| Objective | Pattern (all three tiles must be OCCUPIED) | Achieved | Points |
|---|---|---|---|
| **River Delta** | ocean → plains → forest, in a chain | **52%** | 4 |
| **Highland Rivers** | mountain → forest → ocean, in a chain | **45%** | 4 |
| **Coastal Chain** | plains → ocean → plains, in a chain | **42%** | 4 |
| **Mountain Range** | three mountains in a straight line | **26%** | 5 |
| **Mountain Fortress** | three mountains, each touching the other two | **19%** | 5 |
| **Deep Wood** | three forest, each touching the other two | **13%** | 5 |

Difficulty tracks the explore budget by suit almost exactly — mountain 7.5
tiles created per game, ocean 6.2, forest 5.8, **plains 2.4**. Chains that use
plains as a middle link are easy because plains tiles already exist as everyone's
starting ground; single-terrain triangles are hard because they need three tiles
of one suit, and the budget for any one suit is under two per player.

## Cut, and why

| Dropped | Reason |
|---|---|
| Silk Road, Ocean Corridor, Greenway, Rainforest (4-tile) | four or more tiles — outside the budget, 0% even when pursued |
| Island Nation | needs an ocean with four ocean neighbours; occurs 0.00 times per game on the whole map |
| Breadbasket | plains triangle, 0–18%. Plains is the scarcest explore |
| Archipelago (ocean triangle) | 0%. Ocean holds one unit, so it needs three separate units on three adjacent oceans |
| Highland Rivers / River Delta as straight lines | 22% each — tighter than the triangles they would sit beside |
| Crossroads (three adjacent, all different terrains) | 89–91%. On a mosaic map, variety is nearly automatic |
| Frontier (three tiles touching rivals) | 90–100%. Same problem |
| Highland Lake, Trade Delta, River Flow (originals) | superseded by the two new river cards |

## Note on sample size

An earlier pass ran twelve candidates over 36 games — nine samples each — and
produced swings of 40 percentage points between runs (Mountain Range read 64%
then 22%). The numbers above use six candidates over 62 games for ~31 samples
each. Anything below about 25 samples per objective is not measuring anything.
