# Rewarding the trick winner instead of docking everyone else

> **SUPERSEDED IN PART — read findings-bots.md.** Everything below was measured
> with `smart_bot`, which drafted at random. Re-run with `pro_bot` the
> recommendation changes from **2 gold to 1 gold**: under competent play one
> coin narrows the gap (16.3 → 14.8) *and* lifts last place (15.2 → 18.7),
> while two coins are worse than one on both counts. The direction of the rule
> is unchanged; only the amount.

`bonus_test.py`, smart bots, 25–30 games at three players, identical seeds in
every row. Invariants and conservation checked every round.

**Base rule (v0.21 §04).** The winner spends every card of their meld; everyone
else spends **one fewer** and takes 1 gold for the card left out.

**Proposed.** Nothing changes for the losers except that converting a card to
gold becomes **voluntary** — they spend their whole meld and may cash any card
they like, exactly as §06 already allows. The **winner spends one extra card
from hand** on top, or takes 1 gold if their hand is already empty.

Note what the loser gains and loses. They are strictly *freer*: they can
replicate the old outcome exactly (use one fewer card, cash it for a coin) or
keep all their cards on the map. But the coin is no longer **free** — it now
costs a map action. That price is the whole economic story below.

## The headline: the old "penalty" was a catch-up subsidy

This is the finding, and it reframes the rule that already exists rather than
the one being proposed.

| | base rule | the proposal |
|---|---|---|
| leader's final score | 28.9 | **32.6** |
| last place's final score | 13.0 | **11.1** |
| leader minus last | 15.9 | **21.5 (+34%)** |
| tricks won by the eventual winner | 39% | **46%** |
| tricks won by the eventual last place | 28% | **24%** |
| rounds won by the same player as the round before | 38% | **45%** |

Chance at three players is 33%, so the base rule already shows mild persistence
(38%). The bonus card pushes it to 45%, trick wins concentrate on the eventual
winner, and — the part that matters — **last place ends up absolutely worse
off**, not merely relatively.

The mechanism is not that losers are punished — they are not, they gain
options. It is that the coin they used to receive **automatically** now has a
price, and the player who loses most tricks was collecting most of those coins.
Under the base rule that flow is a **rubber band**: a small, unconditional
subsidy to whoever is behind. Make it voluntary and the subsidy becomes a
trade, which a trailing player can rarely afford — they need the map action
too.

Meanwhile the winner's extra card compounds: more actions, better position,
more tricks won. Trick wins concentrate (39% → 46% for the eventual winner) and
back-to-back wins rise above chance.

## The fix that works: one coin, to the trick's LAST place

Give the winner the extra card, and give **1 gold to the player whose meld
ranked last that trick** — nobody else. One coin enters the game per round,
whatever the player count.

Measured against paying *every* non-winner, which is the obvious alternative:

**3 players**

| | base rule | bonus only | **coin to last** | coin to all |
|---|---|---|---|---|
| rounds | 14.7 | 16.4 | 15.2 | 14.7 |
| leader's score | 28.9 | 32.6 | 31.9 | 32.4 |
| last place's score | 13.0 | 11.1 | **14.3** | 14.3 |
| leader minus last | 15.9 | 21.5 | **17.6** | 18.1 |
| gold earned | 47 | 50 | **53** | 56 |
| food as share of income | 28% | 40% | 37% | 34% |

**4 players** — where the two coin rules diverge most

| | base rule | bonus only | **coin to last** | coin to all |
|---|---|---|---|---|
| rounds | 17.8 | 18.6 | 16.8 | 15.9 |
| leader's score | 31.8 | 32.9 | **31.0** | 35.2 |
| last place's score | 9.3 | 8.9 | **10.4** | 11.2 |
| leader minus last | 22.5 | 24.0 | **20.5** | 24.0 |
| gold earned | 75 | 74 | **74** | 85 |

**2 players** — here the two coin rules are the same rule

| | base rule | bonus only | **coin to last / all** |
|---|---|---|---|
| leader minus last | 10.4 | 13.1 | **8.3** |
| last place's score | 19.7 | 19.7 | **25.1** |
| gold earned | 32 | 37 | 41 |

### Why targeting beats paying everyone

**It does not scale with the player count.** Paying every non-winner injects
*n−1* coins a round, so at four players the economy gains 85 gold instead of 75
— and the extra liquidity helps the leader as much as anyone. That is why "coin
to all" at four players pushes the leader to 35.2 and leaves the gap exactly as
wide as paying nothing (24.0). One coin a round keeps income flat (74 vs 75)
and the help lands where it is needed.

**At four players it is better than the rule you have today.** Gap 20.5 against
the base rule's 22.5, with last place up from 9.3 to 10.4. At two players the
gap closes from 10.4 to 8.3. Only at three players does it come out slightly
wider than today (17.6 vs 15.9), and even there last place finishes better than
it does now.

**What it does not fix** is trick-win persistence: back-to-back wins stay at
44% (vs 45% with no coin, 38% today). A coin does not help you win the next
trick. Whether that matters is a table question — the score gaps say the
compounding is being paid for elsewhere.

## CORRECTION, and how much gold is worth: 1 coin or 2?

The tables above were measured on 25–30 games. Re-run at 50–60 games with 95%
confidence intervals, **most of the gap differences turn out to be noise**, and
one claim made earlier does not survive.

