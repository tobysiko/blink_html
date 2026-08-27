# v0.22 — corrections after the app/sim/document audit

**Status: applied to the documents on 14 Aug 2026.** Every item below is now in
the printed rulebook, the tutorial, the playtest sheet and the player board.

The rulebook is **generated** — do not edit `source/Blink-rules-v0.24.html`. The
sources are `source/build_html.py` (rules), `build_tutorial.py` (first game),
`build_playtest.py`, `build_figs.py` (figures) and `board_a4.py` (the board);
`source/build_pdfs.sh` runs the lot and renders the PDFs with wkhtmltopdf.

`source/check_rules.py` now runs in that build and **fails it** if the printed
numbers stop matching `app/engine.js` — tier units, meld limits, free moves,
food, rank caps, ascension coins, the trick, the retire rule, effect B's reach,
the market size, the terrain table, and the unit slots drawn on the board. Each
of its checks was verified to fail when the corresponding number is mutated.

Line numbers below refer to the generated HTML as it stood during the audit and
are kept only as a record of where each fault was found.

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

**Answered 14 Aug 2026: the catch-up coin stays.** The last-ranked meld takes 1
gold whatever the player count, as the app has always paid it. §04 now also says
what happens when one player is both last and a matcher: they take both coins.

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

Measured difference: none detectable — score 37.6 vs 37.2, population 17.4 vs
17.3, rounds 14.5 vs 14.5, mean meld size identical.

**Applied.** `app/engine.js`, `sim/engine.py` and both rulebook mentions (§03
setup and the §04 tier table) now agree, and so does the tutorial. The old
2/4/5/5/4 also summed to 20, which is why the mismatch survived so long;
`check_rules.py` now counts the unit slots drawn on `board_a4.svg` row by row
and fails the build if any of them drifts.

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

**Applied.** The tier table, the §10 buying step and the quick reference all
read 11 / 13 / 15 / 17 / 20, and `board_a4.py` prints a cap on every row
including Civilization, which previously printed none.

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

---

## 9 · Research — the draw is no longer placed by the player

**Decision:** research is **two decisions**: give up a card from hand, take one
from the market. Drawing the top of the upgrade deck and placing it is
**automatic** — it lands on the position showing the **highest rank**, burying
it. Ties break to the leftmost position so the rule is deterministic.

**Rulebook §10 must be rewritten.** It currently reads "Draw the top of the
upgrade deck onto a grid position of your choice". Placement is not a choice.

`app/` implements this for humans and bots alike; `sim/engine.py` still has
`_pick_grid_slot`, where the bot buries whichever position it values least.

**What it does to the market.** The tallest visible card is always the one
covered, so the top of the market keeps sinking out of reach — a second brake on
high ranks alongside the rank cap, and one nobody can steer. Measured against
the old chosen placement, 3 players:

| | player/bot chooses | automatic, highest rank |
|---|---|---|
| final score | 37.5 | **36.2** |
| victory row | 15.9 | **14.3** |
| rounds | 16.7 | **15.7** |
| kills | 12.4 | **9.8** |

The row loses about 1.6 points and the game shortens by a round: burying the
tallest card slows everyone's climb through the market, so fewer tall cards
reach a victory row.

**Why it is better at the table.** The old step asked a player to make a
tactical decision about a card they had not yet seen the consequences of, with
no legible reason to prefer one position — it was the step most likely to be
clicked at random. Removing it costs a decision nobody was making well and
gains a rule everyone can predict.

---

## 10 · The shared pile was never fed — the classic rule cut §09 off at the tap

**Decision:** the card a matcher sets aside goes **face down to the shared
pile**, not to that player's own discard. It still pays 1 gold, and it is now a
**forced** step: matching the winner's card count costs you a card, and the only
decision is which one.

**This was a live bug, not a preference.** §09 promises that "cards you lose
flow into the shared pile, and cards other players lost flow back to you". Under
the classic trick rule (item 1) nothing ever entered the pile: the set-aside
card went into the player's personal discard and came straight back to them at
the next recycle. Measured over 300 bot games, 3 players:

