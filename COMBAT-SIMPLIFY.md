# Combat: what the assault costs, and what a cap buys

Measured 31 Aug 2026, after Hans im Glück's "too complex". 4-player, hard bots,
2000 games per row. **All of it is bot behaviour** — same caveat as
DUEL-SPOILS.md: no grudges, no table talk, no read on who is about to win.

Four fortification rules and an attack cap are wired into the engine as
options. Defaults are unchanged, so every earlier number still reproduces.

    fortify: "assault"   two cards, the LOWER rank fights   (v0.24 as printed)
             "wall"      the coin defends alone at wallRank + terrain
             "absorb"    the attack is refused, the coin is spent
             "bonus"     the defender commits a card as usual, +fortBonus
    wallRank: 13 · fortBonus: 5 · attacksPerTurn: 0 (uncapped)

---

## 1 · The duel is not a fight

| | duels | attacker wins |
|---|---|---|
| defender committed a card | 1145 (60%) | **13.6%** — and nearly all of those are ties broken by suit |
| defender had **no card** | 776 (40%) | **100%** |

A rational defender plays the minimum card that wins, or nothing. The attack is
face up before they answer, so there is no bluff to make. Combat therefore
resolves to one question — *does the target still hold a card?* — and the
answer is worth 48 duels and 24 tiles changing hands per game.

**This is why a defence BONUS cannot work.** Adding +5 to a card the defender
does not hold is adding +5 to nothing. Measured directly: a +5 wall converts
**3%** of successful attacks into holds; +7 converts 8%.

## 2 · Does combat pay? (two fighters vs two pacifists, 2000 games)

| Rule | Fighter win % | Duels/game (all four attacking) | Tiles taken/game |
|---|---|---|---|
| **assault** — v0.24 as printed | 53.4% | 49.6 | 24.1 |
| assault + 1 attack/turn | 49.8% | 24.0 | 10.5 |
| **wall 13** | 59.7% | 52.0 | 26.0 |
| **wall 13 + 1 attack/turn** | **53.5%** | **24.5** | **11.3** |
| absorb | 56.1% | 44.2 | 20.7 |
| absorb + 1 attack/turn | 51.6% | 22.5 | 9.6 |
| bonus +5 | 57.6% | 50.9 | 24.5 |
| bonus +5 + 1 attack/turn | 51.5% | 24.0 | 10.2 |

50% is chance. Standard error at 2000 games is about 1.1 points.

**The assault is what suppresses combat.** All three replacements raise the
fighter win rate by 3–6 points, and they raise it by almost the same amount —
so the gain comes from deleting the two-card price, not from what replaces it.
Choose the replacement on how it reads at the table, not on the numbers.

**The cap costs about 5 points of fighter win rate** and halves everything else.

## 3 · The recommendation: wall 13 + one attack per map phase

| | v0.24 | wall 13 + cap |
|---|---|---|
| Fighter win % | 53.4 | **53.5** |
| Duels per game | 49.6 | **24.5** |
| Map phases with 2+ attacks | 27% | **0** |
| Tiles changing hands | 24.1 | **11.3** |
| Duels against an empty hand | 43% | **31%** |

Combat pays exactly what it pays today, at half the volume. Rules deleted: the
assault, the "lower of the two ranks", the second card's suit exemption, and
the "cannot spare a card, cannot attack at all" dead end. Rules added: one
number, and one sentence capping attacks.

The empty-hand share falling from 43% to 31% is the mechanism behind "combat
feels overwhelming": the second and third attacks in a sweep are the ones that
find a hand already drained by the first. Capping removes exactly those.

**Wall rank is not sensitive.** With the cap: rank 10 → 54.9%, rank 13 → 53.5%,
rank 16 → 52.7%. Anything in that range works; 13 sits just above the median
attack rank of 12, so a routine card bounces and a strong one gets through.

**A cap of 2 is not a compromise, it is the uncapped game.** wall 13 + cap 2:
41 duels/game, 27% of map phases still holding two attacks.

## 4 · Three players

Two fighters, one pacifist, so 66.7% is chance.

| Rule | Fighter win % | Duels/game | Tiles taken |
|---|---|---|---|
| assault | 71.0% | 35.7 | 17.9 |
| wall 13 + 1 attack/turn | 74.7% | 17.3 | 8.6 |

Same shape, slightly stronger.

## 5 · What this does not say

- It does not say 13 is the right number for people. A bot commits the minimum
  card that wins and never bluffs; a person hoards, over-defends and remembers
  who attacked them last round.
