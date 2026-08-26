# Victory row slot perks — design note

**Status: proposal, unbuilt, untested.** Nothing here is in the engine or the rulebook.

The premise: the victory row is worth points at scoring and nothing before it, so
there is no reason to fill it early. Give the slots live perks and the row becomes an
engine instead of a scorecard.

The goal of a perk is **the feeling of having been clever with it**, not a win-rate
edge. They are deliberately chosen not to move the game much, which is what keeps them
out of balance trouble. Everything below is sorted by *risk* — how badly a perk could
warp the game — not by how good it is.

---

## 1. What the row actually does

Five slots. Cards are **rank-sorted and pushed right**, so:

| slot | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| cards needed to occupy it | 5 | 4 | 3 | 2 | 1 |
| what sits there | your **lowest** | | scores its rank | | your **highest** |

Two gradients run in **opposite directions**:

- **Depth** increases leftward. Slot 1 is the hardest to reach.
- **Rank** increases rightward. Slot 5 always holds your best card.

The row is capped at 5. Research is the only way in, and it retires your **lowest**
hand card. Spending a victory card on effect A/B/C removes it from the row and from
the game, so **using an effect can switch a perk off** — a good, automatic tension.

### Four of the five slot ranks currently do nothing

Only the card in **slot 3** scores its rank. Nudge any other card by one and the score
does not move:

| nudged | row | score |
|---|---|---|
| — | 5 8 12 15 20 | 17 |
| slot 1 | 6 8 12 15 20 | 17 |
| slot 2 | 5 9 12 15 20 | 17 |
| **slot 3** | 5 8 **13** 15 20 | **18** |
| slot 4 | 5 8 12 16 20 | 17 |
| slot 5 | 5 8 12 15 21 | 17 |

Slots 1, 2, 4 and 5 contribute exactly +1 each as *cards*; their ranks are dead
weight. **That is free design space** — a rank-scaled perk gives those numbers a job
they have never had, without touching scoring at all.

### Why rank-scaling works at slot 1 after all

Slot 1 holds your lowest card, so a rank gate there looks weak. It is the opposite:

> The starting deck is ranks 6–10 (2p), 3–10 (3p) or 1–10 (4p). The upgrade deck is
> **ranks 11–20 at every count**. So a slot-1 card of rank 11+ can only have come from
> the market — which means **every card in your row is an upgrade**.

"Your worst idea is still a modern one" is a genuine achievement, it reads instantly
off the table, and it needs no new numbers. **Rank 11+ is the threshold for slot 1.**

## 2. How often the slots are reached today

`node app/rowdepth.js` — 400 games per count, current bots, no perks:

| | s5 (1+) | s4 (2+) | s3 (3+) | s2 (4+) | s1 (5+) |
|---|---|---|---|---|---|
| 2p | 100% | 100% | 100% | 56% | 21% |
| 3p | 100% | 92% | 72% | 18% | 5% |
| 4p | 98% | 78% | 50% | **10%** | **4%** |

**A perk on slot 1 fires for one seat in twenty-five at four players.** Putting the
biggest prize there is right, but as things stand it is a lottery. The slots that
would actually change how people play are 4 and 3. Note too how differently this
behaves by count: a 2p row is full five times as often as a 4p one.

## 3. Why the row stays shallow — and why perks would fix it

| | end gold | end hand | research declined |
|---|---|---|---|
| 2p | 4.8 | 5.6 | 0.01 / player |
| 3p | 4.7 | 5.4 | 1.68 / player |
| 4p | 4.3 | 5.4 | 4.10 / player |

Players end with gold unspent and cards unplayed, having **declined to research four
times a game at 4p**. Gold is not the brake and neither is time — retiring a hand card
costs more than the row pays back. That is exactly the lever a perk pulls, and it
means perks will deepen rows, shifting the table in §2 leftward.

**The compounding risk:** research improves your hand *and* would now buy perks, so
any perk that discounts research, raises the research limit or refunds the retired
card would feed itself. None below do.

---

## 3b. The row prices its own perks — which is why tiering is unnecessary

Spending a victory card on A/B/C removes it from the row. So a player who likes
their perks will spend fewer effects, to keep the row deep enough to run them.
That is a brake nobody has to design, and `node app/perkcost.js` shows it is a
large one:

| | effects spent / player | spends that would switch a perk OFF: needs 2 / 3 / 4 / 5 |
|---|---|---|
| 2p | 11.63 | 0.06 / 3.95 / 5.59 / 2.02 |
| 3p | 9.56 | 0.21 / 3.55 / 4.46 / 1.33 |
| 4p | 7.38 | 0.46 / 3.03 / 3.13 / 0.73 |