| | before | after |
|---|---|---|
| cards drawn from the shared pile, per game | **0.00** | **13.43** |
| cards in the pile at the end | 0.0 | 0.6 |
| recycles per game | 6.9 | 9.4 |
| rounds | 14.0 | 15.8 |
| final score | 38.4 | 36.2 |
| victory row | 16.2 | 14.5 |
| hand size at the end | 5.3 | 4.5 |

Every seat's ten drifts now, which is what §09 says the game does. The knock-on
is that hands empty sooner (a card leaves your economy instead of circling back)
so you recycle 37% more often, pay food more often, and the game runs about a
round and a half longer.

**Rulebook change:** §04's third bullet currently describes the *printed* rule
(a card from hand to the shared pile). Under the reverted rule it must read: a
player who matched the winner's count **sets one played card aside, face down,
onto the shared pile, and takes 1 gold for it**. §09 needs no change — it
already describes the pile correctly; it simply had nothing to describe.

**Also worth printing:** the shared pile is a component players can see and
count. The app now shows it beside the upgrade deck with its size on it, and
cards visibly travel to it and out of it.

---

## 11 · Research retires your LOWEST card — a proposal, and it is expensive

**The rule as printed.** §10: "Retire one card from your hand **or discard**
into your victory row." No restriction on which. Note the app has never
implemented the *or discard* half — it offers the hand only, and so does
`sim/engine.py`. That is a separate gap and should be either implemented or cut
from §10.

**The proposal:** research may retire only the **lowest rank you hold**, every
copy of it — so the decision is which suit to give up, not whether to feed a
high card into the row for points. Research becomes an upgrade in the plain
sense: your worst card leaves, a better one arrives.

It is implemented as a **setup option** (`Research retires: your lowest card /
any card`) and defaults to lowest, so both can be played. Measured over 300 bot
games with the shared pile in place:

| | any card | lowest only |
|---|---|---|
| 2p final score | 43.6 | **38.8** |
| 2p victory row | 18.2 | **14.0** |
| 3p final score | 36.2 | **30.5** |
| 3p victory row | 14.5 | **9.2** |
| 4p final score | 27.8 | **24.1** |
| 4p victory row | 8.9 | **5.5** |
| upgrades per game (3p) | 33.1 | 33.3 |
| population (3p) | 17.3 | 16.9 |

**ADOPTED 14 Aug 2026, and the measured cost above is a floor, not the truth.**
The figures come from bots that research the moment they can afford it, and
"your lowest card" is not a constant — it climbs as you empty your hand. Measured
over 200 games, the rank a bot gives up depends entirely on when it researches:

| hand size when researching | mean rank retired |
|---|---|
| 6–10 cards | **6.0** |
| 3–5 cards | 7.9 |
| 1–2 cards | **12.0** |

A quarter of all retires are still rank 11 or higher. So the rule does not keep
strong cards out of the victory row — it makes them cost **patience**: hold the
card, play the rest of your hand down, and research when it is the lowest thing
you have left. A high card can never be bought off the market and parked
straight into the row; it has to be lived with first. That is the theme the rule
exists to protect — a gradual ascension of technologies replacing old ones — and
the bots cannot play it, which is precisely why they measure it so badly.

§10 now prints the restriction, and a note beside it points at the timing
decision. **The "or discard" half of §10 is cut** — no code has ever implemented
it, and retiring from the discard would sidestep the hold-back tension entirely.

The compensation lever remains available if human play shows the row is too
weak: score the **highest** card in the centre slot rather than the
third-highest. Not applied, and it should not be applied without games behind
it.

---

## 12 · Effect B ignored reach — and §10 contradicts the effect table

**Two implementation faults, now fixed.**

**a. A colony could be founded anywhere on the map.** Founding a colony is an
*explore*, so §06 applies in full: the space must touch two tiles already on the
map **and be in your reach**. The engine applied only the touch-two half.
Measured over 200 bot games, **58% of colonies landed outside their founder's
reach** — mean 2.2 steps away, as far as 8, and one on a disconnected fragment.
The 6–10 band's printed exception, *"found a distant colony — as above, up to 2
tiles out"*, was not implemented either; it is now the only band that reaches
further than one.

Measured cost of the correction: none detectable (3p score 30.4 → 31.1,
colonies per game 6.1 → 6.1). The bot does not care where its colony lands. A
player does, which is the second fault.