**3 players, 60 games**

| | leader minus last | last place's score |
|---|---|---|
| base rule | 16.6 ±2.2 | 12.5 ±1.3 |
| bonus + **1** gold to last | 17.4 ±2.4 | 14.5 ±1.5 |
| bonus + **2** gold to last | 15.6 ±2.2 | **15.8 ±1.7** |

**4 players, 50 games**

| | leader minus last | last place's score |
|---|---|---|
| base rule | 22.3 ±2.0 | 9.3 ±1.3 |
| bonus + **1** gold to last | 21.3 ±2.5 | 11.1 ±1.4 |
| bonus + **2** gold to last | **18.6 ±2.4** | **13.4 ±1.5** |
| bonus + 1 coin to all | 22.7 ±2.5 | 11.9 ±1.3 |

**The correction.** I previously reported that one coin narrows the four-player
gap from 22.5 to 20.5 and called it better than the current rule. On 50 games
that is 21.3 ±2.5 against 22.3 ±2.0 — fully overlapping. **One coin does not
measurably narrow the gap at any player count.** What it reliably does is raise
the trailing player's score.

**Two coins is the version that does something.** Last place rises from 12.5 to
15.8 at three players and 9.3 to 13.4 at four, both well outside the intervals.
At four players the gap also narrows to 18.6 ±2.4 against 22.3 ±2.0 — the
intervals just touch, so treat it as promising rather than proven.

## Does the gold actually become trick-winning power?

Partly, and the model was understating it. Worth being precise about the chain,
because it is shorter than it looks:

**Rank barely matters for winning tricks.** The trick goes to the most cards;
rank only breaks a tie. Buying a rank-17 card does not let you play more cards
— your meld limit comes from your band, not your hand. So gold does *not* buy
trick power directly.

**The real channel is meld formation.** The market shows the lowest remaining
rank of each suit, so the four on offer sit at similar ranks: buy two and you
hold neighbours, and neighbours meld. Bigger melds win tricks. The second
channel is scoring — bought ranks raise the victory row's median.

**The bot was buying a random suit**, which models the first channel badly. A
meld-aware buyer (`SMART_MARKET`) that buys to complete a set or extend a run
now exists, and it changes the game materially: gold earned rises 47 → 59,
upgrades 21.8 → 26.1, mean meld size 2.16 → 2.26, and every player's score
rises.

**And under that buyer, the second coin stops helping** (3 players, 60 games):

| | leader minus last | last place |
|---|---|---|
| base rule | 17.0 ±2.1 | 13.3 ±1.4 |
| + 1 gold to last | 18.9 ±2.5 | 14.7 ±1.6 |
| + 2 gold to last | 21.4 ±2.2 | 14.4 ±1.5 |

Two coins no longer beat one for the trailing player, and the gap widens. The
likely mechanism is worth knowing regardless of which buyer you trust:

> **"Last in this trick" is not "losing the game."** Over a game the eventual
> leader ranks last in plenty of individual tricks and collects those coins
> too. Doubling the payment doubles that leakage. The rubber band is noisier
> than it looks.

**So the two models disagree about the second coin**, and that is the honest
answer: the buying policy is doing as much work as the rule. A table full of
players who buy deliberately will not behave like either model exactly. This is
a question for the playtest, not the simulator.

## Costs to weigh

**Gold gets tighter, not looser.** Income barely moves (47 → 50) but food rises
sharply as a share of it, **28% → 40%**, because the winner recycles faster and
pays more meals. That is the opposite of the worry, and it is good news: the
food economy currently has no teeth (see findings-limits.md), and this pushes it
toward mattering. With the corrective coin income rises to 56 and food settles
at 34%.

**The winner recycles faster.** Spending an extra card each win burns the hand
sooner, so the winner pays food more often — a self-limiting cost built into the
reward. Recycles rise 23%. This is elegant, and it is where the food pressure
above comes from; worth keeping in any final wording.

**The empty-hand clause is not an edge case.** The winner's hand was empty for
1.8 tricks per game, so the "take a gold instead" fallback fires roughly once or
twice a game. It needs to be in the printed rule, not a footnote.

## Recommendation

**Winner spends one extra card; the trick's last place takes 1 gold. Nothing
else.**

(Originally written as "try 2 gold". That was an artifact of a bot that could
not use a single coin well — see findings-bots.md.)

It reads as two prizes rather than a penalty, nobody tracks how many cards they
may use, a quarter more happens on the map, and the economy is *tighter* rather
than looser — food rises from 28% to 37% of income, which a rule that currently
has no teeth badly needs.

The one thing to watch at the table is trick-win persistence, which the coin
does not address: back-to-back wins run at 44% against a 33% baseline. If the
player who wins the opening tricks visibly runs away with it, the lever to try
is not more gold — it is something that helps a trailing player *win a trick*,
which is a different design problem.

Do not extend the coin to every non-winner. It looks fairer and measures worse:
at four players it inflates income 13% and leaves the gap exactly as wide as
paying nobody at all (22.7 ±2.5 against a 22.3 ±2.0 baseline).

On one versus two coins the simulator does not give a clean answer — one coin
lifts the trailing player but never measurably closes the gap, two coins do
both under a random-buying model and neither under a meld-aware one. Two is the
more interesting thing to test, because a rule that visibly does nothing is
worse than one that might do too much.
