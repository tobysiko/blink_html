# Secret map objectives — re-evaluated as push-goals

The earlier review measured **passive emergence** — did the pattern happen to
appear. That was the wrong question. This one measures **deliberate pursuit**: a
bot that knows its secret objective and biases both its meld choice and its
placement toward building it, while still playing the base game.

## 1 · Deliberate feasibility

30 three-player games each, seeking bot versus neutral bot.

| Objective | Pts | Passive | **Seeking** | Verdict |
|---|---|---|---|---|
| Trade Delta | 3 | 43% | **57%** | achievable |
| Coastal Control | 1 | 50% | 38% | achievable |
| Mountain Fortress | 3 | 25% | 25% | hard |
| Mountain Range | 3 | 12% | **25%** | hard |
| Rainforest | 4 | 0% | **14%** | hard |
| Highland Lake | 2 | 12% | 0% | not buildable |
| Island Nation | 1 | 0% | 0% | not buildable |
| Breadbasket | 2 | 0% | 0% | not buildable |
| Greenway | 3 | 0% | 0% | not buildable |
| Silk Road | 4 | 0% | 0% | not buildable |
| Ocean Corridor | 4 | 0% | 0% | not buildable |
| River Flow | 4 | 0% | 0% | not buildable |

Seeking genuinely helps where the target is small — Mountain Range doubles,
Rainforest goes from never to sometimes. **It does nothing at all for the five
line-and-cluster objectives.**

## 2 · The placement constraint — and the number that decides everything

The binding constraint is not the suit rule. It is the **explore budget**.

| | per game |
|---|---|
| Tiles created by all three players | 22.0 |
| ...per player | **7.3** |
| ...per player, of any one terrain | **1.8** |
| Tiles a player occupies at the end | 8.1 |

**A player creates about seven tiles in a whole game — under two of any given
terrain.** An objective asking for a line of four plains is asking for roughly
twice a player's entire lifetime output in that suit, at four chosen positions.
It is not hard; it is off the end of the scale.

That also explains why seeking helped the three-tile targets and not the
four-tile ones: three is within reach of a determined player who also captures
tiles others built; four is not.

**Is the suit rule the right tension?** Yes — but it is currently a *second*
constraint behind a budget that already binds. Two tiles of a terrain per game
means the suit rule almost never gets to be the interesting decision. If the
explore budget rose, the suit rule would become exactly the tension you want:
*"I need a mountain here and I am holding three plains."*

## 3 · Interference — the reason to keep them cheap

Map building is fully public. Every tile you place is visible, and a player
placing their third mountain in a row has announced themselves.

- **Easy to hide:** objectives that use tiles you would want anyway — Trade
  Delta, Coastal Control, anything scoring adjacency or variety. Nobody can tell
  a deliberate Trade Delta from ordinary expansion.
- **Impossible to hide:** anything needing a run or a same-terrain cluster. The
  third tile telegraphs the fourth, and blocking is trivial — a rival explores
  the one space you need, or settles the tile so you cannot own it.

This is a strong argument against long-shape objectives independent of the
budget: even if they were buildable, they would be *counterable for free*, and
the player who drew one would simply be behind.

## 4 · Suggested mechanics

- **Two objectives dealt secretly at the start, keep one.** A single deal is
  pure luck; drafting four is fiddly. Keeping one of two gives a real decision
  on turn zero and lets a player match the objective to their drafted hand.
- **Score at the end, revealed simultaneously.** Continuous scoring would leak
  the objective the moment it first paid, which destroys the hidden information
  and invites blocking. Reveal at scoring, alongside the victory row.
- **Points: 3 to 5, flat.** For scale, a player finishes with 22–26 points, of
  which population is ~12. A 4-point objective is meaningful without swamping
  the game, and flat scoring avoids the current deck's problem where the
  hardest objectives pay most *and* are unreachable.
- **Score once, not per instance.** "Each cluster of three" invites a runaway on
  a big civilization; a single yes/no keeps the objective a goal rather than an
  engine.
- **No penalty for failing.** With a seven-tile budget, failure will be common.

## 5 · A revised set of eight

Design rule, derived from the budget: **an objective may require at most three
tiles of any one terrain, and should prefer adjacency and variety over shape.**

Keeping the four that work:

| # | Objective | Pts | Condition |
|---|---|---|---|
| 1 | **Trade Delta** | 3 | An ocean tile you occupy touching at least one plains, one forest and one mountain. *(57% — the best card in the deck.)* |
| 2 | **Coastal Control** | 3 | Three separate plains–ocean pairs you occupy both tiles of. *(Raised from one pair to three so it is a goal, not a freebie.)* |
| 3 | **Mountain Range** | 4 | Three mountains you occupy in a straight line. *(25% — the hardest thing that is still reachable.)* |
| 4 | **Rainforest** | 4 | Four connected forest tiles you occupy. *(14% — keep as the deck's stretch goal.)* |

Four replacements, built on variety and shape-of-holding rather than terrain runs:

| # | Objective | Pts | Condition |
|---|---|---|---|
| 5 | **The Four Winds** | 4 | You occupy at least one tile of every terrain. |
| 6 | **Crossroads** | 3 | A tile you occupy whose six neighbours include all four terrains. |
| 7 | **The Long March** | 4 | Six of your tiles in one connected chain. *(Rewards shape without requiring terrain.)* |
| 8 | **Salient** | 5 | A tile you occupy with at least three neighbours occupied by rivals. *(Rewards pushing into contested ground — the only objective that pulls a player toward conflict.)* |

Cut: Island Nation, Breadbasket, Greenway, Silk Road, Ocean Corridor, River Flow,
Highland Lake, Mountain Fortress. The first six are unbuildable; Highland Lake
depends on terrain a player cannot arrange; Mountain Fortress duplicates
Mountain Range.

## The larger point

Eight objectives at 3–5 points each will add texture, but they will not carry
asymmetry on their own, because **every player is still building on the same
undifferentiated mosaic with the same seven-tile budget.** The two levers that
would make objectives matter are the same two from the previous review:

1. **Raise the explore budget** — more tiles created per player would make the
   suit constraint the interesting decision rather than a formality.
2. **Give the map geography** — if exploring placed terrain in regions, the
   cut objectives would become buildable *and* evocative, and terrain identity
   would start to mean something.

Objectives are the right vector for asymmetry. They cannot deliver it at a
budget of 1.8 tiles per terrain per game.
