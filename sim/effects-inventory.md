# Card effects — what exists, what the simulator models, what to build next

## 1 · Every card effect in the rulebook

A card sitting in your **victory row** may be spent on **exactly one** of three
effects, after which it leaves the game — so spending it costs you the end-game
points it would have scored. All 80 cards carry all three; only the strength
changes with rank.

| Rank band | A · card phase | B · map phase | C · any time |
|---|---|---|---|
| 1–5 | meld counts as **+1 card** this trick | land **1 extra cell**, this suit | **2** gold |
| 6–10 | **+1 card**, and wins ties | land **1 extra cell**, any suit | **3** gold |
| 11–15 | meld counts as **+2 cards** | land **2 extra cells**, this suit | **4** gold |
| 16–20 | **+2 cards**, and wins ties | land **2 extra cells**, any suit | **5** gold |

Rulings that go with them: **A** is declared in the card phase, in the open, as
you play your meld, so later players can answer it; it never adds cells to the
map. **B** is one additional *settle* — it may not explore and may not attack.
**C** may be taken at any moment, including mid-payment when feeding falls
short. If two players both spend a ties-winning effect, the higher-ranked card
takes the trick.

## 2 · Currently simulated

| | status | notes |
|---|---|---|
| **Effect C** — gold on demand | **yes** | `USE_EFFECT_C`. Spent when feeding would otherwise starve the player; lowest rank first. Worth 11.6 gold a game at 3 players, used 3.4 times. |
| Fortifying | yes | `USE_FORTIFY`. Attack takes the coin before the unit; settling onto a fortified tile disturbs it. Policy is far too eager — 18.6 gold a game to absorb 2.1 attacks. |
| Re-entry when wiped off the map | yes | |
| Suit mismatch → take gold | yes | Fires <1% of the time. |
| Attack terrain cost, per card | yes | |
| Draft, 3-player suit balance | yes | |
| Upgrades (retire → pay 1 → take a market card) | yes | ~5.6 per player per game. |
| Non-cumulative upkeep, proportional starvation | yes | |

## 3 · Missing

| | why it matters |
|---|---|
| **Effect A** — trick bonus | Changes *who wins tricks*, and the trick decides who places their whole meld and who takes gold. |
| **Effect B** — extra cells | Adds units directly to the map — 47% of final score — and accelerates band progression. |
| **Shifting a unit** | Settling always draws from the reserve, so reserves empty faster than in real play. Distorts band pacing and game length. |
| **Ocean drift** | Free repositioning across ocean; affects terrain majorities and defence. |

**The headline gap:** because only C is implemented, the victory row has just
two uses in the simulator — score it, or cash it for gold. The rulebook's
central tension for the row (*"your score, your war chest and your trick
insurance"*) is **entirely untested**, and the row is ~38% of final score.

## 4 · Recommended order

### 1. Effect A — trick bonus
**Highest balance impact.** Roughly a third of all cards become gold, and over
97% of that is the trick-loser's unused card. A perturbs that flow directly: a
spent card can flip a trick, converting a lost card into a placed one and
denying an opponent the same. It is also the only effect with an interaction
rule (two players both winning ties), so it is the one most likely to hide a
degenerate line. Needs declaration during the card phase, before resolution —
the only change here that touches the round structure.

### 2. Effect B — extra cells
Directly adds population, the largest single scoring route, and empties bands
faster, which feeds straight into the band-redistribution question. Cheap to
implement: it reuses the existing settle path with the suit restriction by rank
band. Implement together with A and the victory row finally has three competing
uses, which is the thing worth measuring.

### 3. Shifting a unit
Not an effect, but the largest remaining rules gap. It changes the reserve
economy: a player can hold ground without spending reserve, slowing band
progression and upkeep. Current numbers on game length and band pacing are
biased by its absence.

### 4. Ocean drift
Cheapest and least consequential. Affects dominance scoring (~15%) and lets a
threatened unit escape. Worth having for completeness once the rest is in.

### Not on the list, but do it anyway
Tune the **fortification policy**. It is implemented but spends 18.6 gold a
game to absorb 2.1 attacks, which is almost certainly wrong and currently
distorts the gold picture more than the missing effects do.
