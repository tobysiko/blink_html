# Blink v0.25 — what changed, and what only looked like it changed

Two lists. The first is **corrections to v0.24**: things that were wrong in the
documents or the app and never in the game. A publisher reading the v0.24
rulebook was reading the right rules; some of them were badly drawn.

The second is **v0.25**: three deliberate changes to how Blink is played.

Keeping them apart matters. v0.24 is the version entered for **Hippodice 2027**
on 5 September 2026 and is frozen — `hippodice/Blink-rules-v0.24.pdf` is the
file the jury has, git tag `v0.24-submitted` is the tree it came from, and
nothing in this document changes either. v0.25 is what comes next.

---

## Part one — corrections to v0.24

Nothing here changes how the game plays.

### The printed documents

**Every PDF built from the rulebook stylesheet printed blank pages.** The right
number of them, correctly paginated, with nothing drawn on any. The 28-page
rulebook came out at 13 kB. The cause was one CSS rule: an entrance animation on
the page wrapper starting at `opacity:0`, and Chrome's `--print-to-pdf` takes its
snapshot the instant the page loads, before an animation has advanced a frame. It
printed frame zero.

Two checks should have caught it and did not:

- the build compared **file size** against 8 kB — the shape of a renderer that
  quits, not one that draws nothing. It now measures **ink**: decompressed
  drawing per page. A blank page carries about 250 bytes, a real one tens of
  thousands. The build stops rather than reporting success.
- the font check demanded Fraunces of the player boards, which are set entirely
  in IBM Plex and never contained a word of it. It therefore failed on **every**
  run, and a check that always fails is a check nobody reads — which is how a
  real failure shipped inside its noise. Each document is now asked only for the
  faces it uses.

**The fonts are embedded in the print copy**, so a rulebook's typography no
longer depends on a network fetch succeeding at the moment of rendering.

### The board

**A tier prints six numbers and every picture of it was missing one.** The
figure had the wall and not the rank cap. The rulebook's tier table had the cap
and not the wall. The app's board had neither. Each document was internally
consistent, which is exactly why nothing caught it.

All six — meld limit, units, free moves, food, rank cap, wall — are now on the
figure, the tier table, the printed board, the player aid and the app, and
`check_rules.py` holds all five against the engine.

### The rules text

**The rulebook stopped referring to its own development.** Three places: "one
rule, and it replaces every meld type Blink used to have", "so the old
vocabulary is gone" (now a comparison to rummy and poker, which is a fact about
the reader rather than about the design), and a module disclaimed as not yet
playtested. A rulebook describes a game, not the road to it.

### The app

- **An assault with no second card swallowed the card that declared it.** It
  broke the wall and took a unit with no duel at all — better than a real
  assault — and said nothing while doing it. It is now called off as a declined
  assault is: the wall stands and the card is cashed for a coin.
- **A research that found nothing put the price of the next one up.** The limit
  counts attempts; the price counts purchases. The bots already worked this way
  and only the human path did not. The app also now warns *before* the button
  when nothing in the market is within your cap.
- **Cards were square.** 66 px wide and about 70 tall, with a coloured stripe.
  They are portrait now, and holding any card opens it: all three effects, each
  labelled with when it can be used.
- **The market looked like a hand** — a row of nine across the top, which is the
  one shape a hand also has. It is the 3×3 grid it is on the table, with the
  deck and the shared pile drawn as the card stacks they are.
- **Initiative was coloured pins.** It is the dice now: the winner's die in its
  own colour showing the size of the winning meld, plain dice showing 2/3/4, and
  a die lifted out of its slot for a player who has finished — the idiom the
  printed board already used.
- **The German title bar named v0.23 in a v0.24 build.** It takes the build's
  tag now, and the test suite fails if any language names a rulebook version by
  hand.

---

## Part two — v0.25

Three changes. Two of them delete setup rather than adding to it.

### One deck at every player count

Ranks **1–10** are the starting deck and **11–20** the advanced deck at two,
three and four players alike.

It used to cut the starting deck to fit the table — 6–10 at two players, 3–10 at
three, with a hand-tuned patch drawing two of the four rank-3 cards at random
and boxing the rest to keep the suits even. That cost twice over. The rank caps
printed on the board only mean something against a full ladder: a two-player
game whose market stops at 15 makes Empire's and Civilization's caps decoration.
And it was a setup step, with a table, that had to be got right before a card
was dealt.

**What nobody drafts is not removed. It becomes the shared pile** — face down,
and the pile every hand refills from. Twenty cards at two players, ten at three,
none at four. So at the smaller counts the pile starts stocked and what comes
back into a hand is less predictable than what went into it; at four players
this is exactly the game it always was.

All 80 cards are in play in every game. The only thing that removes one is the
victory row and the effects spent from it.

### One end trigger

A thinning market used to end the game as well as a player placing their last
unit. Measured over 240 games at each count, the market trigger fires in **0% of
two-player games, 8% of three-player and 12% of four-player**, and when it does
it saves about a tenth of a round.

A second trigger nobody meets is a rule everyone has to be taught for nothing.
**The last unit is the only end now.** Every game still ends, 100% of them on
that trigger, with a median of 11–12 rounds at every count and a tail of 15 / 18
/ 21. It is also the trigger you can see coming from across the table.

### Melds are played face down

Everyone lays their meld face down. All anyone can see is **how many cards** each
player put down — which is the number that decides what matching the winner will
cost, and nothing more. When the last meld is down, everyone turns over at once
and the trick resolves.

Effect A was already declared blind. This makes the meld blind for the same
reason: the last player to lay used to choose knowing exactly what they had to
beat, and now nobody does. It costs the bots nothing — they never read a rival's
cards when choosing a meld — and it gives the round a moment it did not have.

---

## What is where

| | |
|---|---|
| `hippodice/Blink-rules-v0.24.pdf` | the rulebook the Hippodice jury has. Frozen. |
| `hippodice/Blink-game-description.pdf` | the one-page description uploaded with it. Frozen. |
| git tag `v0.24-submitted` | the tree as it stood when the entry went in |
| `source/Blink-rules-v0.24.html` | the v0.24 text, restored to the submitted wording and no longer rebuilt |
| `Blink-rules-v0.25.pdf` | current |

The corrections in part one were **not** back-published as a v0.24.1. The jury
has downloaded a PDF; reissuing it helps nobody, and two current rulebooks is a
worse problem than one with a known list of errata. Note that the frozen v0.24
HTML still contains the animation rule that printed blank pages — if it is ever
rebuilt, that has to be patched first.
