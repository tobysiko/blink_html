# Gap report — rulebook against simulator, both directions

Produced after switching to **2/4/6/8** bands. Every claim below was checked
against the built rulebook text and `sim/engine.py`, not from memory.

---

## Part 2 first: the effect-scaling defect needs no fix

I reported that Effect A inverts at the band 2→3 boundary — rank 6–10
(+1, wins ties) took the trick 88.2% of the time against rank 11–15's 86.4%.
Two things have since changed that finding.

**The measurement was taken under open declaration.** Re-run under the blind
declaration now in the rules, the ordering is 6–10 at 62.5% and 11–15 at 58.1%
— but on sample sizes of 16 against 186, which is not a comparison at all.

**And that sample imbalance is the real answer.** Measuring what actually
reaches a victory row over 25 games:

| Rank band | still in the row at the end | spent on an effect |
|---|---|---|
| 1–5 | **0.0%** | **0.0%** |
| 6–10 | 0.0% | 18.9% |
| 11–15 | 60.4% | 79.1% |
| 16–20 | 39.6% | 2.0% |

**Bands 1–5 never reach the victory row, and 6–10 only pass through it.** The
market deals only advanced cards — ranks 11–18 at three players — so a low card
can enter the row *only* by being retired out of a starting hand, and retiring
a high card scores far more.

Within the range that actually occurs, **11–20, scaling is already clean**:

| | 11–15 | 16–20 | monotone? |
|---|---|---|---|
| A | +2 cards | +2 cards, wins ties | yes |
| B | 2 cells, own suit | 2 cells, any suit | yes |
| C | 4 gold | 5 gold | yes |

**Could a player force low cards into the row?** Only by retiring low, and that
loses: over 40 games a seat retiring its lowest card scored **19.4** against
23.7 and 23.0 for seats retiring high (32% wins against 35% and 32%). It does
populate the row with bands 1–2 (97% of its kept cards), so the defect is
reachable — it is just reachable only by playing worse.

**Recommendation: change nothing.** The defect is real on paper and sits in a
region of rank space the game does not visit. Any rule extending tie-winning to
11–15 would make the printed card faces under-state their own effect, which is
the component-contradicts-the-book error this project has already been bitten by
twice. Revisit only if the market is ever changed to sell low cards.

---

## Part 3a · Rules → sim: what the rulebook says that the sim does not model

| § | Rule | Status in the sim |
|---|---|---|
| 06 | **Shift** — settle by moving a unit already on the map instead of drawing from the reserve | **Not modelled.** Settling always draws from the reserve, so reserves empty faster than in real play. Biases game length, band pacing and upkeep. *Largest remaining gap.* |
| 07 | **Ocean drift** — move any number of units freely across unoccupied Ocean at the end of your map phase | **Not modelled.** Affects terrain majorities (~20% of score) and lets threatened units escape. |
| 06 | A unit may be shifted from *any tile connected to your population*, not merely an adjacent one | Not modelled (follows from shift being absent). |
| 06 | Leaving a tile empty by shifting its last unit away, **splitting your civilization in two** | Not modelled. The sim's civilizations are always contiguous by construction. |
| 09 | Upgrading is available "at any time during your map phase, as often as you can afford" | Modelled, but gated behind a 35% random willingness rather than a considered decision. |
| 05 | A meld "may always be shorter than your limit — the limit is a ceiling, never a quota" | Modelled implicitly (all sizes are enumerated) but no bot ever deliberately plays under its limit to bank gold. |
| 06 | Take gold "at either end of a straight, or any card of a set" | Modelled only as an all-or-nothing fallback when no placement exists. Partial voluntary skipping is never chosen. |
| 04 | Initiative dice | Not modelled as objects; initiative order is recomputed each round. No behavioural difference. |
| 10 | "Finish the current round, then play one more full round" | Modelled. |
| 03 | Homeland tile | Correctly absent — cut from the rules. |

## Part 3b · Sim → rules: what the sim does that the rulebook does not say

| Sim behaviour | Rulebook position | Verdict |
|---|---|---|
| **Explore legality is judged against the map as it stood at the start of the placement** | Silent | **Genuine gap.** If an earlier cell of the same meld places a tile, a later cell's legality could change. The sim takes the conservative reading. The rules should say which map you check against. |
| **A tile cannot be created when the box has none** — an explore with no matching tile anywhere takes gold instead | §06 says "if the bag is also empty of that suit, the card takes gold instead" | **Covered.** This is exactly the rule; the sim needed a bug fix to obey it. |
| **A fortification coin cannot outlive its unit** — pulling a unit off by starvation trims stray gold | §07 says the gold is lost when the unit is "disturbed in any way" | Covered, though "disturbed" is doing a lot of work. Worth naming starvation explicitly. |
| **Settling onto a fortified tile clears the coin** | §07 lists "stacked onto" | Covered. |
| **A meld with no legal placement at all converts every card to gold** | §06 states it | Covered. |
| **The trick loser chooses which card to drop** | §04 says they use one card fewer; §06 says what lands must be legal | Rules do not say *who* chooses or how. The sim picks at random among legal drops. **Minor gap** — presumably the player chooses. |
| **Initiative below the winner** follows the same tie-break chain | §04 states it | Covered. |
| **Upkeep is paid at the very end of that player's turn, after upgrades** | §08 states the order explicitly | Covered. |
| **Returned units fill the lowest band with a free slot** | §08 states it | Covered. |
| **Proportional starvation** — one unit per gold short | §08 states it | Covered. |
| **Effect B places settles only, never explores or attacks** | §09 states it | Covered. |
| **Two players declaring tie-winning: higher-ranked spent card wins** | §09 states it | Covered. |
| **Effect A is declared blind, before any meld** | §04 declare step | Covered. |
| **Bots never fortify outside their own map phase** | §07 restricts it to your own map phase | Covered. |

