# Porting the simulator to v0.21 — what the card-conversion rules changed

Smart bots, seeds 0–14, the same seeds through both engines (`econ_check.py`,
`port_check.py`, `moves_test.py`). Invariants and conservation checked every
round of every game: ten cards, twenty units, map connected, touch-two,
60 tiles and the full deck accounted for.

## What was ported

The pattern game is gone from the engine, not switched off. `piece_placements`
and `value_placement` now raise `NotImplementedError` rather than return
something plausible, because several v0.20 scripts import them and a silent
empty result reads as "no legal placement" instead of "this script has not been
ported".

In their place: `reach()` (a tile you occupy or one adjacent to it),
`card_options()` (legal cell/action pairs for **one** card against the map as
it stands **now**), and a `_place` that resolves cards one at a time, best
first, re-reading the map between each. Explore-then-settle within one turn is
therefore modelled — v0.20 explicitly forbade it.

Also new: free moves by band (`USE_MOVES`), fortification coins reclaimable to
cover food (`USE_RECLAIM`), and deliberate cashing (`CASH_FOR_FOOD`,
`CASH_THRESHOLD`) — a card whose best map use scores below the threshold
becomes a coin.

## 1. The economy is the same size, but it is now chosen

| | 2p | 3p | 4p |
|---|---|---|---|
| cards cashed for gold — v0.20 | 21% | 31% | 37% |
| cards cashed for gold — v0.21 | **38%** | **42%** | **46%** |
| gold earned per game — v0.20 | 34 | 46 | 78 |
| gold earned per game — v0.21 | 31 | 46 | 76 |

Cashing nearly doubles at two players and rises everywhere — and **total gold
income barely moves**. That is the finding. In v0.20 much of that gold arrived
by accident: a card whose suit found no terrain, or a pattern that would not
fit, was converted for you. In v0.21 the same quantity of gold arrives because
somebody decided to take it.

This is what the redesign was aimed at, and it lands: the tight-gold economy is
intact, and converting cards is now a decision rather than a consolation.

## 2. Games are ~10–20% shorter, and the reason is the market

| | 2p | 3p | 4p |
|---|---|---|---|
| rounds — v0.20 | 17.9 | 16.5 | 19.7 |
| rounds — v0.21 | 14.3 | 14.7 | 18.0 |
| upgrades per round — v0.20 | 0.76 | 1.26 | 1.63 |
| upgrades per round — v0.21 | 0.98 | 1.50 | 1.81 |

Upgrades per round rise about 20% — gold arrives earlier and more reliably, so
research is funded earlier — and the advanced decks drain proportionally faster.

**A correction worth recording.** The first read of this said v0.21 had flipped
the end trigger from "last unit placed" to "a suit ran out". It had not.
v0.20 already ends on the market drying up in 12/15, 11/15 and 14/15 games at
2/3/4 players. v0.21 makes it 15/15 everywhere (30/30 at three players on the
larger sample). The trigger did not flip; it went from dominant to total.

But it is a **property of skilled play, not of the rules**. Run the same
engine with random-legal bots and the picture inverts: 52 of 60 three-player
games end on the twentieth unit and only 8 on the market. Bots that upgrade
whenever they can afford it drain the ladders; bots that play at random do not
buy enough to get there.

So the honest statement is: *the better the players, the more certainly Blink
ends as a market clock rather than as a race to fill the map.* That question
belongs to v0.20 as much as to v0.21, and it is worth a decision — if the
twentieth unit is meant to be the dramatic ending, it is currently the ending
that only beginners see.

## 3. Fewer units on the map, more score in the victory row

Settles fall 16–20% and explores 25–34%, because cards that used to be forced
onto the map are now cashed. Score composition follows: population falls about
20–26%, and the victory row rises 19–65%. Mean final score is unchanged
(24.6→24.6, 22.1→20.6, 21.0→21.6).

Worth watching at the table: the row was already ~38% of the final score in
v0.20 and this pushes it higher. If the row grows much further, Blink starts
scoring like a card game with a map attached.

## 4. Free moves are NOT yet measurable — the bot is in the way

| allowance (3p) | rounds | moves/turn | tiles | population | score |
|---|---|---|---|---|---|
| band 1–4 (the rule) | 14.7 | 1.72 | 20.1 | 8.2 | 21.2 |
| 0 — off | 14.1 | 0.00 | 22.9 | **10.5** | 22.2 |
| 1 flat | 15.4 | 0.72 | 21.1 | 8.4 | 20.5 |
| 2 flat | 14.9 | 1.42 | 20.5 | 8.3 | 21.3 |

Read naively this says free movement is actively bad for you. Do not believe
it. The move policy as written relocates any spare unit toward open ground,
which strews single units across the map where rivals kill them cheaply — and a
moved unit also drops its fortification coin. What the table measures is that
policy, not the rule.

The honest statement: **the free-move allowance is unvalidated.** Before it can
be trusted the policy needs to move units for a reason (reinforce a contested
majority, evacuate a doomed tile) rather than to spread. Flagged rather than
papered over, because a plausible-looking number here would be worse than none.

## What did not change

Attack kills per game are up 4–36% (more gold means more players can afford
Forest and Mountain), dominance scoring is flat within noise, and mean score is
flat. Nothing in the port suggests the redesign broke the balance — it moved
where the decisions are.

## Not ported

`compare.py` and `h2h.py` call `greedy_bot`, `turtle_bot` and `mixed`, which do
not exist in either v0.20's or v0.21's engine. That breakage predates this work.
Every objectives script (`seek3.py`, `obj2.py`, `passive.py`) still assumes
pattern placement and has **not** been ported: objective rates measured on
chains of adjacent tiles are meaningless until someone decides what a map
objective means when melds no longer draw shapes.
