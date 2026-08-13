# Is the v0.21 rulebook consistent, and is it supported?

Two separate questions. Answers: **consistent, yes. Supported, partly — with
two printed claims the simulation contradicts.**

Measured with `pro_bot` in every seat, 40 games at each player count.

## Consistency — 21/21 automated checks pass

Band table (2/4/6/8 units, melds 2–5, moves 1–4, food 0–3) agrees between the
rulebook, the printed player board and the quick reference. Terrain values
agree everywhere. Effect B reads "extra **unit**" in both the rulebook and the
effects reference, and its once-per-turn cap appears in both. Every `§`
cross-reference resolves and none dangle. The tutorial contains no
pattern-placement language and teaches free moves and food slots as the
rulebook defines them.

No stale v0.20 vocabulary survives anywhere in the sixteen PDFs.

## Supported — the scoring balance is good

| | 2p | 3p | 4p |
|---|---|---|---|
| units on the map | 42% | 44% | 46% |
| victory row | 35% | 34% | 37% |
| terrain dominance | 23% | 22% | 18% |

No term runs away with the game; the three-way split the rulebook promises is
real.

**The central decision is live.** Players cash 42–50% of their cards for gold
by choice. "Is it people, or is it gold?" is genuinely being asked every turn,
which is the claim the whole redesign rests on.

## Contradicted — two printed claims

### 1. "A civilization that expands faster than it earns will starve back down"

§09, *The pressure*. Measured: **0.00 units starved per game**, at every player
count, with competent play. Food costs roughly 30% of income and is always
paid. The sentence describes a pressure that does not exist.

Either the numbers need to bite (more food per band, or less income), or the
sentence should be softened to describe food as a tax rather than a threat.

### 2. The two end triggers are not equals

§11 presents them in parallel — last unit placed, *or* a suit's advanced deck
runs dry. Measured:

| ends because | 2p | 3p | 4p |
|---|---|---|---|
| a suit ran out | 35/40 | 39/40 | **40/40** |
| someone placed their 20th unit | 5/40 | 1/40 | **0/40** |

At four players the expansion ending **never fires**. The player board, the
bands, the whole reserve-emptying arc is built around a race that does not
finish the game. This is inherited from v0.20, not caused by the redesign — but
v0.21 makes it near-absolute.

Worth a decision: either shorten the advanced decks so the market clock and the
unit race finish at similar times, or accept that Blink ends when the ideas run
out and stop presenting the twentieth unit as an equal trigger.

## Unsupported — not wrong, just untested

- **Free moves (1/2/3/4 per band).** The simulator could never separate the
  rule from the bot's movement policy. Completely unvalidated; question 1 on
  the playtest sheet.
- **Food-slot reallocation.** The ergonomics of pre-placing coins and pulling
  them back off fortifications have never been done by a human.
- **Effects A, B and C** are implemented but their balance against each other
  has not been examined under v0.21.
- **Whether meld shape still feels worth building.** Straight-of-four and
  quadruple now do identical work; the sim cannot tell you whether that feels
  flat.

## Caveat on everything above

`pro_bot` is a better bot than its predecessor but still a crude one. Two
findings already flipped when the bot improved (see findings-bots.md). The
population-ladder and objective findings have **not** been re-run against it
and remain provisional.
