# v0.22 — corrections needed after the app/sim/document audit

Four places where the rulebook, the player board and `sim/engine.py` disagreed.
Decisions taken 12 Aug 2026; `app/` now implements all four. Line numbers are in
`source/Blink-rules-v0.22.html`.

---

## 1 · Trick resolution — REVERT to the classic rule

**Decision:** the trick winner uses every card of their meld. A player who
matched the winner's card count sets **one played card aside**, unused — it
earns **1 gold** instead of a map action. Playing fewer than the winner costs
nothing. No winner bonus card; no face-down discard to the shared pile.

**Rulebook now says the opposite** and must be rewritten:

- **lines 408–422** — the three bullets under "The round then settles three
  ways". Delete "The trick winner spends one extra card" and "Anyone who
  matched the winner's card count and still lost discards one card… face down,
  to the shared discard pile". Replace with the set-aside rule above.
- **line 408** — "Everyone spends every card of their meld. Nobody is docked a
  card" is now false for a player who matched the winner.
- **lines 465–470** — the "Losing the trick costs you almost nothing" note
  describes the old costs.
- **lines 787–790** — the worked example: Ada matched Bex and *discards from
  hand*; under the new rule she sets one of her two played cards aside and takes
  a coin for it.
- **lines 914–918** — the round summary at the back.
- **line 685** — *already correct again.* "Losing a trick pays you a gold per
  unused card" was stale text from the pre-v0.22 rule; the revert makes it true.
  This contradiction is what surfaced the whole audit.

**Open question:** does the last-ranked meld still take 1 gold? That catch-up
coin arrived with the rule just reverted. The app still pays it (line 417 of the
rulebook stands); say so either way.

**Measured cost of the revert** (300 games per player count, bots only):
games run **20–25% longer** — 3p goes 14.5 → 17.5 rounds — because fewer cards
reach the map each round. Cards cashed for gold rise 21 → 28, which funds
roughly double the fortifying (6.8 → 12.8). Kills fall slightly, 15.7 → 13.3.

---

## 2 · Victory row — the SIM is right, the rulebook is wrong

**Decision:** the row scores **1 per card, plus the centre-slot rank** once it
holds three. Unchanged in the app.

**Rulebook §13 says centre slot alone** and must be corrected:

- **line 844** — "If you have three or more, score the rank in the centre slot"
  → score **1 point per card plus** the rank in the centre slot.
- **lines 852–855** — the worked table is wrong in three of four rows:

  | row | printed | correct |
  |---|---|---|
  | 2 cards — 9, 17 | 2 | 2 |
  | 3 cards — 6, 9, 17 | 6 | **9** |
  | 4 cards — 6, 9, 14, 17 | 9 | **13** |
  | 5 cards — 6, 9, 14, 16, 17 | 14 | **19** |

- **line 858** — "With fewer than three cards you score 1 point each instead"
  → the per-card point is not an *instead*, it is always there.
- **line 848** — the figure captions read "Three cards — centre slot scores 3"
  and "Five cards — centre slot scores 11". Still true of the centre slot, but
  the row's total is now 3+3=6 and 5+11=16; caption or figure should say which
  number it is showing.

Measured: the correction is worth about **+1 point per card in the row** — 2.5
points at 3 players, and the row's share of the final score goes 38% → 42%.
Nothing about how anyone plays changes.

---

## 3 · Tier unit counts — the BOARD is right, the sim was wrong

**Decision:** **2 / 4 / 6 / 4 / 4**, as printed on the player board and in §04.
The app has been changed to match; `sim/engine.py` still has 2/4/5/5/4.

No document change needed. Measured difference: none detectable — score 37.6 vs
37.2, population 17.4 vs 17.3, rounds 14.5 vs 14.5, mean meld size identical.

**`sim/engine.py` line 53–57** should be updated so future simulation runs match
the components.

---

## 4 · Rank caps — the SIM is right, board and rulebook must be reprinted

**Decision:** **11 / 13 / 15 / 17 / 20**, one tier tighter than printed.

- **rulebook line 351–355** — the Rank cap column reads 13 / 15 / 17 / 20 /
  none. Should be 11 / 13 / 15 / 17 / 20.
- **`source/board_a4.svg`** (and `-bw`, and the PDFs built from them) — the cap
  numbers at `x="274"`: lines 28, 42, 60, 78 read 13, 15, 17, 20. Should be 11,
  13, 15, 17, with **20** added on the Civilization row, which currently prints
  no cap at all.

