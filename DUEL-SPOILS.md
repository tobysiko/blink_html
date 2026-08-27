# Combat does not pay — and it did not pay before the duel either

Measured while wiring up the duel. Every number below is 4-player, hard bots,
no noise, 250 games per row unless stated. **All of it is bot behaviour**, so
read it as "what a competent, unimaginative player finds", not as a verdict.

---

## The test

Four seats, two of them ordinary bots, two of them forbidden to attack at all
(`ATTACK_V: -99`). Rotated so nobody keeps a seat. If attacking is worth doing,
the fighters should win more than half the games.

| Rule | Fighters | Pacifists | Kills/game |
|---|---|---|---|
| **Gold rule** (attack costs 0/0/1/2 coins, kill is certain) | **43.5%** | **56.5%** | 6.0 |
| **Duel as agreed** | 47.1% | 52.9% | 0.9 |
| Duel + winner keeps their card | 49.0% | 51.0% | 0.8 |
| **Duel + winner takes the ground** | **51.0%** | **49.0%** | 0.9 |
| Duel + both | 51.0% | 49.0% | 0.8 |

**The headline is the first row.** A player who never attacks beat one who does
by thirteen points *under the old rule*. Combat was already a trap. The duel did
not break it; the duel is the first change that moves the number in the right
direction, and it still does not get there on its own.

## Why

An attack costs a meld card and buys the removal of one enemy unit. It does not
gain you the tile — your own unit stays in reserve, and the ground still belongs
to its owner unless you emptied it. Settling that same card gains you a unit on
the map, which is a point. So an attack has always been *worth less than the
alternative use of the card*, and under the gold rule it was merely cheap enough
that a bot with nothing better to do would take it.

The duel adds a second card and a coin-flip on top of that. It makes the price
honest, and the price turns out to be higher than the goods.

## The candidate fix

**A won duel takes the ground.** If the tile is emptied and you have a unit in
reserve, it settles there at once. That is the only change measured that puts
fighters above pacifists, and it is also what an attack *looks like* it should
do at the table — currently you win a fight and then watch the tile stay in
somebody else's colour until a later card can settle it.

It is wired into the engine as `duelTake`, **off by default**, next to
`duelKeep` (only the loser discards), which helps less. Neither is in the
rulebook.

## What this does NOT say

- It does not say the +1/+2 terrain bonus is the wrong size. That was measured
  separately and could not be measured with bots at all — see the note in
  `app/combat_test.js`.
- It does not say players will behave like this. A bot values a kill at
  `D_DENIAL_W` and nothing else; it has no grudges, no table talk, and no read
  on who is about to win. Combat in a four-player game is a social instrument
  and half its value never appears in a simulator.
- It does not say combat should be *frequent*. One decisive fight a game may be
  better than six cheap ones. What it says is that under the current numbers a
  player who ignores combat entirely is not making a mistake, and that is the
  thing worth fixing.

## Bot changes made alongside this

The bot's attack valuation still charged the gold price the duel had removed,
so it was deterred by a toll nobody collects and undeterred by the fight it was
walking into. Rewritten as `duelValue()` in `app/engine.js`. Three things, in
order of measured impact on the Raider style's head-to-head win rate:

1. **Refuse fortified tiles.** A coin absorbs the attack outright; there is no
   duel and nothing dies. Worth 12 points on its own.
2. **Check your hand first.** You cannot win a duel with cards that do not clear
   the ground. Worth ~10 points.
3. **Charge for the committed card**, and treat the terrain as a defence bonus
   rather than a toll.

Raider went from 23% to 49% head to head. All five styles now sit between 43%
and 55%, the tightest spread this test has recorded.