- It does not say combat should pay *more*. 53% is a slight edge for fighting,
  which is roughly what a civilization game wants: worth doing, not compulsory.
- Nothing here is in the rulebook. `fortify` and `attacksPerTurn` default to
  v0.24 as printed.

## 6 · The defender's policy is worth more than any rule (added after §1–5)

Every number above assumes the engine's own defender: spend the CHEAPEST card
that holds the ground, decline when nothing does. That is the one thing in the
duel a person will not reproduce, so it was made an option — `defend` —
and the whole comparison re-run against three more policies.

    min       cheapest card that holds, decline when nothing does  (default)
    hoard     as min, but decline rather than spend above rank 12 —
              a hand is for winning tricks, not for saving one unit
    panic     the highest card that holds; over-defending, which people do
    lastditch defend only when this is the tile's last unit

Fighter win %, 2000 games, 4 players, 50% is chance:

| defender | assault (v0.24) | wall 13 + cap | change |
|---|---|---|---|
| min | 53.4 | 53.5 | +0.1 |
| **hoard** | **69.0** | **66.3** | −2.7 |
| panic | 47.6 | 47.5 | −0.1 |
| lastditch | 53.5 | 53.8 | +0.3 |

**Two conclusions, and the second one matters more.**

1. The recommendation survives every policy: wall 13 + cap tracks the printed
   game within three points whatever the defenders do. The simplification is
   free. Take it.

2. **The rules are not what balances combat — the defenders are.** A table that
   hoards its high cards for tricks makes attacking worth 69%, and doubles the
   ground that changes hands (46.8 tiles a game against 24.1). A table that
   over-defends makes attacking a mistake at 47.6%. That is a 21-point spread,
   larger than every rule change measured here put together.

   And hoarding is the *rational* trick-taking instinct: your hand wins tricks,
   which buys your whole turn, while a defence card saves one unit on somebody
   else's turn. A person who plays Blink well will hoard. So the honest reading
   of every number in this document is that it is a floor: at a real table
   combat is probably stronger and the map churns harder.

### Two attempts to close that gap, both rejected

**"The winner keeps their card"** (`duelKeep`, already in the engine). Spread
across the three policies: 26.7 points, worse than doing nothing. It cannot
reach a hoarding defender, because they decline *before* the fight — the rule
only refunds a card that was committed.

**A garrison** — defence the ground has whether or not a card is committed
(`garrison: N`, added for this test). It does compress the spread, and it does
it by making combat a trap again:

| garrison | min | hoard | panic | spread | tiles taken/game |
|---|---|---|---|---|---|
| 0 | 53.5 | 66.3 | 47.5 | 18.8 | 11.3 |
| 3 | 44.6 | 62.0 | 42.0 | 20.0 | 7.7 |
| 5 | 45.6 | 57.4 | 42.5 | 14.9 | 5.7 |
| 7 | 45.7 | 53.2 | 42.1 | 11.1 | 4.0 |

A garrison of 7 nearly halves the spread and puts fighters at 45.7% — below
chance, which is where DUEL-SPOILS.md found the game before the duel existed.
Robustness bought by making the fight not worth having is not robustness.

**So this one goes to a table, not to the simulator.** The thing to watch in
the first human game of v0.25 is not who wins the duels. It is whether people
spend cards defending at all.

## 7 · A fortification is mostly not a purchase

Measured alongside the rest, 4 players, all seats attacking:

- coins **bought** as fortifications: ~5.5 a game
- coins placed **free by colonies** (effect B): ~11.5 a game
- coins still standing on the map at final scoring: ~8

Two thirds of the walls on the board were never chosen by the player they
protect, and a third of all coins are never tested by anybody. The rule that
governs them is therefore read far more often than it is used — which is an
argument for the simplest wording that works, not the best-balanced one.

It is also the fault the engine already recorded against the pre-v0.24 "a coin
absorbs the attack" rule: bots learned walls were not worth hitting and stopped
hitting them, leaving 8.5 coins untouched at scoring. Under the assault rule
that symptom never went away — 8 coins still stand at the end. Under wall 13 it
is 8.8 coins but 3.8 walls broken a game against the assault's 3.1, so the coin
is fractionally more alive, not less.

## 8 · A wall must never lower a defence (corrected)

The first wiring had the coin REPLACE the defender's card: fortified tiles
defended at WALL_RANK and the hand was never asked. That is a bug in rule
shape, not in code — a defender holding a 19 was made *weaker* by the wall they
paid for, and any card over the wall both broke it and took the ground.