This is the one discrepancy that changes play. With the printed caps:

| 3 players, 300 games | caps 11/13/15/17/20 | caps 13/15/17/20 |
|---|---|---|
| upgrades per game | 29.6 | **35.7** |
| buys blocked by the cap | 5.1 | **1.8** |
| research declined as unwinnable | 7.9 | **1.8** |
| rounds | 14.5 | 13.4 |
| population | 17.4 | 17.9 |

The printed caps remove about two-thirds of the friction the cap exists to
create, and shorten the game by a round.

---

## Reproducing any of this

From `app/`:

```
node verify.js bonus     # v0.22-as-printed trick rule (matches the Python sim)
node verify.js dock      # the classic rule, now the default
node vrow_test.js        # victory row, both readings, matched seeds
node tier_test.js        # tier units and rank caps, four combinations
```

---

## 5 · Effect D — playable, and it dominates

`Blink-deck-with-D.html` is implemented as a **deck toggle on the setup screen**
(A/B/C base, or A/B/D proposal). D replaces C exactly as the document specifies,
including removing the row as a famine valve — with A/B/D there is no take-gold
effect, so gold comes only from cashing a hand card, ascension, and last place.

**Measured, bot-only, 300 games per player count, classic trick rule:**

| 3 players | A/B/C | A/B/D |
|---|---|---|
| final score | 38.6 | **26.9** |
| victory row points | 16.3 | **7.0** |
| kills | 13.5 | **51.1** |
| effect B used | 4.7 | **0.8** |
| third effect used | 4.1 (C) | **21.2 (D)** |
| ground taken by D | — | 35.8 |

4 players: score 30.0 → 20.7, row 10.8 → 3.7, kills 27.8 → 64.3.
2 players is mildest: 45.1 → 38.8, row 19.7 → 14.4.

**This is not a bot artifact.** Three different D policies were tried and the
conclusion held under all three:

1. **B's four-card guard** — D took ground **0 times in 900 games**. A row does
   not reach four cards until late, and by then the reserve is empty, so the
   settle step always failed. The effect measured dead because it was asked too
   late, not because it is weak.
2. **No guard** — D fired 18–24 times a game, B never fired, the row scored 1,
   and table scores halved.
3. **Priced against the row** (`gain > _rowCost`), denial counted at half a
   point because a kill takes a point off a *rival* rather than adding one to
   you — the numbers in the table above.

The reason is structural: a settling strike is **+1 to you and −1 to a rival for
a card worth about 1 point**, so it is never worse than holding the card and
usually better. Every retired card wants to become a strike, the victory row
stops being a scoring track, and because everyone does it all scores deflate. It
scales with player count, because more rivals means more adjacent targets.

**Two specification problems found while implementing it:**

- **The top band's extra clause is a no-op.** 16–20 reads "remove 2 rival units
  from ANY tiles you can reach", against "a tile touching your civilization" for
  1–15. But *reach* is defined in §06 as a tile you occupy or one adjacent to
  it — which for rival tiles is exactly "touching your civilization". As written
  Overrun grants nothing over Conquer except the wording.
- **D ignores the terrain attack cost.** A card spent attacking pays
  0/0/1/2 gold by terrain (§06). D pays nothing, so conquering a Mountain is
  free while attacking one with a card costs 2. Deliberate or not, it is one of
  the reasons D is the cheaper way to fight.

**Levers, if you want D but not this:** charge the terrain attack cost; let
fortifications block a strike outright instead of absorbing it; restrict
settling to ranks 11+; or cap D at one card per *game* rather than per turn.
Each is a one-line change in `app/engine.js` and can be measured with
`node deck_test.js`.

---

## 6 · Endgame audit — one bug, one dead rule, one non-issue

### 6a · The game ran ONE ROUND TOO LONG — fixed

§11: *"Finish the current round, then play one more full round."* The trigger is
checked at the **end** of a round, so the current round is already finished and
exactly one more should follow. Both engines had:

```js
finalRounds = round + 1;
finished()  = round > finalRounds;     // plays TWO more rounds
```

Measured: **2.00 extra rounds after the trigger in 200 of 200 games.** Fixed to
`>=` in the app. `sim/engine.py` has the identical off-by-one, so **every figure
ever measured in this project includes an extra round** of placements, research
and scoring.

Cost of the fix, 3 players: rounds 17.7 → 16.7, score 38.6 → 37.5.

### 6b · The rulebook's dominance rule is almost unachievable

