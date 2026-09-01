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
