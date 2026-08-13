# Variable per-tier population limits — simulation

Instead of fixed Plains 3 / Forest 2 / Ocean 1 / Mountain 1 for everyone all
game, the limits grow with the **tile owner's band**: flat at Founding,
everything stackable by Empire, Mountain and Ocean staying low for theme.

Two ladders tested against the v0.21 fixed limits, `limits_test.py`, smart bots,
40 games at 3 players, identical seeds in every column.

| band | flat_wide | gentle |
|---|---|---|
| Founding | P1 F1 O1 M1 | P2 F1 O1 M1 |
| Growth | P2 F2 O1 M1 | P2 F2 O1 M1 |
| Expansion | P3 F2 O1 M1 | P3 F2 O1 M1 |
| Empire | **P4 F3 O2 M2** | P3 F3 O2 M2 |

## The rules gap this found first

The invariant check failed within six games, and it was not a coding bug. A
player stacks four units on Plains at Empire, later **loses a band** to
starvation or attack, and the stack is now over the limit their board grants.

**Resolved: starvation culls.** After you return units for missing food, every
tile holding more than your *new* limit sheds the surplus back to the reserve —
famine hits the crowded places first. Those units refill the reserve, which can
drop the band again, so the cull loops until stable.

Only starvation culls. Combat losses lower your band without emptying your
cities, so a stack can sit above its owner's current limit until the next
famine. Measured, that state exists in about **1% of rounds** — rare enough to
leave alone, and arguably right: losing a battle is not a famine.

See "the rule is dormant" below, which is the more important half of this.

## Results

| | fixed (control) | flat_wide | gentle |
|---|---|---|---|
| rounds per game | 15.1 | 16.1 | 15.3 |
| mean final score | 20.2 | 21.0 | 21.2 |
| **leader minus last** | **15.8** | **19.5** | **17.1** |
| units on map (mean) | 8.4 | 9.0 | 8.6 |
| — leader's units | 10.9 | **12.9** | 11.9 |
| — last place's units | 5.6 | 5.6 | 5.8 |
| units per occupied tile | 1.23 | 1.37 | 1.30 |
| tiles on map at end | 21.1 | 20.2 | 20.4 |
| units killed per game | 12.3 | 12.8 | 12.5 |

### 1. It does what it is meant to do, but the effect is small

Stacking rises from 1.23 to 1.37 units per occupied tile under `flat_wide` —
real, but the map is still overwhelmingly one unit per tile. The reason is that
climbing to Empire takes most of the game, so the wide limits only exist for
the last few rounds. The flat *start* is doing more work than the wide *end*.

### 2. The compounding advantage is real and measurable

This was the thing to watch, and it shows up cleanly:

**The leader gains 2.0 units; last place gains nothing (0.0).** The whole
benefit of the ladder accrues to the player already ahead, because reaching
Empire is what unlocks it. Leader-minus-last widens from 15.8 to **19.5**, a
23% wider final gap.

`gentle` costs a third of that (17.1) by giving Founding a Plains 2 and topping
out at Plains 3 — the early flatness is softened and the late reward is
smaller.

### 3. Almost nothing else moves

Game length, kills, map size and mean score are all within noise. This is not a
balance risk; it is a **feel** change that happens to widen the gap.

One small positive: the 20th-unit end trigger fires in 4 of 40 games under both
ladders and 0 of 40 under fixed limits. Stacking gives players somewhere to put
units late, so the expansion race very slightly re-enters the game.

## 4. The famine cull is a correct rule for a situation that never happens

Once implemented, it never fired. Across 20 games at three players with the
bot's two safety valves (holding back from an unaffordable band, reclaiming
fortification coins) deliberately switched **off**:

| | per game |
|---|---|
| units returned by starvation, all players | **0.1** |
| units culled from over-limit stacks | **0.0** |
| games where a cull cascaded | **0 of 20** |

The reason is upstream of this variant entirely, and it is worth stating on its
own:

| | v0.20 | v0.21 |
|---|---|---|
| units starved per game | 0.00 | 0.04 |
| food owed per game (all players) | 17.2 | 13.5 |
| gold earned per game | 50 | 47 |
| peak gold held | 4.3 | 4.1 |

**Food is a real tax and never a real threat.** It consumes roughly 30% of
income, and peak gold of ~4 shows players are spending nearly everything they
earn — but they always cover the meal first. The rulebook's stated pressure,
"a civilization that expands faster than it earns will starve back down", does
not occur in either version.

That makes the cull rule safe — no death spiral is possible at these numbers —
and it makes the food economy a separate question worth asking: if starvation
is meant to be a threat, the current numbers do not deliver one.

## Reading

`gentle` is the better of the two on these numbers: it captures most of the
stacking, most of the thematic arc, and two-thirds less of the runaway.
`flat_wide` gives the strongest progression feel and the strongest rich-get-richer.

Neither is a clear improvement over fixed limits on numbers alone — the case for
them is thematic and tactile (your board visibly teaching you what your
civilization can now support), which is exactly the sort of thing a simulation
cannot score and a table can. Both are recorded in the variants document.