Effects are spent **seven to twelve times a game**, and around **three of those
spends** would each cost the player a perk needing three or four cards. So a
player holding perks they value faces that decision three times a game, and the
better the perks, the more effects they forgo. **Strong perks pay for
themselves.** Tiering power by slot is solving a problem the game already
solves, twice over — and it does active harm, because putting the weakest perks
in the only reachable slot means the perks a player can actually get are the
boring ones, which defeats the entire premise of making the row worth filling.

### Correction: the case against free assignment was measured wrong

An earlier draft of this note argued that free assignment collapses, because a
perk in slot 4 fires ~2.3 times a game and the same perk in slot 1 fires once in
a hundred. Those numbers are real but they are **a lower bound taken under the
wrong incentives**. They come from bots that dump effects freely, because in
their world the row does nothing but score at the end. That is precisely the
behaviour perks exist to change.

Sampling depth at every turn rather than every recycle does not rescue the deep
slots either — 8.4 / 3.5 / 0.4 / 0.03 turns for slots 4 / 3 / 2 / 1 — but that
is the same bots making the same free spends. **The post-perk equilibrium cannot
be measured with players who have no reason to hold cards.** It has to be
played.

That is twice in this note that bot behaviour has produced a confident wrong
conclusion. Worth remembering before the next one.

## 4. Equal perks, dealt to players, assigned by them

**The model:** every perk is equal in standing. Each player is dealt a few and
assigns each to a slot on their own victory row, permanently, at setup.

- **The slot is the bet.** An easy slot means the perk works almost at once; a
  deep slot means holding a row you must not spend down. The measurements above
  say the deep end is expensive — that is the point. It is a commitment, not a
  worse option.
- **Agency beats curation.** A player who arranges their own perks is invested
  in them. A player handed a fixed ladder of someone else's ordering is not, and
  if the reachable rungs are dull they will ignore the whole system.
- **Variance wants a draft.** Blink already opens with one — keep 4, pass 6;
  keep 6, pass 4 — so dealing perks and passing would sit inside a ritual the
  table already performs, and turn a random hand into a decision.

**What this costs.** The four decks below stop being structure and become
flavour at most, since their whole job was tiering power by slot depth. The
printed tokens carry "slot 1", "slot 2" and so on; under free assignment those
labels are wrong and the sheet needs a reprint without them.

## 4b. The four decks (superseded — kept for the perk list)

One deck per slot, named so they cannot be confused with the **A / B / C** effects
printed on every victory card:

| slot | deck | character | needs |
|---|---|---|---|
| 1 | **WONDERS** | powerful, interactive, rank-scaled | 5 cards |
| 2 | **WORKS** | map-facing, solid | 4 cards |
| 3 | **CRAFTS** | about the row and the cards themselves | 3 cards |
| 4 | **CUSTOMS** | small, economic, fires often | 2 cards |
| 5 | — | nothing: it fills on your first research, so a perk here is a baseline everyone has rather than something earned | 1 card |

Slot 3 keeps its scoring job, so its deck is deliberately the one **about the row** —
the perks there read as related to what that slot already does rather than competing
with it.

### WONDERS — slot 1

Every Wonder is **once per recycle, twice if the card in slot 1 is rank 11+**. One
scaling rule for the whole deck, no per-tile arithmetic.

| perk | notes |
|---|---|
| **Force a rival to spend a victory card** on B or C and discard it | The brake on the whole system — see §5. At rank 11+, *you* choose the card instead of them. |
| **Move one enemy unit** to a legal adjacent tile, instead of one of your own moves | Dominance scores the largest **connected** stretch, 3 points × 4 terrains, so one nudge can break a chain worth up to 12. |
| **Overstack one tile** by one unit above its terrain limit | Mountain and Ocean hold 1, so this doubles them. |
| **Touch-one placement** — a new tile need touch only one tile, not two | Opens frontiers the map otherwise forbids; compounds with the water advantage. |
| **Take the set-aside card into your hand**, discarding one of yours instead | Card selection plus denial; fires whenever anyone matches you and loses. |

### WORKS — slot 2

| perk | notes |
|---|---|
| +1 free move | Clean, always useful, scales with tier. |
| Water advantage on **every** sea move, not just the first | Turns navies into an expansion engine. |
| A fortification survives one disturbance | Makes walls worth the coin. |
| Attacks on Forest/Mountain cost 1 less (min 0) | Narrow but sharp. |
| Reach extends one tile further | Situational. |

### CRAFTS — slot 3

Perks about the row, the hand and the market — so the scoring slot's second job stays
thematically close to its first.

