# Can the economy live without Effect C?

Short answer: **yes, and it already does.** C contributes 0.0–0.6 gold out of
77–99 per game. Removing it is a no-op for the economy.

The longer answer is more interesting: **the economy is not tight.** The
rulebook says gold is tight. Under competent play it is comfortable.

## Where gold comes from, per game, all players (30 games)

| source | 3 players | share | 4 players | share |
|---|---|---|---|---|
| **ascension coins** | 27.6 | **36%** | 32.4 | 33% |
| cards cashed on purpose | 22.6 | 29% | 35.7 | **36%** |
| ranking last in a trick | 14.6 | 19% | 16.2 | 16% |
| held back (a card cashed rather than climb a tier) | 6.1 | 8% | 9.2 | 9% |
| no reserve / unplaceable (a card that had nowhere to go) | 4.6 | 6% | 3.2 | 3% |
| bonus with an empty hand | 1.4 | 2% | 1.3 | 1% |
| **effect C** | **0.0** | **0%** | **0.6** | **1%** |
| **total income** | **77.1** | | **99.0** | |

Group them properly and there are only **three** real taps:

- **cards turned into coins** — 33.3 at 3p, 48.2 at 4p → **43–49% of income**
- **ascension** — 33–36%, and it is a fixed 1+2+3+4 = 10 gold per player, once
- **the last-place coin** — 16–19%

C is not a fourth tap. It never was.

## Where it goes

| | 3p | share | 4p | share |
|---|---|---|---|---|
| food | 31.0 | **46%** | 41.0 | **48%** |
| research | 28.9 | 43% | 30.4 | 35% |
| attacks | 3.6 | 5% | 9.4 | 11% |
| fortifying | 3.6 | 5% | 5.1 | 6% |
| **total spent** | **67.1** | | **85.9** | |
| **share of income actually spent** | **87%** | | **87%** | |

## Is it enough? It is more than enough

| | 2p | 3p | 4p |
|---|---|---|---|
| **units starved off the map** | **0.0** | **0.0** | **0.0** |
| attacks abandoned for lack of gold | 0.0 | 0.0 | 0.0 |
| research abandoned for lack of gold | 0.0 | 1.0 | 2.7 |
| gold left unspent at the end, per player | 4.1 | 3.3 | 3.3 |
| share of income never spent | 13% | 13% | 13% |

**Nobody ever starves.** Not once in 90 games. Attacks are never blocked by
money. Research is blocked one to three times a game across the whole table.
Every player finishes holding three or four coins they never found a use for.

So the answer to *"is that enough to fund feeding, fortifications and
upgrades?"* is yes, with 13% to spare. The constraint that was supposed to bite
— food — is paid 46–48% of the time out of income that arrives faster than it
is needed.

## And still enough cards to populate and attack?

| cards spent in the map phase | 2p | 3p | 4p |
|---|---|---|---|
| **placed on the map** | 78% | 75% | 74% |
| cashed for a coin | 22% | 25% | 26% |

**Three cards in four still reach the map**, and population lands at 16–19 of
the 20 units. One card in four becomes a coin, and that quarter funds nearly
half the economy — that is the trade you built, and it is working as designed.

Attacks are rare (5–11% of spending) but **not because of gold** — no attack was
ever abandoned for want of a coin. They are rare because, as measured
separately, killing a unit is a 1-point denial that does not advance you. That
is what Effect D is for, and D costs a victory card rather than gold, so it does
not lean on this economy at all.

## The real finding

Removing C is safe. But the numbers say something you did not ask about:
**§07's claim that "gold is tight" is not true under skilled play.** Zero
starvation, 13% of income unspent, and a full ascension payout collected by
nearly every player.

If food is meant to be a squeeze, the levers are the food ladder itself
(0/1/2/3/4 is currently affordable), the ascension payout (10 gold per player,
guaranteed, is the single biggest tap), or the last-place coin. I would look at
ascension first — it is a third of all income, it is unconditional, and it
arrives exactly when a player is expanding fastest and therefore least in need
of help.

*(Reproduce: the scarcity counters `upgrade_no_gold` and `attack_no_gold` are
now in the engine.)*