### The three that need a rulebook decision

1. **Which map does explore legality check against?** The sim assumes the state
   at the start of the placement. The alternative — re-checking after each cell —
   is more permissive and would let a meld's own tiles enable later cells.
2. **Who chooses the dropped card when you lose a trick?** Certainly the player,
   but the rules never say so, and with two-set melds the choice matters.
3. **Does starvation count as "disturbing" a fortified unit?** The sim says yes.

---

## Confidence in the findings, given the gaps

The two unmodelled rules — **shift** and **ocean drift** — both make units
*cheaper to keep on the map*. Their absence means the sim consumes reserves
faster than real play, so:

- **game length is understated** (fewer rounds than a real table would take),
- **upkeep pressure is overstated** (you climb the bands faster),
- **dominance scoring is understated** (drift is a majority tool).

Everything about the card economy, the trick, the meld ladder and the victory
row is unaffected by those two gaps.

---

# Update — the three sim gaps are filled

`USE_SHIFT`, `USE_DRIFT`, `USE_HOLD_BACK` (all default on) and
`DISCONNECT_PENALTY` (default **off** — see the conflict note below).

| configuration | rounds | upkeep | starved | shifts | drifts | held back | settles | pop/row/dom |
|---|---|---|---|---|---|---|---|---|
| none of the three | 18 | 21.9 | 0.1 | 0.0 | 0.0 | 0.0 | 45.9 | 58/21/21 |
| + shift | 18 | 21.7 | 0.1 | 0.3 | 0.0 | 0.0 | 45.9 | 55/24/21 |
| + shift + drift | 18 | 21.4 | 0.3 | 0.6 | 3.5 | 0.0 | 46.6 | 59/20/21 |
| **all three** | 18 | **16.9** | 0.0 | **9.3** | 2.2 | 0.2 | **37.9** | 52/27/21 |

**Game length did not move at all** — 18 rounds throughout. I had predicted the
sim was understating length because it consumed reserves too fast; that was
wrong. Shifting recycles units rather than adding them, so it does not delay the
end trigger.

**Upkeep pressure fell 23%**, 21.9 → 16.9 gold a game, and that is the real
finding. But note it only appears when all three are on. Shift alone is used
0.3 times a game; combined with hold-back it jumps to **9.3**. The two are one
mechanism: a player who is about to empty a band and cannot afford the next one
either shifts a unit across instead of spending a fresh one, or takes the gold.
Settles drop 45.9 → 37.9 accordingly — a fifth of all placements are now
recycled units rather than new ones.

**Dominance scoring did not change** — 21% in every configuration. Drift fires
3.5 times a game but moves units *between* ocean tiles, so it never changes how
many units a player has on ocean. It is a repositioning and escape tool, not a
majority tool. My earlier claim that the sim understated dominance was wrong.

**The victory row gains** — 21% → 27%, because gold not spent on upkeep is
available for upgrades.

## Two conflicts with the rulebook, flagged rather than implemented

**Shift.** You described "move one unit to an adjacent tile, paying the terrain
cost". §06 says a shifted unit comes "from any tile connected to your
population", with no cost: *"Shifting costs you nothing from the reserve but
grows nothing either."* I implemented the rulebook version. Your version is a
real change — a source restriction plus a new cost — and would need §06 rewritten.

**Disconnection.** You described units on a severed fragment being removed. The
rulebook says the opposite in two places: §06 — *"You may leave a tile empty by
shifting its last unit away — splitting your civilization in two is allowed"* —
and §07 — drift *"may leave its origin tile empty and may break your
civilization into unconnected pieces."* This would be a new rule, not a gap.

Implemented behind `DISCONNECT_PENALTY` so you can see it:

| | rounds | upkeep | settles | units culled | pop/row/dom |
|---|---|---|---|---|---|
| all three | 18 | 16.9 | 37.9 | — | 52/27/21 |
| + disconnect penalty | 18 | 15.7 | 38.6 | **5.1/game** | 49/26/**26** |

It kills 5.1 units a game — a quarter of a player's twenty — and pushes
dominance from 21% to 26%, because holding a compact block becomes the only safe
shape. That is a substantial change in what the game rewards, and it makes the
"two-set melds may land in two places" rule dangerous rather than exciting.

---

# Conflicts closed

**Shift cost** — §06 stands: a shift is free and may come from any tile
connected to your population. No rulebook change, no simulator change.

**Disconnection** — §06 and §07 stand: splitting a civilization is allowed and
fragments survive. The speculative `DISCONNECT_PENALTY` toggle and its
`_cull_fragments` code have been **removed from the engine entirely**, rather
than left switched off. Speculative mechanics sitting dormant in a simulator are
how a sim drifts from its rules, which is the failure this report exists to
catch.

## Knock-on found while closing them

Switching to 2/4/6/8 broke two statements in the tutorial, and a third error had
survived from earlier:

1. *"Everyone's board is full, so nobody has emptied a band yet"* — the board is
   not full after setup, and with Founding holding two units the point is now
   the opposite: the band is nearly gone before play starts.
2. *"Emptying your top band raises your meld limit to 3 … worth doing, but not by
   accident"* — under 2/4/6/8 it is not a choice. Setup spends one of Founding's
   two units, so the first unit you settle clears the band whether you meant to
   or not.
3. *"the bill grows faster than the reward"* — the cumulative-upkeep claim. It
   was corrected in the rulebook when upkeep was fixed, but the tutorial copy
   was missed at the time.

All three are fixed. Worth noting the pattern: every band or upkeep change so
far has required a tutorial edit that was not obvious from the rulebook diff.