§13: *"3 points for each terrain where you have the most units — but only if all
your units on that terrain form a single connected group."* The sim instead
scores your **biggest connected stretch** of a terrain, counted in tiles.

| dominance points, 300 games | sim: biggest stretch | rulebook: most units, all connected |
|---|---|---|
| 2 players | 6.33 | **0.45** |
| 3 players | 4.30 | **0.27** |
| 4 players | 3.25 | **0.23** |

The "all your units" clause is the problem: by the end a player holds 15–18
units across a 40-tile map, and *one* stray unit of that terrain anywhere
disqualifies the whole terrain. As printed, dominance is worth about a quarter
of a point — it stops being a scoring track at all, and the ~11% of the score it
is supposed to carry silently vanishes.

The app keeps the sim's reading (`majority:'area'`); pass `{majority:'units'}` to
`playOut` to reproduce the table.

### 6c · Market size — 6 or 9, it does not matter

§03 and §10 print a **2 × 3 market of six**; the sim uses **3 × 3 of nine**.
Measured at nine vs six: score 37.45 vs 37.63, rounds 16.68 vs 16.57 at three
players — no detectable difference. Match whichever the components print; the
app takes `{gridSize: 6}`.

Note the second end trigger also differs in wording: §11 says the deck runs out
*and a grid position cannot be refilled*; the app ends when the grid is down to a
single layer. It fires 1–6% of games either way, so it is not worth chasing until
the market size is settled.

---

## 7 · Effect D now pays the terrain attack cost

Conquest pays the same price a card attack does — 0 Plains, 0 Ocean, 1 Forest,
2 Mountain — and a target you cannot afford is not offered. This changes the
character of A/B/D but not the verdict, 3 players:

| | A/B/C | A/B/D, free | A/B/D, paying terrain |
|---|---|---|---|
| score | 38.6 | 26.9 | **25.4** |
| victory row | 16.3 | 7.0 | **5.5** |
| kills | 13.5 | 51.1 | **56.9** |
| cards cashed for gold | 28.3 | 34.8 | **55.6** |
| units starved | 0.0 | 0.0 | **0.87** |
| rounds | 17.7 | 18.4 | **22.3** |

The price does not stop D — it funds it by forcing players to cash far more
cards, which is why the game runs five rounds longer. **It is the first
configuration in this project where anyone starves at all**, so if you want the
food ladder to bite, this is the combination that does it.

---

## 8 · Map objectives — implemented, and re-measured

`Blink-map-objectives.html` is in as a setup option with all three modes from the
module: **secret** (deal two, keep one), **open** (two face up, shared), and
**keep both**. Scoring is 4 points, once, and every tile of the chain must be one
you occupy.

The module says its figures need re-doing because it was balanced against v0.20
pattern placement, where completion ranged 1–28% and Mountain Pass, Coastal
Chain and Clearing "have all but stopped happening". **Re-measured passively on
the current engine** — bots do not steer, 500 games at each player count:

| objective | chain | completed |
|---|---|---|
| Foothills | M–F–P | **55.0%** |
| Highland Rivers | M–F–O | 43.3% |
| Watershed | M–P–O | 41.8% |
| Riverbank | P–F–O | 35.4% |
| Timberline | F–M–F | 34.7% |
| River Delta | O–P–F | 33.9% |
| Fjord | M–O–M | 29.6% |
| Mountain Pass | P–M–P | 21.4% |
| Clearing | F–P–F | 21.4% |
| Mountain Lookout | O–M–O | 20.3% |
| Sheltered Water | F–O–F | 19.4% |
| Coastal Chain | P–O–P | **13.0%** |

Overall 36.3% at two players, 32.0% at three, 27.1% at four.

Two things fall straight out of the ordering:

- **Asymmetric chains are easier than symmetric ones.** The top six all ask for
  three different terrains; five of the bottom six are X–Y–X. A chain of three
  different terrains has far more ways to match, and needs only one tile of each.
- **Ocean in the middle is the hardest position.** Coastal Chain and Sheltered
  Water are last, and both need an *occupied* Ocean between two occupied tiles —
  Ocean holds one unit, so the middle of the chain costs a whole tile's capacity.

So the flat 4 points still is not flat: the spread is 4.2× rather than the
module's 28×, which is a large improvement, but Foothills is worth roughly four
Coastal Chains. If you want them level, the lever is the *points*, not the
patterns — or drop the three symmetric stragglers and print nine.

Reproduce with `node objectives_test.js`.
