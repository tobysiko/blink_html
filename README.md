# Blink — v0.22

**Climbing the Ladder of Civilization** — a 2–4 player game for 60–120 minutes
that alternates between trick-taking card play and actions on a growing hex map.
Designed by Toby Siko.

Every round has two halves: everyone plays a meld of cards, then everyone spends
those same cards on the map — settling units, exploring new tiles, attacking, or
cashing them for gold. Your player board's tier ladder turns population into
everything else: bigger melds, longer strides, a higher rank cap, and a larger
food bill.

> Prototype. The rules are still moving; see `RULEBOOK-CORRECTIONS.md` for the
> open decisions and where the documents and the simulation currently disagree.

## What is here

| path | what it is |
|---|---|
| `Blink-rules-v0.22.pdf` | the rulebook · `-bw` is the printer-friendly build |
| `Blink-deck-*.pdf`, `Blink-player-board-*.pdf`, `Blink-first-game.pdf` | print-and-play components |
| `PRINT-AND-PLAY.md` | what to print and how to assemble it |
| `source/` | the HTML and SVG the PDFs are built from |
| `sim/` | the Python rules engine, the bots, and the findings behind each design decision |
| `app/` | the browser prototype — engine, client, tests |
| `deploy/` | the built single-page app, ready to host |
| `RULEBOOK-CORRECTIONS.md` | audit of rulebook vs player board vs simulation |

## Play it in a browser

`Blink-play-v0.22.html` is one self-contained file — no server, no network, no
dependencies. Double-click it. You play one seat; the others are run by the bot
the simulation was tuned with.

To build it from source:

```
cd app
node build.js
```

That writes both `../Blink-play-v0.22.html` and `deploy/index.html` (the same
page, minified, with the meta tags a hosted copy wants).

**On a phone**, the file must be *served* — iOS Files previews HTML in Quick
Look, which renders the page but never runs its scripts. The page detects this
and says so rather than appearing broken. See `deploy/DEPLOY.md`.

## Tests

```
cd app
node smoke.js        # 180 bot-only games: unit, tile and connectivity invariants
node human_test.js   # 240 games driving a human seat; every request type
node verify.js       # 900 games, 16 metrics, to diff against the Python sim
```

Those need only node. Two more drive the real DOM and want jsdom
(`npm install jsdom`):

```
node visible_test.js         # the app is VISIBLE after Start, not merely built
node nojs_test.js            # the no-JavaScript notice appears, and only then
node ui_playthrough_test.js  # clicks four whole games through the interface
```

Design questions are answered by measurement, not argument. `deck_test.js`,
`vrow_test.js`, `tier_test.js`, `objectives_test.js` and `scoring_audit.js` each
A/B one rule against another on matched seeds.

## Simulation

`sim/` is the Python engine the balance work was done on, with a `findings-*.md`
for each question asked of it. `app/engine.js` is a port of it, and `verify.js`
checks the two agree distributionally — they use different random number
generators, so games never match card for card.

## Rights

© Toby Siko. All rights reserved. The rules, art, and card and board designs are
not licensed for redistribution or commercial use. Print-and-play files are here
so people can play the prototype and tell the designer what is wrong with it.
