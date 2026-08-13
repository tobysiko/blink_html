# Removing ascension gold — and why C still does not come back

Two answers, and the second one corrects advice I gave you an hour ago.

## C does not come back. It cannot.

| per game | 2p on → off | 3p on → off | 4p on → off |
|---|---|---|---|
| **Effect C used** | 0.5 → **0.7** | 0.9 → **0.7** | 0.8 → **0.9** |
| gold C brought in | 2.3 → 3.2 | 3.7 → 3.0 | 3.2 → 3.6 |

Take away a third of the economy and C moves by a rounding error.

**The reason is structural: there is always a cheaper way to get a coin.**
Cashing a card from your hand costs you a card. Spending a victory card costs
you a *victory point* — plus, if it is not your lowest, a slice of your centre
slot. When a player needs gold they reach for the cheap tap every time, and
since the hand now refills the moment it empties, that tap never runs dry.

C could only ever matter to a player who is broke *and* out of cards, and the
immediate-refill rule makes that state unreachable.

*(The bot's C policy was itself broken until this run — it only fired when a
row slot cost zero points, which stopped being possible when the row started
scoring 1 per card. It is now need-driven: cash when broke, if the coins beat
the point. It still barely fires.)*

## The bigger finding: this economy cannot be made tight

| 30 games | 2p | 3p | 4p |
|---|---|---|---|
| total income, ascension **on** | 55.2 | 79.7 | 101.3 |
| total income, ascension **off** | **58.7** | **89.6** | **113.9** |
| gold from cashed cards, on → off | 10.2 → **28.2** | 21.0 → **53.5** | 34.8 → **72.7** |
| units starved off the map | 0.0 → **0.0** | 0.0 → **0.0** | 0.0 → **0.0** |

**Removing a third of the income made total income go UP.** Players simply
cashed two and a half times as many cards. Cashing is an unlimited tap under the
player's own control at a fixed rate of one coin per card, so any squeeze you
apply is immediately absorbed. Still nobody starves — not once in 90 games.

What actually changes is the map and the clock:

| | 2p | 3p | 4p |
|---|---|---|---|
| rounds, on → off | 12.2 → **14.9** | 14.6 → **18.9** | 16.2 → **21.1** |
| research blocked for lack of gold | 0.0 → 1.6 | 0.9 → 3.9 | 2.6 → 6.3 |
| victory-row points | 19.2 → 18.3 | 17.4 → 16.7 | 13.0 → **10.2** |
| population points | 19.2 → 19.5 | 17.6 → 18.2 | 16.0 → 16.0 |
| mean score | 44.5 → 44.0 | 39.3 → 39.3 | 32.3 → **29.5** |

Cards diverted into coins are cards not placed, so the map fills more slowly and
games run **2.7 to 4.9 rounds longer**. The victory row shrinks because research
stalls. Scores are flat at 2p and 3p and fall at 4p.

## I was wrong about ascension

Last message I suggested ascension was the first lever to pull, on the grounds
that it is a third of all income and unconditional. That was wrong, and the
measurement above is why: **ascension is not what makes the economy loose. The
cashing tap is.** Removing ascension costs you a designed reward for climbing
tiers, lengthens every game, and buys no scarcity at all.

If you want gold to actually bite, the lever has to be **cashing**, not income:

1. **Cap it** — at most one card per turn may be cashed, or at most your tier
   number. This is the only change that can create real scarcity, because it
   closes the elastic tap.
2. **Price it** — a cashed card gives 1 gold only if it is below some rank, so
   dumping good cards for coins costs you.
3. **Leave it.** A game where the player can always convert cards to coins is a
   game with a soft floor and no death spiral, which is a legitimate choice —
   it is why nobody ever starves.

And if C is to survive at all, it needs to stop paying in gold. Gold is the one
thing a player can always print.