**b. Nobody chose where the colony went.** The engine placed it on the
lowest-sorted cell — an arbitrary corner. A person now picks every cell, and the
terrain too for the 16–20 band, and may stop early.

**A rulebook contradiction to settle.** §10's prose says of B:

> "each extra unit is one additional **settle**, within your normal reach — it
> may not explore and may not attack."

But the effect table on the same page says every B band lays **new tiles**:
"Found a colony — 1 new tile of this suit, 1 unit, fortified". Those cannot both
be true. The app implements the table, which is also what the effect is worth
paying a victory card for. The sentence in §10 reads like the pre-v0.22 B (extra
settles only) and should be deleted or rewritten to match the table.

**Also worth printing:** the table's distance clause is the only place "2 tiles
out" appears. If it stays, §06 should mention the exception where it defines
reach; if it goes, the 6–10 band needs a different upgrade over 1–5, because
"as above" then means "identical".

---

## 13 · Movement is correct — but the water advantage is invisible, and at Tribe unreachable

**No change needed to the rules.** Every sentence of §07's movement section was
turned into a board and checked (`app/move_test.js`): land movement crosses your
own occupied tiles and steps off onto an adjacent free tile with room; sea
movement crosses *unoccupied* Ocean only and ends on empty Ocean; rivals block
both; capacity holds; a moved or stacked-onto unit loses its fortification coin.
All hold.

**Two things the table should know, though.**

- **Stepping onto the water from land is not a sea move.** The advantage says
  "the first time each turn that you **move by sea**", and a sea move starts on
  Ocean. Getting onto the water costs a move; collecting the advantage costs a
  second one. **At Tribe, with one free move, the water advantage cannot be
  collected in a single turn at all** — you must have ended a previous turn on
  the water. That is a real consequence of two correct rules meeting, and it is
  probably why the advantage feels like it never fires. If it is meant to be
  available to a Tribe, either the first step onto Ocean should count, or Tribe
  needs a second move.
- **Nothing said which move was which.** The app now labels the hexes: *Move
  here*, *Sail here*, and *Sail — free tile* while the advantage is unspent.
  A printed rulebook cannot do that, so §07's wording carries the whole weight —
  worth a sentence spelling out that the unit must already be standing on Ocean.

**Found later, and it is a rules question, not just a client one.** The free
tile is an *explore*, so it needs a legal space — touching two tiles already on
the map — **in reach**. Out in open water there frequently is none. Measured
across scripted games, **29% of first sea moves could not use the advantage at
all**, and the engine marked it spent regardless: one sail into empty sea burned
the turn's advantage without ever showing a choice.

Fixed in the app two ways, and both are worth a line in §07:

- **The advantage is only spent when it is actually offered.** If nothing legal
  is in reach it keeps, and a later sea move that same turn may still collect
  it. That is the reading the printed rule supports — *"you MAY immediately
  explore"* is permission, and permission you cannot use is not permission
  spent — but it is not stated, and a table would rule it either way.
- **The map no longer promises what it cannot pay.** A sea destination reads
  *Sail — free tile* only where a tile could actually be laid, and the log says
  so when the advantage survives unused.

### And then the reach limit itself had to go

Reported again from play — *"no explore option when using it at the border of
the map"* — and classified over scripted games. Every single failure was one
geometry, and it was **not** a shortage of legal spaces:

| why the first sea move paid nothing | share |
|---|---|
| the ship sailed into an enclosed pocket — no empty cell beside it at all | **26%** |
| the map had no legal space anywhere | 0% |
| a legal space sat beside the ship but out of reach | 0% |

The map had somewhere legal to lay a tile **every single time**. What blocked
it was §07's own clause: *"it must be within your reach (§06)"*. A ship that
sails into a closed pocket has nothing beside it; a ship at the frontier has
cells beside it that touch only its own tile and so fail touch-two. Both are the
same wall.

**Decision: the water advantage is no longer bound by reach.** Touch-two still
holds — §06's "Blink has no bridges" is the structural rule that keeps the map
one body, and a voyage does not get to break it — but the free tile may be laid
**anywhere the map will legally take it**.

That is also the better rule, not just the working one. A card acts beside your
own civilization; a voyage should not. It gives the sea a job nothing else in
the game does — reaching ground you have never stood on, sometimes on somebody
else's doorstep — and it is the first real reason to build ships.