| perk | notes |
|---|---|
| **An extra meld shape** — friends of 10s, or combination melds | Already built; see below. |
| **Resurrect a spent card** — swap a hand card for one from the removed pile | Measured below. Helps most at 4 players, which is where hands fragment worst. |
| Choose which card the matching loser sets aside | The mild half of the Wonder version. |
| Rank cap +1 | Mildly compounding — better cards, better melds. Watch it. |
| Peek at the top of the upgrade deck before committing to research | Information only; removes the blind draw the bots decline over. |
| Move a market card to another grid slot | Fiddly — only matters through which card the next draw buries. |

### CUSTOMS — slot 4

| perk | notes |
|---|---|
| Pay one less food per recycle (min 0) | Dead at Tribe, worth 4 gold a recycle at Civilization — grows exactly as the row deepens. |
| Once per turn a cashed card pays 2 gold | Small, steady, hard to misplay. |
| Take 1 gold when you come last in a trick, on top of the usual coin | Rewards the graceful concede. |
| Your first research each turn costs nothing extra to *place* | Cosmetic-ish; safe. |

### Rejected — would rewrite the game

| perk | why not |
|---|---|
| Play one card outside the run | The unbroken run is the one rule everything else is built on. |
| Retire any hand card on research, not your lowest | Removes the central friction of research outright. |
| Any research discount or extra research | Feeds itself: research buys perks, perks buy research. |

### Resurrection — and why it is a 4-player perk

Cards spent on effects go to `removed` and never come back. The pile is public — every
one of them sat face up in somebody's victory row — so browsing it leaks nothing.