**The coin is a floor, not a substitute.** The defender still answers; the
higher of coin and card fights; the card is spent only if it was the one that
fought, so a wall that holds costs the defender nothing but the coin. Breaking
the wall and winning the fight remain one event — an attack is still one card.

Both are in the engine: `fortify: "wall"` (floor) and `"wallonly"` (substitute,
kept so the first numbers reproduce).

| defender | assault (v0.24) | wall as substitute | wall as floor |
|---|---|---|---|
| min | 53.4 | 52.2 | 50.8 |
| hoard | 69.0 | 65.4 | 65.5 |
| panic | 47.6 | 45.2 | 45.3 |

The floor costs the attacker about two and a half points against the printed
game — walls are genuinely stronger when the hand can top them — and it gets
the coin tested about as often as the assault does (3.3 walls broken a game
against 3.1), so it is not the dead rule the pre-v0.24 absorb was.

### What the coin should be worth: 10

| coin | fighter win % (min) | (hoard) | walls broken/game | coins left at end |
|---|---|---|---|---|
| 9 | 52.0 | 67.1 | 4.0 | 8.6 |
| 11 | 51.4 | 67.3 | 3.7 | 8.8 |
| 13 | 50.8 | 65.5 | 3.3 | 9.0 |
| 15 | 52.0 | 65.3 | 2.7 | 9.5 |

The number does not matter to the balance — one standard error covers the whole
column. So choose it for the sentence it makes. **10 is the top of the starting
deck, and a level fight goes to the defender: no card you were dealt can break
a wall.** Walls are broken by researched cards, which gives the coin a meaning
a player can state without looking it up, and gives research one more job.

`wallRank` now defaults to 10.

## 9 · Does a wall still matter late? Measured, and the answer reframes it

Toby's worry: by the second half everyone holds market cards, so a wall of 10
stops nothing — you only meet it if you were going to attack with a 12 anyway.

For every duel on a fortified tile, ask what would have happened WITHOUT the
coin: the defence would have been the defender's best hand card plus the
ground. Three outcomes — the coin held a tile the hand would have lost, the
wall was beaten, or the hand would have held it anyway and the coin was idle.
600 games, 4 players, one attack per turn.

| wall | rounds | coin held the tile | wall beaten | hand held it anyway |
|---|---|---|---|---|
| **10** | 1–6 | 3% | 46% | 51% |
| **10** | 7+ | 2% | 51% | 46% |
| **12** | 1–6 | 6% | 41% | 53% |
| **12** | 7+ | 4% | 51% | 45% |
| **cap** (12/14/16/18/20) | 1–6 | **18%** | 9% | 73% |
| **cap** | 7+ | **12%** | 35% | 52% |

**He is right, and it is worse than he thought: it is not only late.** At a flat
10 the coin changes the result of 3% of the fights it is in, in the FIRST half
too. Half the time it is beaten, and the other half the defender's own card was
already above it — the floor is under their hand, so it adds nothing.

**But the metric misses the coin's actual job.** The attacker can see the coin,
so they only attack a wall when they are holding something that clears it, and
otherwise they go elsewhere. That is deterrence, and it does not appear as a
save — it appears as an attack that never happened. The number that shows it is
the one the pre-v0.24 rule was condemned by: **8.6 of about 17 coins are still
standing on the map at scoring**. Half the walls are never tested. They are not
idle; they are working.

So a wall does two jobs, and they want measuring separately: it STOPS an attack
(rare — 2 to 6%) and it REDIRECTS one (common — half of them). At a flat 10 the
second job is already being done, and raising the number mostly buys more of
the first.

**Scaling the wall with the tier** (`wallRank: "cap"` — a wall holds at the rank
you may buy, a number already printed on the board) is the only version where
the coin decides fights at a rate you could feel: 18% early, 12% late. The cost
is visible in the same table — walls are attacked half as often (1.9 duels a
game against 3.9) and 10 coins stand at the end instead of 8.6. That is
deterrence turning back into avoidance, which is how the absorb rule died.

**Recommendation.** Leave the printed rule at a flat 10 — it is one number, it
teaches in a sentence, and its real work is already being done. Put the
scaling version in the perk deck, where a rate that changes how one player
plays is exactly the right size:

> **Bastions** (standing) · Your fortifications hold at your tier's rank cap
> instead of 10.

That is measurably stronger than "+2" (18% against 6%), it reuses a number the
player already reads off their board every turn, and it sits beside Ramparts in
the same corner of the design without overlapping it — Ramparts makes a coin
survive being disturbed, Bastions makes it harder to break.
