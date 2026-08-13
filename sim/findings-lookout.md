# Mountain Lookout — and a seeding bug that invalidated two runs

## First, the bug

`Game.__init__` is `(self, n, seed=0, bot=None)`. My passive-rate harness called
`E.Game(3, E.smart_bot)` — passing the **bot function as the seed**.

Two consequences, both silent:

1. `random.seed(<function smart_bot>)` is legal. Python hashes the function by
   identity, so every game *inside one process* got the same seed. All 39 games
   were byte-identical: one game, measured 39 times. That is why the rates came
   out as exact thirds — 0.0%, 33.3%, 66.7%.
2. Across processes the function's id differs, so each run got a different
   constant. **That is the whole explanation for Lookout-open reading 0.0% in
   one run and 66.7% in the next on identical inputs.**

`bot` also silently defaulted to `None`, so the games did not even use the bot I
thought I was measuring, and ran to the 80-round cap every time.

`seek3.py` calls `E.Game(3, seed=s, bot=bot)` with keywords and is unaffected.
**Every number measured through `seek3.py` stands. Both passive runs are void.**

Fixed harness: `E.Game(3, seed=9000 + g, bot=E.smart_bot)`.

## The measurement, redone

117 player-boards each, three-player games, 95% intervals.

| Objective | Passive | Sought | Gap |
|---|---|---|---|
| **Lookout-open** — own the peak, two touching oceans beside it (oceans need not be yours) | **43.6%** [35–53] | **45.7%** [37–55] | **none** |
| **Lookout-strict** — own the peak *and* both oceans, touching | — | 17.2% [10–24] | — |
| **Isthmus** — own all three, oceans *not* touching | — | 17.2% [8–27] | — |
| **Mountain Lookout as printed** — own ocean–mountain–ocean | 21.4% [14–29] | 37.9% | **+16.5 pts** |
| Foothills (mountain–forest–plains) | 37.6% [29–46] | 64.7% | +27 pts |
| Watershed (mountain–plains–ocean) | 39.3% [30–48] | 64.7% | +25 pts |

## What that settles

**The open lookout fails, and it fails on the criterion you set.** You asked for
objectives players *build toward*. Seeking it moves the rate by 2 points inside
overlapping intervals — it is not a goal, it is a thing that happens to you. Any
card where passive ≈ sought is a card that rewards the deal, not the play.

**The strict triangle fails on difficulty.** 17.2% against a deck sitting at
29–65%. At a flat 4 points a player dealt it beside any other card discards it.

**The card already in the deck is the one that works.** Ocean–mountain–ocean,
all three yours: 21.4% passive, 37.9% sought — the largest proportional gap of
anything measured, and inside the deck's band.

## And it already permits your triangle

`_chain` requires only that the three tiles are **adjacent in order**. It does
not require a straight line. So "an ocean, next to a mountain, next to another
ocean" is *already* satisfied by the bent arrangement — one peak with two
touching oceans wrapped round it — as well as by the straight one. Both were
included in every number above.

The idea you described is in the deck. What is missing is that **the card art
shows only the straight arrangement**, which invites players to read it as the
only legal shape.

That is the same point you made about melds early on: *the sequence can be
mapped onto tiles in many patterns, it doesn't have to be linear.* It applies to
objective patterns identically, and it currently applies to all twelve cards —
Coastal Chain, Foothills and the rest can all bend.

**The fix is art and wording, not mechanics.** Options, in order of my
preference:

1. **Add one line to every objective card**: *"The three tiles may sit in any
   arrangement, as long as each is next to the one before."* Costs nothing,
   fixes all twelve at once, and makes the deck 12 cards rather than 13.
2. Draw Mountain Lookout bent rather than straight, so the art itself shows the
   headland you pictured. Combines well with option 1.
3. Show both arrangements on the card. Clearest, but the art is already the
   largest element on a 63 × 88 mm face.

## Still open

Foothills and Watershed both measure **64.7% when sought**, against Mountain
Lookout's 37.9%. That spread is wider than the deck should carry at a flat 4
points — a player dealt Foothills against Mountain Lookout has an easy keep.
Worth either repricing those two to 3 points or tightening them.