**Measured, 250 bot games per player count:** essentially free. 3p score 30.8 →
31.3, rounds 14.5 → 14.5, tiles on the map 38.1 → 38.4, kills 15.0 → 14.2. The
advantage is now wasted **0.00 times per game**, against 26% of first sea moves
before.

**§07 and the quick reference are rewritten**, and `move_test.js` builds the
closed pocket by hand — a seven-hex flower — and fails if the offer is narrowed
to reach again.

---

## 14 · What was applied to the documents, 14 Aug 2026

| item | rulebook | tutorial | playtest sheet | board | figures |
|---|---|---|---|---|---|
| 1 · classic trick, set aside to the shared pile | §04, §05 note, §09, worked example, quick ref, glossary | round-one walkthrough | question 3 rewritten | — | — |
| 2 · victory row scores 1/card + centre | worked table (9 / 13 / 19), the "instead" wording | — | — | — | vprow captions now show the totals |
| 3 · tier units 2/4/6/4/4 | §03 setup, §04 table | step 3 | — | ✔ | — |
| 4 · rank caps 11/13/15/17/20 | §04 table, §10, quick ref | — | — | ✔ (Civilization gained the cap it never printed) | — |
| 9 · research draw is automatic | §10 step 1, quick ref | market figure caption | — | — | — |
| 10 · the set-aside card feeds the shared pile | §04, §09, glossary (new *Set aside* entry) | round-one walkthrough | — | — | — |
| 11 · retire your lowest card | §10 step 2 + a note on timing | round three | — | — | — |
| 12 · effect B founds ground, in reach | §07, §10 prose rewritten; "may not explore" deleted | — | — | — | — |
| 13 · a sea move starts on the water | §07 note | — | — | — | — |

Two things were found while applying these and fixed in passing:

- **The market figure had been overflowing the print column by 49 px** ever
  since the grid went from 2 × 3 to 3 × 3 — `check_figs.py` had been failing on
  it, so the nine positions were being clipped in the PDF. It now has its own
  scale and all ten figures pass.
- **`build_pdfs.sh` never built the tutorial**, so `Blink-first-game.html` was
  rendered from whatever happened to be on disk. It is in the sequence now,
  followed by `check_rules.py`.

**To reprint:** `cd source && ./build_pdfs.sh`. It needs `wkhtmltopdf`, which is
not in this sandbox — the HTML, the SVG boards and the board PDFs are rebuilt
and current, but the booklet PDFs in the project root are still the old renders
and must be made on a machine that has it.

---

## 15 · Effect B is under-priced, and the bot was under-using it

Found while giving the bots play styles. Head to head against the tuned bot,
changing **one** number — hold effect B until the victory row has 4 cards, or
until it has 3 — is worth **71% of games**. Every other weight tried, across
five styles and twenty knobs, sits within a few points of par.

That is not a bot-tuning detail. It says the row's decision between *keeping* a
card for points and *spending* it on a colony is lopsided: B founds a tile,
settles a unit on it and fortifies that unit, all from the **general supply**,
for a card worth roughly one point. Spending earlier is simply better, and the
only thing stopping the tuned bot was an arbitrary guard.

Two consequences worth deciding:

- **Is B priced right?** The obvious levers are dropping the free fortification,
  or making the colony unit come from your reserve *without* the ascension it
  currently pays. Neither is measured yet.
- **Item 5's comparison of D against B used B's four-card guard as its
  reference.** If B's guard was too conservative, D looked stronger partly
  because B was being held back. Worth re-running before the D proposal is
  judged.

The guard is deliberately **locked out of the play styles** (`STYLE_LOCKED` in
`app/engine.js`): letting a style carry it would mean choosing that style is
choosing to win, and would hide this question behind a flavour label.

---

## 16 · The bots bought their upgrades at random — every earlier number was measured that way

`_buyValue` — the heuristic that decides *which* market card to take — existed
from the first port and **was never called**. The line read
`const k = this.rng.choice(avail)`. So in every measurement taken in this
project before 14 Aug 2026, each bot spent its gold on a card chosen by coin
flip from everything its rank cap allowed.

Wiring it up is worth **61% of games head to head** against the old behaviour.

Two things worth knowing about the fix:

