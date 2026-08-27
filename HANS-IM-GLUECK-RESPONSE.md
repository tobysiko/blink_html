# Julius Körner's feedback, point by point against v0.24 core

He reviewed **v0.14** (the PDF at deep-diversions.com/blink/blink-rulebook.pdf).
This compares it against the **v0.24 core** — sections 01–11, which is exactly the
app's default setting. Map objectives (§12) and perks (§13) are modules, off by
default, and are not part of this comparison.

---

## The seven points

| # | Julius said | Status |
|---|---|---|
| 1 | Card market setup is complicated — sorting by rank into one pile | **Resolved**, with a caveat |
| 2 | Card phase and melding are a good mix | **Kept, and simplified** — see the risk note |
| 3 | Super Meld is too complex, unintuitive to mix | **Removed from the base game** |
| 4 | You don't need the black die | **Resolved** — one die does both jobs, 5 → 4 |
| 5 | The cards/terrain interaction is the strength | **Untouched** |
| 6 | Make combat interact with the played melds | **Done** — combat is now a card duel |
| 7 | Scoring unintuitive, especially the median | **Half done** |
| 8 | Consider set collection (e.g. 5 VP per suit) | **Not done** |

---

## 1 · Card market setup — resolved

**v0.14:** "Sort the advanced deck face-down by rank, highest at the bottom (equal
ranks in random suit order). Turn the top 4 cards face up." A manual sort of 40+
cards before you can start.

**v0.24:** shuffle the upgrade deck (ranks 11–20 at every player count) and deal
**nine face up in a 3×3 grid**. Shuffle and deal — nothing to sort, and the same
setup at every player count.

This is better than either option offered in the reply to him: not four suit decks,
and no per-card gold values.

**Caveat, and it is a real one.** Setup got simpler; the market's *operation* gained
a rule. Research now draws the top card onto the grid position showing the **highest
rank, covering it** (leftmost breaks a tie, nobody chooses). A fresh reader may flag
that covering rule where he flagged the sort. It is deterministic and needs no
decision, which is the defence, but it is a new thing to learn.

## 2 · Melds — the thing he liked is also the thing that changed most

**v0.14:** five meld types — Single, Straight (same suit, consecutive), Set (same
rank), Friends of Ten, Super Meld.

**v0.24:** one rule. *A meld is any cards whose ranks form an unbroken run. How many
you hold of each rank does not matter, and suits do not matter at all.*

Sets still work (duplicates are free, so 9-9-9 is a run of one rank). Friends of
Ten survives as an optional variant. Straights no longer need matching suits.

**The risk:** he praised "a good mix of trick taking and poker", and this is the
part that has been cut hardest. It is unquestionably simpler — one sentence instead
of a five-row table — but it is less recognisably poker. Worth calling out to him
directly rather than hoping he does not notice.

## 3 · Super Meld — removed

Out of the base rules entirely; it lives in the variants booklet. Exactly what he
asked for.

## 4 · The dice — one die, both jobs

