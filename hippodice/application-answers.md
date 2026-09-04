# Hippodice Competition 2027 — application form answers

Form: https://hippodice-competition.net/en/info-participation/application-form/
Deadline: **5 September 2026**. Digital form only; physical prototypes are requested
later (24 Oct – 7 Nov) from the games that get through.

## About the game

| Field | Answer |
|---|---|
| Title of the game | **Blink** |
| Age recommendation | **10** |
| Number of players: at least | **2** |
| Number of players: maximum | **4** |
| Playing time | **61–90 Min.** — the bucket for the recommended 3–4 players. The rulebook says 45–90 because two-player games are genuinely faster; the two do not contradict, and the form asks about the recommended count. |
| Target group | **connoisseurs** (Kennerspiel — BGG-weight estimate ~2.9, Arnak / Everdell territory) |
| Type | **board game** (defensible either way; the map, tiles and boards outweigh the deck. "card game" would undersell the terrain, which is the part publishers have praised) |
| Mode | **competitive** |
| Properties and special features | **area control · card drafting · tile placement · 2-player** |
| Properties: other (40 chars) | **trick-taking** |
| Upload game description (PDF) | `hippodice/Blink-game-description.pdf` |
| Upload game rules (PDF) | `hippodice/Blink-rules-v0.24.pdf` (1.4 MB, well under the 25 MB cap) |
| Link to a video-description | *leave blank* — the pitch video on the site is from July and shows pre-v0.22 rules. Better nothing than something contradicting the rulebook. |

## About the participant

| Field | Answer |
|---|---|
| Company Name | **Deep Diversions** |
| Name of the game designer | **Tobias Sikosek** (the credit "Toby Siko" is the pen name; the form wants the person) |
| Additional name(s)? | **No** |
| Street / ZIP / town / country | *yours to fill in* |
| E-mail address | toby.sikosek@gmail.com |
| Telephone number | *yours to fill in* |
| Other comments (500 char limit) | see below |

### Other comments — draft (312 characters)

> Blink can be played in the browser at deep-diversions.com/blink — 2–4 players, against bots
> or through a shared table link — if that is useful before prototypes are requested. The
> rulebook, a card-effects reference and the print-and-play files are on the same page. A
> physical prototype can be sent at any point.

## Playing time — settled 4 Sep

The rulebook, the site and the one-pager said **60–120**; the form's longest bucket is 61–90.
That combination was the one to avoid — a juror who opens both sees the contradiction.

**Now 45–90 everywhere**, derived from the simulator rather than guessed. 400 games per player
count:

| players | rounds (mean / median / p90 / max) | decisions a person makes per game |
|---|---|---|
| 2 | 10.7 / 11 / 13 / 14 | 112 (p90 139) |
| 3 | 11.2 / 11 / 13 / 17 | 158 (p90 190) |
| 4 | 12.0 / 12 / 14 / 20 | 203 (p90 252) |

A "decision" is one card resolved, one duel, one recycle or one research — the things that take
time at a table. At ~18 seconds each plus a card phase per round, four players comes to roughly
70 minutes typical and ~85 at the long tail; two players to roughly 40–50. The market-thinning
end trigger is what bounds it, and the round counts show it bounding tightly: the p90 is two
rounds above the median at every player count.

**This is a model, not a stopwatch.** Timing two or three real games is still the right thing
to do, and it is the first thing to check in the prototype round. But 45–90 is defensible and
consistent, which "60–120 alongside a 61–90 form answer" was not.

## Checklist before submitting

- [x] **Playing time settled** — 45–90 in the rulebook and the one-pager, 61–90 on the form
- [x] **Rules PDF is the current v0.24** — rebuilt 4 Sep from `source/Blink-rules-v0.24.html`,
      28 pages, 640 KB. The copy that was in this folder was a **31 Aug** snapshot predating the
      §07 wall rewrite; a stale duplicate of the HTML at the workshop root (1 Sep, still saying
      60–120) was what made that easy to miss and has been moved to `_to_delete/`.
- [x] **Game description PDF final** — 1 page, 406 words (Hippodice wants 250–500)
- [x] **Typography actually in the files.** Every shipped PDF was checked on 4 Sep and *none*
      had Fraunces or IBM Plex Sans embedded — the rulebook bound for this entry was set in
      DejaVu Sans and Liberation Serif, because the builders link the fonts from Google Fonts
      and that fetch had been failing silently. `source/embed_fonts.py` now inlines them before
      any render, and `check_fonts.py` was reading `/BaseFont` only, so it could not see a
      variable font and reported a false negative on a correct PDF. Both fixed.
- [ ] v0.24 pushed live (deep-diversions.com/blink)
- [ ] Re-run `build_pdfs.sh` on the Mac so the remaining four PDFs (both boards, the blank
      board, the b/w rulebook) pick up the embedded fonts — not needed for the entry itself
- [ ] Address and telephone filled in
- [ ] Terms of participation read and the box ticked
