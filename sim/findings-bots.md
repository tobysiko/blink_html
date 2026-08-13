# Better bots — and what they changed

`pro_bot`, `bot_h2h.py`. Every claim below is a head-to-head result, because a
bot is only better if it beats the other one at the table.

## What was wrong with `smart_bot`

Four weaknesses, in descending order of how much they turned out to matter:

1. **It drafted at random.** `_deal` shuffled the offered cards and kept the
   first *n*. No player has ever drafted like that.
2. **It valued the trick with a flat constant** — `0.35 × cards` — with no
   notion of whether the meld could actually win, even though every rival's
   meld limit is printed on their board.
3. **It cashed on a fixed threshold**, ignoring whether food was covered or an
   upgrade was one coin away.
4. **It moved units by spreading them** toward open ground, which measured
   *worse than not moving at all* (see findings-v021-port.md §4).

## `pro_bot`

- **Drafts for meldability** — keeps the card that most improves `hand_power`,
  which rewards pairs and, more heavily, *adjacent ranks*.
- **Estimates the trick.** Compares its meld size against the largest limit any
  rival could answer with, and values winning at roughly one card's map action
  plus tempo.
- **Values the hand it keeps**, so it will not dump its only pair to play one
  extra card today.
- **Cashes situationally** — threshold 2.2 when food is uncovered, 0.4 when
  sitting on spare gold.
- **Moves only to reinforce or evacuate**, never to spread.

## It wins

One pro seat against two `smart_bot`s, 40 seeds × 3 seat rotations so seat
order and deal luck cancel:

| | pro side wins | pro mean score | smart mean score |
|---|---|---|---|
| all pro policies on | **45.4% ±8.9** | 24.3 | 21.2 |

Chance is 33%. Clear.

## Ablation — the draft is nearly the whole story

Same test, one policy disabled at a time:

| disabled | pro wins | vs chance |
|---|---|---|
| nothing (all on) | 45.4% ±8.9 | +12 |
| the meld chooser | 40.4% ±8.8 | +7 |
| situational cashing | 41.7% ±8.8 | +8 |
| reinforce/evacuate moves | 43.3% ±8.9 | +10 |
| **the draft** | **33.3% ±8.4** | **+0** |

Remove the draft and the pro bot is exactly average. **Drafting is where the
bot's entire edge lives**; the other three policies are worth a few points
between them.

## What this changes about earlier findings

### 1. The starting-hand answer needs qualifying, not retracting

Measured again with *every* seat drafting properly, hand quality's correlation
with final score rises from 0.06 to **0.17** — still weak (about 3% of
variance), and the spread of hand quality across the table barely moves
(1.76 → 1.69).

So the two statements are both true and they are about different things:

- **The deal is close to fair.** Even against competent drafters, what you are
  dealt predicts very little.
- **Drafting is a real skill lever.** A player who drafts for adjacency beats
  one who does not, decisively.

That is an argument *for* keeping the draft as it stands, and against replacing
it with fixed symmetric decks — the draft is not decoration, it is the opening
skill of the game. It is not an argument for card-by-card drafting: the lever
already exists.

### 2. The winner-bonus recommendation FLIPS from 2 gold to 1

Re-run with pro bots in every seat, 50 games, three players:

| | leader minus last | last place's score | cards cashed |
|---|---|---|---|
| base rule | 16.3 ±2.2 | 15.2 ±1.7 | 47% |
| bonus + **1** gold to last | **14.8 ±2.0** | **18.7 ±1.7** | 33% |
| bonus + **2** gold to last | 16.1 ±2.0 | 18.4 ±1.8 | 28% |

Under the weaker bot, one coin did nothing to the gap and two coins were needed
to help last place. **Under competent play, one coin does both jobs and two
coins are worse than one** — the gap goes back up and last place gains nothing
further.

The likely reason is the same leak identified before: "last in this trick" is
not "losing the game", so doubling the payment doubles what reaches the eventual
leader. A stronger player converts that leak more efficiently.

**Revised recommendation: winner spends one extra card, the trick's last place
takes 1 gold.** The earlier "try 2" was an artifact of a bot that could not use
a single coin well.

## Standing caveat

Every finding in this folder dated before this file used `smart_bot`. The two
re-tested above moved. The others — the v0.21 port economy, the population
ladders, the objectives rates — have **not** been re-run against `pro_bot`, and
the ladder findings in particular involve exactly the kind of long-horizon
planning a better bot does differently. Treat them as provisional.