- **The evaluator buys *lower* cards than random did** — mean rank bought 13.6
  against 14.2 — because a card that fills a gap in your hand is worth more than
  a tall one: melds are runs, and a run needs its neighbours. The gain shows up
  in melds, not in the victory row (row score 14.0 vs 14.3, unchanged).
- **Table-level figures barely move** — 3p score 31.4 → 30.8 — because every
  seat improved at once. The fix matters to a *person* playing against the bots,
  which is exactly where it was invisible.

`BUY_RANDOM: 1` restores the old behaviour for anyone re-checking an old number.

---

## 17 · Retire timing: the hold-back line is real, and it is a trap

Item 11 argued that the lowest-card rule lets a high card reach the victory row
if you hold it until it is the lowest thing you have. True — but measured as a
policy it loses badly. Bots told to research only when their hand is down to N
cards, against the tuned bot that researches whenever it can afford to:

| research only when the hand is ≤ | win % | retires per game | mean rank retired | row points |
|---|---|---|---|---|
| 10 (whenever affordable) | 47% | 12.8 | 9.6 | 14.2 |
| 8 | 26% | 10.3 | 9.6 | 10.1 |
| 6 | 22% | 8.7 | 9.6 | 9.0 |
| 4 | 8% | 6.5 | 10.3 | 6.1 |
| 2 | 10% | 4.9 | 10.7 | 4.3 |

Waiting buys about **one rank** and costs **half your upgrades**. The row is
paid per card before any rank is counted, so volume beats patience heavily.

**The rulebook has been corrected**: §10's note and the tutorial's round three
now say a high card *can* reach the row by being lived with, and add that
researching whenever you can afford it generally out-scores waiting for the
perfect card. The theme survives — nothing enters the row that was not once
your worst card — without the text recommending a losing line.

---

## 18 · The two meld variants, measured under v0.22

Both are now setup options in the app (`Meld variants: off / combination /
friends / both`), and both are pure legality changes — nothing else in the game
moves. 200 bot games per cell.

### Combination melds — real, but a third of what the booklet says

| | 3 players | 4 players |
|---|---|---|
| melds of 4+ cards | 10.9 → **13.7** (+26%) | 14.0 → **18.8** (+34%) |
| mean meld size | 2.66 → 2.80 | 2.49 → 2.62 |
| rounds | 14.5 → **13.9** | 16.6 → **15.7** |
| final score | 31.3 → 31.2 | 24.0 → 23.8 |

**The booklet's figures are from a different game.** It reports five-card melds
up 119% at three players and 205% at four, measured "under v0.20 pattern rules".
Under v0.22 the gain is a third of that. The reason is the meld limit: in v0.22
a tier caps you at 2–6 cards, and a bigger *legal* vocabulary cannot beat the
cap — so combinations mostly convert three-card melds into four-card ones
(3p: 3-card melds 11.9 → 9.3, 4-card 7.1 → 8.7) rather than unlocking fives.

What it does buy is **tempo**: games run about half a round shorter at 3p and
nearly a full round at 4p, because more cards reach the map each round. Scores
are unchanged, so it is a pace variant, not a power variant.

### Friends of 10s — measured at last, and it is negligible

The booklet says "effect on balance never measured". Now it is:

| 3 players | base | friends of 10s |
|---|---|---|
| mean meld size | 2.66 | **2.67** |
| melds of 4+ cards | 10.9 | **10.8** |
| final score | 31.3 | 31.5 |
| singles played | 9.9 | **9.2** |
| pairs played | 10.7 | **11.3** |

It converts about **0.7 singles a game into pairs** and changes nothing else.
That is the whole effect: an occasional extra pair when your hand has no run.
It was cut "because it adds an arithmetic check to every hand evaluation" — the
measurement supports that call, since the check buys almost nothing.

Together the two are additive and mild: 4+ melds 14.0 → 20.0 at four players,
games 1.4 rounds shorter, scores flat.

**One rules question the booklet leaves open, decided in the app:** when both
variants are on, a friends pair *is* a legal component of a combination, since
§the combination rule asks only for "a valid meld of at least two cards". So
5+5 with 10+10 is one four-card meld. If that is not intended, it is one line.

---

## 19 · Growing population limits — a denser, faster, much less violent Blink

