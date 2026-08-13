# Card effects — full review across ranks

## 1 · Every variant

Four rank bands. Every card carries all three effects; only strength changes.

| Band | A · card phase | B · map phase | C · any time |
|---|---|---|---|
| 1–5 | +1 card | 1 cell, **own suit** | 2 gold |
| 6–10 | +1 card, **wins ties** | 1 cell, any suit | 3 gold |
| 11–15 | +2 cards | 2 cells, **own suit** | 4 gold |
| 16–20 | +2 cards, **wins ties** | 2 cells, any suit | 5 gold |

**Distinct types: 4 per category, 12 in all.** A and B are the same 2×2 design —
a *magnitude* axis (+1/+2 cards, 1/2 cells) crossed with a *freedom* axis
(wins ties or not; own suit or any). Magnitude steps up at the halfway point
(band 3); freedom alternates every band. C is one linear axis, 2/3/4/5.

## 2 · Does power scale cleanly? No — and both faults sit at the same seam

Measured over 25 three-player games.

**Effect A — an inversion at bands 2/3.**

| Band | used | took the trick |
|---|---|---|
| 6–10  (+1, wins ties) | 17 | **88.2%** |
| 11–15 (+2, no ties) | 132 | **86.4%** |

A rank-8 card is worth *more* than a rank-13 card for effect A. Melds cluster
small, so +1 usually produces a tie — and tie-winning converts it, while +2
overshoots and still loses genuine ties. The freedom axis is worth more than
the magnitude axis, so withdrawing it at band 3 cancels the upgrade.

**Effect B — a flat spot at bands 2/3.**

| Band | granted | placed | delivered |
|---|---|---|---|
| 6–10  (1 cell, any) | 41 | 41 | **100%** |
| 11–15 (2 cells, own suit) | 176 | 105 | **60%** |
| 16–20 (2 cells, any) | 20 | 16 | **80%** |

Effective cells: **1.00 → 1.19 → 1.60**. Band 3 grants twice as many cells as
band 2 and delivers 19% more, because the own-suit restriction means the second
cell frequently has nowhere legal to go. Then band 4 jumps hard.

**Effect C** is clean: 2/3/4/5, one gold per band, no restriction to interact
with. It is the only category that scales as its rank implies.

**Diagnosis:** the design withdraws freedom at exactly the band where it grants
magnitude, so bands 2 and 3 are near-equals in both A and B. The two middle
rank bands are much closer in power than their ranks suggest — and for A they
are in the wrong order.

**Suggested fix (needs card faces reprinted):** make the axes cumulative rather
than alternating, e.g. A = +1 / +2 / +2 & ties / +3 & ties, and B = 1 own /
1 any / 2 any / 2 any + ignore adjacency. Both become monotone.

## 3 · The turn-order asymmetry — and why weakening ties does not fix it

Trick wins by play position, 20 games each.

| variant | lead | mid | last | spread |
|---|---|---|---|---|
| A off entirely | 36.9% | 31.3% | 31.8% | 5.6 |
| **open declaration (current)** | 23.6% | 31.6% | **44.8%** | **21.2** |
| open, ties only at 16–20 | 24.5% | 31.9% | 43.6% | 19.1 |
| open, earliest wins among tie-winners | 25.1% | 30.2% | 44.8% | 19.7 |
| **blind declaration** | 36.2% | 31.9% | 31.9% | **4.3** |
| blind, ties only at 16–20 | 35.3% | 33.2% | 31.4% | 3.9 |

**Both requested weakenings essentially fail.** Restricting tie-winning to the
top band moves the spread 21.2 → 19.1; resolving declarer-versus-declarer by
earliest play instead of highest rank moves it to 19.7. Neither is close to the
5.6 baseline.

**The cause is information, not ties.** The last player sees every meld already
on the table and spends *exactly* enough to take the trick — +2 cards does that
on its own, with or without a tie-winning clause. Weakening the clause leaves
the sizing advantage untouched.

**What works: declare before the melds are seen.** Committing A blind — you
know only your own meld — restores the baseline exactly: spread 4.3, and the
leader is back on top at 36.2%, which is the tie-break ("earliest played wins")
doing its job again. It also gets *used more*, 8.3 declarations a game against
6.2, because it becomes a genuine gamble rather than a guaranteed conversion.

This is a real change to the rulebook's wording — §09 currently says A is
declared "in the open, as you play your meld — so players after you can still
answer it". That clause is precisely what creates the asymmetry.

**If you want to keep open declaration**, the honest framing is that last seat
is worth ~13 extra points of trick share, oscillating because the winner leads
next. Final scores stay within about two points, so it is a texture problem
rather than a fairness problem.
