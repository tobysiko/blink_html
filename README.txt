BLINK v0.22
===========
Base game rules, teaching booklet, print-and-play components, and the rules
simulator used to test them.

The version number lives in ONE place: source/version.py. Every builder imports
it, so bumping the version renames the rulebook and restamps every document,
booklet footer, player board and card back in one edit.


WHAT IS IN THIS FOLDER
----------------------
Every document exists in colour and in a black-and-white version (-bw) that is
safe on a mono laser printer.

  Blink-rules-v0.22          Main rulebook
  Blink-first-game           Teaching booklet, 3-player scripted walkthrough
  Blink-card-effects         Victory-card effect reference
  Blink-map-objectives       Advanced module: secret map objectives
                             NOT re-tuned for v0.21 - leave out of a first game
  Blink-playtest-sheet       One A4 page to fill in at the table
  Blink-variants             Variants and shelved rules: pattern placement,
                             per-tier population limits, the winner bonus card,
                             combination melds, super melds, friends of 10s.
                             None are base game.
  Blink-deck-colour / -bw    Print-and-play main deck, 80 cards + backs
  Blink-objectives-colour    Print-and-play objective deck, 12 cards + backs
  Blink-player-board-A4      Player board, one per player, print at 100%

  PRINT-AND-PLAY.md          How to print and assemble the above
  sim/                       Rules engine, bots and findings
  source/                    Every generator; nothing here is hand-written HTML


BUILDING
--------
  cd source && sh build_pdfs.sh

That runs every generator, the figure checker, the black-and-white pass and
wkhtmltopdf. Nothing in the parent folder should ever be edited by hand.

wkhtmltopdf is the reference renderer. The PDFs currently in this folder were
rendered with WeasyPrint because wkhtmltopdf could not be installed in the
sandbox; they paginate differently and render the masthead at the wrong size,
because WeasyPrint does not support the CSS clamp() the display headings use.
Re-run build_pdfs.sh locally before sending anything to a publisher.


HOW THE GENERATORS RELATE
-------------------------
The point of the pipeline is that a rule exists once and every document that
mentions it is derived.

  version.py        the version string; imported by all builders
  figs.py           drawing helpers (hexes, prisms, units, cards, gold)
  build_figs.py     -> figs.json, 22 figures
  check_figs.py     fails the build if a figure is clipped or overflows
  pattern_figs.py   the objective pattern diagrams
  cardstock.py      card geometry, terrain glyphs, hatch patterns, mono_svg()

  build_html.py     -> the rulebook. Owns the CSS everything else reuses.
  build_tutorial.py -> First Game. Imports CSS and figures from build_html.
  build_effects.py  -> card effects. Its per-rank table is derived from the
                       same four rank bands the rulebook prints.
  build_module.py   -> map objectives booklet. Owns DECK.
  build_playtest.py -> the one-page playtest sheet. Reuses the rulebook CSS.
  build_variants.py -> variants and shelved rules booklet.
  build_cards.py    -> main deck. Effect text imported from build_effects.
  build_objcards.py -> objective deck. Wording from DECK, art from pattern_figs.
  board_a4.py       -> player board SVG.
  build_bw.py       post-processes the HTML the others just produced, rewriting
                    the palette and hatching the figures. NOT a second set of
                    builders, so a mono booklet cannot lag behind its colour twin.


WHAT CHANGED IN v0.21 — melds no longer land as patterns
--------------------------------------------------------
The map-placement pattern game (connected shapes, straights walked in rank
order, set clusters) is GONE. A meld now only competes for the trick; then
each of its cards is spent individually — settle a unit / explore a tile /
attack / take 1 gold — on any cell in reach (a tile you occupy or adjacent
to one you occupy), suit matching terrain. Cards resolve one at a time in
any order, each seeing the map as the last one left it.

New free-action layer, once per own map phase:
  Free moves       band number (1/2/3/4): by land across your own connected
                   units onto a free adjacent tile, or by sea across open
                   Ocean. Never an attack. Replaces shift and ocean drift.
  Reallocate gold  freely between reserve, food slots and fortifications;
                   research (upgrade) spending is one-way
  Effect B         capped at ONE victory card per turn