Now a setup option. `Tile.capacityFor(seat)` already asked the map for a
per-band table and fell back to the fixed one, so switching it on is a single
assignment; the work was the starvation cascade, which no bot game ever reaches.

**One decision the booklet forces.** It prints four bands — Founding / Growth /
Expansion / Empire — from the version of the game that had four. v0.22 has five
tiers, so **Civilization repeats Empire's row**. Adding a fifth, higher row
would contradict the variant's own line that "Mountain and Ocean stay low
throughout: hostile ground never becomes comfortable".

| tier | Plains | Forest | Ocean | Mountain |
|---|---|---|---|---|
| Tribe | 2 | 1 | 1 | 1 |
| Settlement | 2 | 2 | 1 | 1 |
| Kingdom | 3 | 2 | 1 | 1 |
| Empire | 3 | 3 | 2 | 2 |
| Civilization | 3 | 3 | 2 | 2 |

**Measured, 200 bot games per cell:**

| | 3 players | 4 players |
|---|---|---|
| rounds | 14.5 → **12.5** | 16.6 → **13.6** |
| tiles on the map at the end | 38.1 → **30.5** | 43.7 → **36.2** |
| kills per game | 14.4 → **8.8** | 26.4 → **14.8** |
| final score | 31.3 → 31.9 | 24.0 → 25.0 |
| population | 17.2 → 17.2 | 15.2 → 15.1 |

The same twenty units go down on **20% less ground**, because the top bands
stack three and four deep where the base game stacks one and two. That makes the
game noticeably **faster** (two rounds shorter at 3p, three at 4p) and — the
striking one — **cuts the fighting almost in half**, since fewer tiles means
fewer borders to fight over. Scores barely move.

So it is not a "more room to grow" variant, whatever it looks like on the
player board: it is a **compression** variant. Worth knowing before it goes in
front of a publisher who asks why the map is small.

**The cascade is a human-play rule.** Bots feed themselves: across 600 games at
three player counts, starvation fired **zero** times, so the shedding rule never
ran once. It is tested directly instead (`limits_test.js`), including the case
that needs two passes — a tile judged before the band falls has to be caught
again afterwards — and that combat losses do *not* shed, only starvation.

---

## 20 · The app speaks German — and what that asks of the rulebook

`app/i18n.js` holds every string a player reads, English and German written as
adjacent pairs. The language is chosen on the setup screen, defaults to the
browser's own, and can be forced with `?lang=de`; switching re-renders
everything, mid-game included. 285 strings.

Two structural rules make it maintainable:

- **The engine holds no sentences.** `say()` stores a key and its variables, and
  the reasons an action is unavailable are keys too (`why.colony.noReach`, not
  English prose). The engine is language-free, which is what lets the node tests
  read it without a catalogue.
- **`i18n_test.js` guards the quiet failures**: a key present in one language
  only, placeholders that differ between languages (a dropped `{n}` swallows a
  number silently), markup that differs, a key the code asks for that nobody
  wrote, English still hard-coded in the source, and — by playing a game in each
  language — an untranslated key reaching the screen.

**This is where the app starts asking the rulebook questions.** A German edition
has to settle its vocabulary, and the app has now had to guess. The terms it
guessed, which are the ones that would be printed:

| English | chosen German | note |
|---|---|---|
| meld | **Kombination** | *Auslage* reads as a display, not a play; *Meldung* is Rommé's word for announcing |
| trick | **Stich** | standard |
| unbroken run | **lückenlose Reihe** | |
| rank | **Wert** | *Rang* competes with the tier ladder |
| suit | **Farbe** | standard |
| tier / band | **Stufe** — Stamm / Siedlung / Königreich / Imperium / Zivilisation | |
| victory row | **Siegreihe** | |
| meld limit | **Kartenlimit** | *Kombinationsgrenze* is accurate and unusable |
| shared pile | **gemeinsamer Ablagestapel** | |
| set aside | **beiseitelegen** | the new trick rule's verb |
| cash (a card) | **eintauschen** | |
| research | **forschen / Forschung** | |
| water advantage | **Vorteil zur See** | |

The card effect text and the twelve objective names are **printed-component
voice**, and the German there is a first pass rather than a decision — it should
follow whatever a German rulebook settles on, not lead it. Worth reviewing
before any of it reaches a publisher, since these are the words that would end
up on the cards.
