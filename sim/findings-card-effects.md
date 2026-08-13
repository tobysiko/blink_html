# Are the card effects in good shape? And should there be a military one?

## Read this caveat first

**The bot does not choose between effects.** It runs A, B, C and now D as fixed
policies in a fixed order, each with its own threshold — B only fires with four
cards banked, C only when starving, and so on. So every "share of spending"
number below measures **the bot's ordering, not the effects' relative merit.**

I proved this the hard way: Effect D with no threshold measured at **100% of all
spending** and halved everyone's score. Giving it B's guard dropped it to 7–11%.
Nothing about the effect changed. The same caution applies to the A and B shares
I quoted earlier in the session, including "B has eaten the victory row" and "A
is 74% at four players" — those are ordering artifacts as much as findings.

Answering "which effect is best" properly needs a bot that values all four and
picks the maximum. That is a real piece of work and it is not done.

## What can be said robustly

| per game, 30 games | 2p | 3p | 4p |
|---|---|---|---|
| A used | 6.8 | 12.0 | 13.8 |
| B used | 5.8 | 6.7 | 4.7 |
| **C used** | **0.0** | **0.0** | **0.2** |
| cards left unspent in the row | 3.8 | 3.4 | 2.9 |

**A and B are both alive and both used.** That much survives the caveat, because
each has its own policy and each fires often.

**C is genuinely dead, and this one is not an artifact.** It has a dedicated
policy with *no* threshold and it still never fires, for a reason established
separately: since the row began scoring 1 per card, spending a card costs a
point, and C returns gold — the one resource that is already in surplus by the
time you hold a victory row. Games end with 2.5–6.3 gold unspent. A bot made to
cash every free slot won no more often (31.1% against a 33.3% baseline).

## The rank ladders are in reasonable shape

| rank | A: +cards, wins ties | B: tiles, units, suit-locked | C: gold | D: kills, may settle |
|---|---|---|---|---|
| 3 | +1, no | 1 tile, 1 unit, same suit | 2 | 1, no |
| 8 | +1, **yes** | 1 tile, 1 unit, same suit | 3 | 1, **yes** |
| 13 | **+2**, no | **2 tiles**, 1 unit, same suit | 4 | **2**, yes |
| 18 | +2, **yes** | 2 tiles, **2 units**, **any terrain** | 5 | 2, yes |

Each ladder escalates on two axes and the bands stay distinguishable. No
complaints here.

## The military option: Effect D — Conquest

**Yes, and the measurements say what it has to do.** Attacking today is pure
denial: it removes a rival unit worth 1 point and puts nothing of yours on the
ground. That is precisely why a strike-minded player kills far more and wins no
more often (31.7% against 33.3%). Every existing victory-card effect builds your
own side; none projects force.

So D is not "attack better", it is **take the ground**:

> **D · Conquest.** Remove 1–2 rival units from tiles touching your
> civilization, and settle one of your units on each tile you empty.
> Fortifications still absorb a hit.
> Ranks 1–5: remove 1, no settle. 6–10: remove 1, settle. 11–20: remove 2, settle.

That turns a strike from −1 to them into a **two-point swing plus territory plus
a step up your tier ladder** — the reserve leaving your board is the engine of
the whole game.

Measured with the same guard B uses:

| | A/B/C only | with D |
|---|---|---|
| kills per game, 2p / 3p / 4p | 7.5 / 13.0 / 21.0 | **10.2 / 16.1 / 23.0** |
| D's share of spending | — | 7–11% |
| rounds | 12.2 / 14.6 / 16.2 | 12.2 / 14.7 / 16.2 |
| population points | 19.2 / 17.7 / 16.1 | 18.4 / 17.2 / 15.8 |
| mean score | 44.8 / 40.1 / 32.5 | 43.2 / 39.0 / 31.9 |

**Kills rise 25–36%. Length, population and score barely move.** It is safe to
add — it does not distort the game, and it gives the row a fourth appetite that
is genuinely different in kind from the other three.

## Recommendation

**Replace C with D.** C is dead for a structural reason that more gold will not
fix, and the card faces then read as one effect per phase and one per ambition:

- **A** — the trick (card phase)
- **B** — expansion (map phase)
- **D** — conquest (map phase)

Gold still comes from cashing cards during the map phase, which is where the
economy already lives. Four effects also crowd a card face; three is the
printable number.

**Before adopting**, the effect-choosing bot is worth building — it is the only
way to know whether A really is running away with it at four players, or whether
that is my ordering again.

*(`USE_EFFECT_D` is implemented and defaults to off.)*