`node app/resurrect.js` — 200 games per count. The naive question ("would one more
rank lengthen my longest run?") answers *yes, 100% of the time* and is worthless,
because melds are capped at your tier's limit: lengthening a run you already cannot
play in full buys nothing. Measuring the real operation — discard one, take one, does
the best **playable** meld grow:

| | pile size | ranks 1–5 | 6–10 | 11–15 | 16–20 | already at limit | of the rest, helps | gain |
|---|---|---|---|---|---|---|---|---|
| 2p | 23.3 | 0% | 79% | 20% | 0% | 31% | 25% | +1.09 |
| 3p | 28.6 | 34% | 52% | 13% | 1% | 21% | 37% | +1.05 |
| 4p | 29.6 | 56% | 30% | 12% | 2% | 24% | 55% | +1.15 |

Three things fall out:

1. **It scales with player count** — useful on ~17% of hands at 2p, ~42% at 4p. Most
   perks do the opposite. The 4p starting deck is ranks 1–10 against 6–10 at 2p, so
   hands are spread wider and fragment more, and this is the fix arriving exactly
   where the problem is.
2. **The pile cannot be fished for power.** It is mostly junk — 56% rank 1–5 at 4p and
   2% rank 16–20 — because it fills with cards retired from hands as the *lowest*
   card held. You bridge a gap; you do not pull a 20 out of it.
3. **Roughly a quarter of hands are already at the meld limit** and gain nothing at
   all, which is a healthy natural ceiling.

Under sum scoring one extra low card adds map actions, not trick-winning total — same
family as the meld shapes below. Flexibility, not force.

**The friction is table time.** Browsing thirty cards mid-turn is slow. Keep the pile
face up in a spread rather than stacked, or restrict the perk to ranks 10 and under,
which is 86% of the pile at 4p anyway and costs almost nothing.

### Alternate meld shapes — already built

**Friends of 10s** (two cards summing to 10, 20 or 30) and **combination melds** (two
or more melds of 2+ cards played as one) already ship as global setup options —
`friendsOf10` and `comboMelds` in the engine, both in the setup panel. The perk version
hands one player a shape the others lack.

`node app/meldrules.js` — 300 games per count — finds **no measurable difference** in
score, rounds, row depth or end gold between run-only, friends, combo and both. Bots
cannot tell us whether that is because they never hunt for these shapes or because the
shapes cannot spike power. But the second is structurally true either way: **a friends
pair sums to exactly 10, 20 or 30 by definition**, and under sum scoring a run of three
middling cards beats 10 or 20 outright.

So friends of 10s is almost never the meld that *wins* a trick. It is a way to spend
two unconnected cards on the map while conceding — and conceding pays a coin. That
makes it a **graceful-concede tool**, and it answers the complaint that research
strands you with high and low cards that connect to nothing. Flexibility, not force:
exactly what a Craft should be. Same-suit melds, every-other-rank sequences and
ranks-summing-to-a-multiple-of-ten all share the property.

### One pain point, three perks

Friends of 10s, combination melds and resurrection all attack the same thing: a hand
whose ranks do not connect. That is worth naming, because it means the problem is
real and recurring rather than three separate ideas.

Usefully, **the deck structure already stops them stacking** — all three are CRAFTS,
so a game draws at most one. Each game gets a different answer to the same problem,
which is close to ideal for replayability. If playtests show hands still fragment
badly *without* a Craft in play, that is the signal the base game needs a direct fix
rather than a perk.

---

## 5. The forced-effect perk deserves its own note

A **poisoned gift**, not a plain attack: the victim loses a row card but *gains* the
effect. On a full row of 5, 8, 12, 15, 20:

| | row after | centre rank | row score |
|---|---|---|---|
| untouched | 5 8 12 15 20 | 12 | **17** |
| they drop the **lowest** | 8 12 15 20 | 12 | 16 |
| they drop the **highest** | 5 8 12 15 | 8 | 12 |

Left to themselves they always dump their lowest: one point, unchanged centre rank,
and the weakest possible B or C since both scale with rank band. The real damage is
5 cards becoming 4, which switches off their own slot-1 perk.

That is why the rank-11+ upgrade is *you choose the card*: forcing the highest out
costs them 5 points, but hands them their strongest colony or a full 5 gold. The more
you hurt them, the more you give them.

Either way it does nothing to a shallow row. **That is the point** — it only bites
players who invested, which makes it the built-in brake on the perk economy. Without
something like it, whoever researches hardest snowballs.

The cost is table friction: an out-of-turn action interrupts. A deferred version — *at
the start of their next turn they must spend a victory card* — keeps the effect and
loses the interruption.

## 6. Spent and available

Measured over 300 games per count:

| | rounds/game | recycles per player |
|---|---|---|
| 2p | 10.6 | 2.69 |
| 3p | 10.7 | 2.49 |
| 4p | 11.7 | 2.54 |

**Per recycle is roughly four times rarer than per turn**, and a perk unlocked
mid-game gets fewer still. It is still the better cadence:

1. It makes each use a decision instead of a routine drip.
2. It hooks a beat the board already tracks — food is paid on recycle, so that moment
   already stops play and gets attention.
3. **It deepens an existing choice rather than adding one.** Meld size decides when you
   recycle, so "when does my hand come back" quietly becomes "when do my perks come
   back" too.

Do not mix cadences by tier — double the rules to remember for very little.

### The component

Two-sided tokens or cards, one face **available**, one face **spent**, flipped back on
the recycle.

One production note: duplex registration is the thing print-and-play does worst, and a
token whose two faces are misaligned by two millimetres looks broken. A
**fold-over tile** avoids it entirely — print both faces side by side on one side of
the sheet, fold along the middle, glue. Same component, no back-to-front alignment,
and it comes out double thickness, which is welcome at token size.

**Where they sit is unsolved.** The victory row divider is at 183.5 mm and the cards
start at 194, with the row label and rank arrow between — no room for four tiles on
the board. On the table above the row is fine for a playtest; hosting them properly
means a board redesign, which is premature.

## 7. The modular draw

Deal one perk per slot at setup, face up, **shared by all players** — same ladder for
everyone, so there is nothing to balance between seats, and a different game each
time.

The four decks are what make a blind draw safe. Drawing three perks from one pool
regularly produces an all-aggressive game or one where nothing touches the map; one
draw per deck guarantees a spread and tiers power by depth automatically. With the
perks listed here that is already **5 × 5 × 5 × 4 = 500 combinations**, and adding a
perk later is just adding a card to one deck.

## 8. Iconography

A perk deck needs a visual grammar, and there is one to extend rather than invent:
lettered effect rows on the cards, terrain glyphs, the coin. Each tile needs three
marks:

- **what it does** — the perk's own symbol
- **when it comes back** — the recycle mark, which the board already implies through
  the food slots
- **who it points at** — self or rival, since the aggressive perks are the ones most
  easily misremembered as self-targeting

Detail goes in an appendix, as with complex euros: the tile carries an icon and one
line, the appendix carries the edge cases. Worth doing once and consistently, because
the same icons will want to appear on the board, in the rulebook and in the app.

## 9. On asymmetric civilisations

The decks would furnish it, but two cautions:

1. Because the row fills in a fixed order, a per-player ladder is not a *choice* — it
   is a fixed sequence you climb. Asymmetry would come from each player holding a
   different ladder, not from anyone picking a path.
2. Balancing four ladders against each other is a far larger playtest job than
   balancing one, and the base game has not yet been tested with Disasters or trade.

The shared modular draw in §7 gets most of the variety for none of that risk, and it
is how you would tune the individual perks before handing anyone their own set.
