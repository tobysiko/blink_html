# Does the starting hand decide the game?

> **QUALIFIED — read findings-bots.md.** The numbers below come from a sim in
> which *nobody drafted*: cards were kept at random. With every seat drafting
> for meldability the correlation of hand quality with final score rises from
> 0.06 to 0.17 — still weak. But drafting *skill* turns out to be the single
> largest edge a bot can have, which is an argument for keeping the draft
> exactly as it is.

`hand_test.py` plus the stacked-deal and rotation experiments below. Smart bots,
60–80 games at three players.

**The worry.** One player is dealt most of the top ranks, the draft lets them
keep several, and the game is decided before it starts.

**Short answer: no, and the specific fear is backwards.** A hand of top ranks is
a *below-average* hand. What actually matters is rank **adjacency**, and even
that is weak.

## 1. Natural deals: almost no signal

Correlation of each hand property with that player's final score, 80 games:

| hand property | correlation with final score |
|---|---|
| longest run of consecutive ranks | 0.06 |
| biggest set (same rank) | 0.03 |
| cards adjacent to another rank held | **0.10** |
| sum of ranks | −0.00 |

All negligible. The most meldable starting hand won **30%** of games at three
players, against a 33% chance baseline — no advantage at all.

**The rotation test.** For each seed, the same three hands were played three
times, rotated between seats, with every later random draw identical:

| | share of seeds |
|---|---|
| the same **hand** won all three rotations | 18% |
| the same **seat** won all three rotations | 3% |
| chance, if the result were random | 11% |

So the hand carries a *little* signal (18% against 11%) and seat position
carries none. Whatever decides a game of Blink, it is mostly not the deal.

## 2. The pathological deal — and why it fails

Seat 0 was force-fed the top ranks; everyone else got the remainder:

| seat 0 holds | seat 0 win rate | its score | others' mean |
|---|---|---|---|
| all four **10s** + filler | **22%** | 17.4 | 22.1 |
| all **10s and 9s** (8 cards) | **18%** | 17.1 | 22.7 |
| all **10s, 9s and 8s** (10 cards) | **45%** | 23.7 | 21.0 |

Chance is 33%.

**Hoarding one rank is actively bad.** Four 10s make exactly one meld — a
quadruple — playable only once you have cleared two bands. They make no runs at
all, and rank 10 is the *top* of the starting deck, so nothing in hand can
extend them upward. The remaining six filler cards are random. A player dealt
"all the best cards" ends up 4.7 points behind the table.

**A consecutive block is the real prize.** 8s, 9s and 10s across four suits is
runs everywhere, sets everywhere, two-pair and full houses — and it wins 45%.
The dangerous hand is not *high*, it is *contiguous*.

This matters for your proposed fix: **equalising the top ranks addresses the
wrong variable.** Measured, sharing the 9s and 10s out evenly cut the top-rank
spread from 2.1 to 1.0 cards and did nothing useful to the score spread
(16.6 → 18.4, within noise).

## 3. Why the deal matters so little

Not for the reason I first assumed. I guessed upgrades churn the deck and
dilute a lucky start. **They do not:** at the end of a game **90% of your
original ten cards are still in your playing deck.** The bot buys a high card
and then retires *that* card to the victory row rather than a starting card,
because the row scores its centre rank. Your opening ten persists almost
intact.

The real reasons look structural:

- **The meld limit binds harder than the hand.** You start able to play two
  cards. A hand full of quadruples cannot express itself until two bands are
  clear, by which time the game is half over.
- **Score is mostly map, not cards.** Units placed and terrain majorities
  dominate the final total; the victory row is one term of three.
- **Natural deals are narrow.** The starting deck is ranks 3–10 at three
  players, so the gap between the best and worst hand at a table is small —
  longest run varies by 2.7 ranks, biggest set by 0.8.

## 4. What this means for the alternatives

**Card-by-card drafting (ten passes)** — not justified by balance. It would buy
almost nothing the current draft does not, at a large cost in table time.

**Equal top ranks per player** — addresses a variable that does not predict
anything, and measured no improvement. Do not do this.

**Fixed symmetric starting decks** — would remove a variance that is already
near zero, and would cost the draft entirely. Worth it only if you want
tournament-grade determinism.

**If you want to reduce deal luck anyway**, the variable to equalise is
**adjacency** — deal so that each player's ten cards contain a similar number
of consecutive-rank neighbours. That is the property with the (weak) signal and
the one the stacked test showed can reach 45%.

## Caveats worth stating

**The sim's draft kept cards at random.** ~~It models the deal, not drafting
skill.~~ **Now answered:** a drafting bot (`pro_bot`) was built and it beats the
random-keeping bot 45.4% to a 33% baseline — and disabling *only* its draft
drops it to exactly 33%. Drafting is the whole of that edge. With every seat
drafting well the hand-quality correlation is 0.17 and the spread of hand
quality across the table is unchanged, so the conclusion above survives: the
deal is close to fair, but the draft is a genuine skill lever rather than a
formality.

**The bot's upgrade policy retires bought cards, not starting ones.** That is a
plausible strategy but not the only one, and it is why the starting hand
persists. A player who instead retires their weak starting cards would churn
the deck much faster and dilute a bad deal — which would make the deal matter
even less than measured here.