**v0.14:** 5 dice — 1 black (trick winner), 3 white (initiative), 1 red (action
limit, set to the winner's meld size).

**An earlier draft of this note claimed the red die's job had disappeared. It has
not.** The winner's card count is still live information every single round, because
anyone who **matched** it and lost gives a card up to the shared pile. What changed
is the rule that reads it — from *"everyone uses one fewer card than the winner"* to
*"whoever matched the winner and lost sets one aside"* — not whether the number is
needed.

**v0.24:** the two dice become one. The **winner's die** is set to the number of
cards in the winner's meld, and marks them as first in initiative *whatever face is
showing*. It is the only die of its colour, so nothing can be confused with a plain
initiative die showing the same number. The others show 2, 3, 4 in finishing order.

Five dice become four, and Julius's actual point — the component was redundant —
is answered exactly as he suggested: *"The red die could be used for both showing
the starting player and the corresponding meld."*

## 5 · Cards and terrain — untouched

A card's suit is the terrain it acts on. Settle, explore and attack all still run
through it. This is the part he called the strength and nothing has been done to it.

## 6 · Combat interacting with melds — DONE

He raised it; the reply said *"I think I can make that work."* It works now.

**v0.14 / v0.22:** spending a card on a tile a rival occupies removed one of their
units, for a gold price set by the terrain. Nothing about it touched anybody's cards
and the defender did not participate.

**v0.24:** an attack is a **duel**. The gold price is gone. Both players commit one
card from hand, face down, and reveal together: attacker's rank against defender's
rank **plus the terrain** (Plains 0, Ocean 0, Forest 1, Mountain 2). Higher wins; a
level fight goes to the card whose suit is the ground being fought over, and to the
defender if both match or neither does. Clear the **last** defender and the ground
changes hands on the spot. Both cards go to their owners' discards, so losing a duel
costs tempo rather than material.

Three things this does, in the order they matter:

- **The defender plays.** Combat is the only moment in the game where a player acts
  on somebody else's turn, and it is the first thing in Blink that makes the hand you
  keep back worth something on its own. A hand played out is a frontier with nobody
  on the walls, and everyone at the table can count your cards.
- **The terrain acts through the fight** rather than gating entry to it. The 0/0/1/2
  is the same set of numbers as the old gold price — it now says how hard the ground
  is to take instead of how much it costs to try. A penniless player can attack a
  Mountain; they just need three ranks more than the unit holding it.
- **It made combat worth doing.** Measured: before this, a bot forbidden to attack
  beat one that attacked, 56% to 44% — under the *old* rule. Combat was a trap. With
  the duel and the change of ownership it is 51/49 the other way. See DUEL-SPOILS.md
  for the numbers and their limits.

**The honest caveat:** it is one more decision point per attack, in a game whose
other complaints were about complexity. It is bounded — one card, face down, no
table lookups — but it is not free.

## 7 · Scoring — half done

**v0.14:** four sources — units on map, count of VP cards, **largest valid meld in
the VP row**, and **median rank** (with an even-count tie rule).

**v0.24:** units on map, 1 per card in the row, the **rank in the centre slot**
(3+ cards), and **dominance**.

- **"Largest valid meld in the VP row" is gone.** That was a whole second meld
  evaluation at scoring time, and it has been deleted.
- **The median is now physical, not arithmetic.** Five printed slots, cards pushed
  right, the centre slot marked SCORES on the board. You read the card sitting
  there. This is precisely what the reply promised him — "made more obvious with a
  proper player board layout" — and it was done.

**But be honest about two things:**

- If his objection to the median was *conceptual* rather than about the arithmetic,
  it stands. It is still "the middle card of your row".
- **Dominance is new since v0.14 and is harder to evaluate than what it replaced.**
  3 points per terrain for the *largest connected stretch* you occupy, tie-broken by
  units on that terrain. That is a connected-components problem, per terrain, per
  player, at the end of the game. It is the single most demanding calculation in the
  scoring, and he has never seen it.

**Net: the scoring table is shorter, but the number of things to compute is still
four, and one of them got harder.**

## 8 · Set collection — not done

No suit-set scoring. Worth noting that his suggestion and the dominance rule are
aimed at the same target — rewarding a spread — so if dominance stays, set
collection may be redundant rather than missing.

---

## What was simplified that he never asked for

This is the stronger half of the story, and it is not in his list at all.

| | v0.14 | v0.24 core |
|---|---|---|
| Card effects | **80 unique** — a four-page per-card index | **3** (A / B / C by rank band) |
| Mismatched-card subsystem | a full section (§12) | **gone** |
| Board sync | rearrange units across four terrain tracks to match the map, every turn | **gone** — the reserve empties top-down by tier |
| Tile market | 2× players face-up, a bag, redraw for gold | **gone** — open supply |
| Combat resolution | strength totals, terrain bonuses, gold boosts, survivors distributed | one card each, one comparison; a coin fortifies |
| Meld types | 5 | **1** |
| Meld-size limit | clear a line across all four tracks | read your current tier |
| Action limit | non-winners use one fewer card than the winner | narrowed: only those who **matched** the winner and lost give one up |
| Dice | 5 (black + 3 white + red) | **4** — the winner's die shows the meld size and leads |

The v0.14 appendix alone — one bespoke effect for each of 80 cards — was more
rules text than several whole sections of v0.24.

## What is new since he looked

Be upfront about these; they are additions, not removals.

- **Feeding.** Your tier's food is due each time your hand recycles, and short slots
  starve units off the map. There was no upkeep in v0.14.
- **Dominance scoring** (above).
- **The market covering rule** (above).
- **Research is twice a turn**, at 1 gold then 2.
- **Combat is a duel** (above) — the largest single addition since he looked, and the
  only one he asked for.

---

## Where that leaves the reshow

**Ready to say:** the two structural complaints — market setup and Super Melds —
are resolved, the black die is gone along with a second die he did not ask about,
and roughly two-thirds of the base game's rules mass has been removed, mostly from
places he never named. The core is 11 sections.

**Also ready to say:** combat now runs through the cards, which is the one change he
asked for by name and the only outstanding item on this list until v0.24.

**The honest risk list, in the order he is likely to hit it:**

1. Dominance is new, unasked-for, and is the hardest sum in the game.
2. The meld rule he praised has been cut to one line — simpler, but less poker.
3. The duel adds a decision to a game being simplified everywhere else.
4. The median survives conceptually, even though the board now shows it.

**Before sending anything:** none of v0.24 has been played by humans start to
finish. The simulator proves the engine agrees with itself, not that the game is
good. A publisher reshow on unplaytested rules is the one avoidable mistake here.

Next contact is **Elmar Quiring** (elmar.quiring@hans-im-glueck.de); Julius has
already briefed him.