Renames: upkeep -> food (coins pre-placed on the band's food slots, eaten on
recycle); upgrades -> research. Player board gains a MOVES column.
The sim/ engine HAS been ported to v0.21 — see sim/findings-v021-port.md.
Headline: total gold income is unchanged but cards are now cashed 38-46% of
the time by choice rather than by accident; games run 10-20% shorter; the
free-move allowance is not yet validated (the bot policy is in the way).


WHAT CHANGED IN v0.22
---------------------
  Melds        ONE rule: any cards whose ranks form an unbroken run.
               Duplicates free, suits irrelevant. The straight/set/full-house
               taxonomy is gone, and with it ten figures.
  Tiers        Five, renamed: Tribe / Settlement / Kingdom / Empire /
               Civilization, units 2/4/6/4/4 = 20. Meld 2-6, moves 1-5,
               food 0-4, rank cap 13/15/17/20/none.
  Ascension    Reaching a tier pays its printed coins once: 1 / 2 / 3 / 4.
  Trick        Winner spends one extra card; last-ranked meld takes 1 gold;
               anyone who MATCHED the winner's card count and lost discards
               one card to the shared pile.
  Refill       Hand empty -> feed, take back your discard, draw from the
               SHARED pile up to ten. The ten-card invariant is gone: your
               deck now churns.
  Tiebreak     Most cards, then highest card, then next-highest, ... then
               earliest played. Never a tie.
  Effect B     Rewritten as COLONIES: new tiles + units + fortifications, the
               coins from the GENERAL SUPPLY. Touch-two still applies; reach
               does not.
  Water        Your first sea move each turn grants one free explore of ANY
               terrain.
  Market       One shuffled upgrade deck + a 2x3 face-up grid. One upgrade per
               turn: draw onto the grid, retire, pay 1, take a card at or
               below your tier's rank cap, refill.
  Majority     Terrain majority requires ALL your units on that terrain to
               form ONE connected group.
  End          Last unit placed, or the UPGRADE DECK runs out.


SETTLED RULES (these were open once; they are not any more)
-----------------------------------------------------------
  Trick reward     winner spends ONE EXTRA card from hand (1 gold if the hand
                   is empty); the meld that ranked LAST takes 1 gold; nobody is
                   docked. Replaced "losers spend one fewer + 1 gold" — that
                   rule had the worst score floor of six structures tested at
                   every player count, and asked players to track a number.
                   See sim/findings-trick-reward.md. NOT YET PLAYED.
  Bands            2/4/6/8 units, meld limits 2/3/4/5, upkeep free/1/2/3
  Upkeep           NOT cumulative — pay the current band only, on recycle
  Starvation       proportional: return one unit per gold short
  Returned units   fill the LOWEST band with a free slot
  Explore legality touch-two: a new tile must touch at least two existing ones
  Tile supply      open. No bag, no market; all tiles visible until they run out
  Cashing cards    any card may take 1 gold instead of acting; no restriction
  Attack cost      paid per card spent attacking, not per tile
  Fortifying       your own map phase only, one coin per unit
  Effect A         declared BLIND, before any meld is played
  Effect B         used in your own map phase; settles only
  End trigger      a player places their last unit, or an advanced deck runs dry
  Disconnection    allowed; fragments survive

Still unratified, and flagged rather than hidden: the 3-player suit balance in
the deal, and "win ties" resolved by the higher-ranked spent card when two
players both declare it.

OPEN FOR THE FIRST v0.21 PLAYTEST (the playtest sheet asks exactly these)
  free moves     1/2/3/4 per band is UNVALIDATED - the sim could not separate
                 the rule from the bot policy. Watch whether they get used.
  meld shape     shapes no longer reach the map. Does anyone still care which
                 meld they hold?
  cashing rate   the sim predicts 38-46% of cards cashed. Count it.
  end trigger    the sim says a suit always runs dry before anyone places a
                 twentieth unit. Does that ending land?
  food slots     pre-placing coins, and pulling them back off fortifications,
                 has never been done by a human.


SIMULATOR
---------
sim/ holds a full rules engine for v0.21 with invariant checks that assert the
physical box is intact every round. See sim/README.txt. It has found several
real bugs in both the engine and the rules, and every quantitative claim in the
findings files came from it.

Read sim/README.txt's SAMPLE SIZE note before trusting any objective rate.


HISTORY
-------
This folder supersedes v0.19 and the v0.18 documents in the parent directory.
The audit trail is kept there: ../v018-audit.md and ../v019-readiness-review.md
record what changed between versions and why. Those filenames are historical
and are correct as they stand.
