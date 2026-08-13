BLINK v0.22 — GAME SIMULATOR
=============================

READ THIS FIRST: everything below the CURRENT STATE block is a CHRONOLOGICAL
LOG, kept in the order the work happened. Earlier entries are superseded by
later ones — several describe defaults that have since changed, or a proposal
that was later adopted. Do not quote a number from the log without checking it
against the current state.


CURRENT STATE (v0.22)
---------------------
PORTED TO v0.22 — see findings-v022-port.md. Melds are now ONE rule (ranks
form an unbroken run, duplicates free, suits irrelevant); five tiers 2/4/6/4/4
with ascension coins and rank caps; match-the-winner discard into a SHARED
pile that hands refill from; single shuffled upgrade deck + 2x3 grid, one
upgrade per turn; Effect B founds colonies paid from the general supply;
water advantage; connected-patch majority; end trigger is the upgrade deck.

HEADLINE: games are ~40% SHORTER (13.8 -> 8.7 rounds at 3p) and the upgrade
deck ends 38-40 of every 40 games. Doubling the deck restores v0.21 length and
hands the ending back to the expansion race. Effect B now takes 96% of spent
victory cards. Ascension is 42% of all gold earned.

Superseded note, kept for history — PORTED TO v0.21. Melds no longer place patterns: a meld wins the trick and
nothing more, and each of its cards is then spent independently — settle /
explore / attack / take 1 gold — on any cell in reach, resolved one at a time
with the map re-read between cards. See findings-v021-port.md.

Engine defaults, all ON:
  PROPORTIONAL_STARVATION, USE_EFFECT_A/B/C, USE_FORTIFY, USE_MOVES,
  USE_RECLAIM, CASH_FOR_FOOD, USE_HOLD_BACK;
  FORTIFY_POLICY = "targeted";  A_TIMING = "blind";  CASH_THRESHOLD = 1.0
  LIMIT_LADDER = None  (a key of LADDERS switches on per-tier population
  limits; the TILE OWNER's band applies)
  WINNER_BONUS_CARD = True    <-- NOW THE BASE RULE. Winner spends one extra
  card from hand, or
  takes 1 gold if the hand is empty; nobody is docked)
  LOSER_CONSOLATION = "last"  <-- BASE RULE. Pays the seat whose meld
  ranked last that trick; CONSOLATION_GOLD sets the amount. One recipient per
  round regardless of player count. See findings-winner-bonus.md)
  CONSOLATION_GOLD = 1        (1 at 3 players, 2 at 2 and 4 players)
  GIVE_BONUS_CARD = True      (set False with WINNER_BONUS_CARD=True for
  the "no trick reward at all" control)
  SMART_MARKET = False        (buy market cards to complete a set or extend a
  run, instead of a random suit. Materially changes the economy: gold 47->59,
  upgrades 21.8->26.1. The random buyer UNDERSTATES how much gold becomes
  trick-winning power, so run both before trusting a market finding)
  STARVE_CULLS_STACKS = True  (with a ladder on: after starvation drops your
  band, stacks over the new limit shed units back to the reserve, looping until
  stable. Combat does NOT cull. Measured dormant — see findings-limits.md)
Bands are 2/4/6/8, free moves 1/2/3/4. USE_SHIFT and USE_DRIFT are gone —
free moves replace both. DISCONNECT_PENALTY was removed from the engine
entirely rather than left switched off — a dormant speculative mechanic is how
a sim drifts from its rules.

THE ONE THING TO KNOW BEFORE READING THE LOG BELOW: every finding dated before
the v0.21 port was measured on the pattern-placement engine. Numbers about meld
shapes, placement rates, straights vs sets, and all objective rates DO NOT
CARRY OVER. The economy and band findings largely do; check them against
findings-v021-port.md.

Ported and current:
  run.py         invariants + conservation, random-legal bots
  port_check.py  v0.20 vs v0.21 on identical seeds, smart bots
  econ_check.py  the gold -> upgrades -> market clock chain
  moves_test.py  end triggers, and free-move sensitivity
  limits_test.py per-tier population limits (LADDERS) vs fixed HOLDS
  NOTE: every script other than run.py measures v0.21 rules unless it has
  been re-checked against the v0.22 engine. The findings files dated before
  findings-v022-port.md describe DIFFERENT RULES.
  cull_test.py   does famine-culling of over-limit stacks cascade? (no)
  bonus_test.py  winner spends a bonus card instead of docking the losers
  bot_h2h.py     pro_bot vs smart_bot head to head, seats rotated
  reward_test.py all six trick-reward structures, 2/3/4 players
                 (THE answer on trick rewards: findings-trick-reward.md)
  hand_test.py   does the starting hand decide the game? (barely — and
                 hoarding top ranks is a BAD hand. See
                 findings-starting-hand.md)
  obj_v21.py     objective rates under v0.21 (the scorer is engine-free)

NOT ported (they assume pattern placement):
  seek3.py, obj2.py, passive.py, objectives.py — every objective rate
  combo_test.py, tiecheck.py, band3.py, bands_test.py, gapfill.py, rerun.py
  compare.py, h2h.py additionally call greedy_bot/turtle_bot/mixed, which have
  not existed in the engine for some time — that breakage predates the port.

BOTS: use pro_bot. smart_bot drafts AT RANDOM and is measurably weaker
(loses 45/33 head to head). Findings measured with smart_bot are marked
provisional; two of them changed when re-run. See findings-bots.md.
  g = Game(3, seed=s, bot=pro_bot); g.smart = True
  g.pro = set(range(3)); g._deal()      # pro seats must redeal to draft

Which script to use:
  run.py      random-legal bots + the invariant and conservation checks
  seek3.py    THE tool for objective rates. Two objectives per batch, 60-120
              samples each, prints 95% intervals.
  passive.py  passive (unsought) objective rates, for comparison with seek3
  obj2.py     the current objective scorers
  compare.py, h2h.py, ab_test.py, fort_test.py, band3.py   policy experiments

  objectives.py, seek.py, seek2.py are SUPERSEDED. objectives.py scores the OLD
  twelve-card deck, which no longer exists; seek/seek2 use sample sizes too
  small to decide anything. Kept only so the log below can be read.

Two harness bugs worth remembering, both of which produced confident nonsense:
  - Game.__init__ is (n, seed=0, bot=None). Calling Game(3, smart_bot) passes
    the BOT AS THE SEED; Python hashes it to one constant per process, so every
    game in a run is identical and different runs disagree. Always use keywords.
  - Objective rates on 20-30 samples carry a +/-20 point interval. See the
    SAMPLE SIZE note at the end.

The current objective deck is twelve mixed-terrain chains, all worth 4 points;
see findings-objectives-final.md and findings-lookout.md. _chain requires only
that the three tiles are ADJACENT IN ORDER — bends count, straight lines are not
required, and every measured rate already includes both.


THE LOG
-------
engine.py   Full rules engine for v0.20. Cards, the draft, hand/recycle and the
            ten-card invariant, trick resolution, meld enumeration, placement
            enumeration on the hex map, settle/explore/attack/take-gold, bands
            and non-cumulative upkeep, the card market and victory row, both end
            triggers, and scoring. Simplifications are listed at the bottom of
            the file (SIMPLIFICATIONS).
run.py      Random-legal bots + the invariant checks. Run: python3 run.py 150
compare.py  Policy comparison and a head-to-head. Run: python3 compare.py

THE INVARIANTS ARE THE POINT
----------------------------
run.check() asserts, after every single round of every game:
  - each player holds exactly ten cards across hand + discard + table
  - each player's 20 units are all accounted for, on the map or in the reserve
  - no tile is overstacked and no tile has two owners
  - the map is one connected mass
  - every tile placed after setup touches at least two others
These caught a real bug on the first run: setup put a unit on the map without
taking it out of the player's reserve.

NOT the same file as ../../blink_sim.py, which models the v0.12 design (per-
terrain unit tracks, scaling population limits, defence bonuses) and has been
obsolete since v0.18.

WHAT THE FIRST RUN FOUND
------------------------
bands.png        the bug: band level crashing to Founding all game
bands_fixed.png  the same game after the fix: a staircase

Combat, not upkeep, is what was emptying the map: of 58 units placed in a
3-player game, 18 were killed by attacks and only 0.8 were starved off by
upkeep. But the damage was done by a rule I had invented and never had
ratified - "returned units fill the TOPMOST band with a free slot". Because
your current band is the topmost one still holding units, a single returned
unit landed in Founding and reset the meld limit to 2, even for a player with
eighteen units on the map.

Changed to: a returned unit goes into the LOWEST band with a free slot - the
one most recently emptied. Time spent stuck in Founding fell from 51% to 24%
and the band curve became a progression instead of noise. Rulebook §08 updated
to match.

COMPONENT CONSERVATION
----------------------
run.conservation() now asserts, every round of every game, that the physical
box is intact:

  TILES  bag + market + map = 60, and exactly 15 of each terrain
  CARDS  every card in a hand, discard, meld, victory row, deck or market slot
         appears EXACTLY ONCE, and the total equals what was dealt
  UNITS  each player's 20 units are on the map or in their reserve

Units were already covered. Tiles and cards were not, and adding the check
found a real bug within 25 games: the engine was CREATING tiles out of nothing.
An explore's legality is tested when the meld is enumerated, but an earlier
cell of the same meld can take the last tile of that suit before the later
cell resolves. do_explore() then dug an empty bag and wrote the terrain in
anyway - 16 oceans in a 15-ocean box.

do_explore() now returns False when the box has no such tile, and the caller
takes gold instead. Conservation holds over 180 games at 2, 3 and 4 players.
It fires about 0.24 times per game, so it is rare - which is exactly why an
assertion was the only way to find it.

NOTE ON REPRESENTATION
Units are counts, not objects: a reserve is four integers and a tile holds a
list of owner ids. Cards and tiles are value objects - (rank, suit) tuples and
terrain strings - which is safe here because every (rank, suit) is unique in
the deck and tiles of a terrain are interchangeable. Conservation is therefore
enforced by assertion rather than by construction. That is weaker than handing
out numbered objects, but it caught this bug, and it is what a physical box
guarantees anyway.

THE MAP IS A GRAPH OF TILE OBJECTS
----------------------------------
A Tile is one physical hex and owns everything about itself:

    cell      its fixed position, which never changes
    terrain   plains / forest / ocean / mountain
    units     owner ids standing on it (single-owner while occupied)
    gold      fortification coins, at most one per unit
    link      the six neighbour slots: direction -> Tile, or None if unexplored

Adding a tile wires it to its neighbours in BOTH directions. check_graph()
asserts every round that links are symmetric, that they agree with the
geometry, that no tile has two owners, that none is overstacked, and that no
tile carries fortification gold with no units under it.

Placement enumeration walks that graph. A meld's pattern is a walk over cells;
from a Tile we follow its six links and its empty slots, and only from an empty
slot - which has no object yet - do we fall back to coordinate arithmetic.
adjacent() is the one place that decision is made.

WHY IT MATTERED
The old version kept two parallel dicts, terr{cell->terrain} and
stack{cell->[owners]}, which could disagree. _place() used
stack.setdefault(cell, []) - it would have created units on a cell that was
not a tile at all. That can no longer be expressed: units live on a Tile or
they do not exist.

Fortification is now on the tile and an attack takes the gold before it takes
a unit (§07). No bot fortifies yet, so the field is correct but unexercised.

BOTS THAT ACTUALLY DECIDE  (findings-smart.txt)
-----------------------------------------------
Until now placement was random.choice() over the legal options: bots chose
WHAT to play sensibly and WHERE to put it by coin flip. smart_bot adds a
readable scoring function (value_placement) - settling is worth more than
gold, contesting a terrain majority is worth more than padding one you
already lead, attacking is discounted by what it costs and pays only when it
clears a tile outright - and the upgrade policy now retires HIGH cards to the
victory row instead of the weakest.

WHAT CHANGED, AND WHAT DID NOT

  Victory row   21-24% of score -> 33-42%. The old 25% was an artefact of
                bots retiring their worst cards. The row is a major scoring
                engine, not a side dish.
  Explores      48-51 per game -> 24-33. Half the exploring was bots with
                nowhere better to put a card. Real players build less map.
  Game length   barely moved: 32 -> 28 rounds at 3p, 38 -> 35 at 4p. Length
                is structural, not a bot artefact. This is the number to
                question against a 60-120 minute box claim.
  Attacks       18.9 -> 18.6 at 3p, 41.7 -> 37.1 at 4p. A bot that weighs the
                cost still attacks about as often, which is evidence that
                attacking is genuinely correct rather than accidental.
  Turtle        still 0%, but its score doubled (5.7 -> 11.7) because it now
                retires high cards. Still not close.
  Smart v greedy  76% / 24%. Choosing where to place beats choosing what to
                play, which is the right shape for a game about patterns.

GOLD FLOW  (findings-gold.txt)
------------------------------
NOT MODELLED, and both are gold sinks/sources:
  - FORTIFYING. Tiles carry the field and an attack takes the coin before the
    unit, but no bot ever pays to fortify. Gold spent on fortification: zero.
  - VICTORY-CARD EFFECTS. Effect C alone is 2-5 gold on demand, which is the
    single biggest income line in the game and is entirely absent. A and B are
    absent too.
So the income side is understated and one sink is missing altogether. Read the
numbers as a floor on income and a floor on spending.

WHAT THE FLOW SHOWS
  A third of every meld becomes gold rather than landing: 24% at two players,
  34% at three, 41% at four. Almost all of it (>97%) is the trick-loser's
  unused card, NOT cards that had nowhere legal to go - unplaceable cards are
  under 1%. The escape hatches in Rule 06 are almost never needed.
  Gold income scales with player count but spending does not keep up:
  unspent gold at game end is 4.3 / 16.8 / 44.2 at 2 / 3 / 4 players. At four
  players roughly a third of all gold earned is never spent on anything.

IS THE FEEDING RIGHT?  — a cliff in the starvation rule
--------------------------------------------------------
Timing and amounts are correct: upkeep is paid only when a hand recycles, after
that player's map phase and upgrades, off the CURRENT band only, non-cumulative
(0/1/2/3). The ten-card swap happens after payment. All verified.

The problem is what happens when you cannot pay. §08 says "take units back off
the map until you can" - and because your current band is the topmost band that
still holds units, dropping one step of upkeep means REFILLING THE WHOLE BAND
ABOVE YOU:

    Empire     -> Expansion    save 1 gold    return up to 2 units
    Expansion  -> Growth       save 1 gold    return up to 8 units
    Growth     -> Founding     save 1 gold    return up to 6 units

Measured over 14 three-player games: 21 starvation events, 81 units returned,
so ~3.9 units per event - but the distribution has a long tail. Three of the 21
events returned 8 or 9 units at once. Being one gold short can cost nine points
of population.

PROPOSED FIX (implemented, off by default)
  "If you cannot pay, return one unit from the map to your board for each gold
   you are short. The debt is then settled."
Proportional, bounded, one sentence, and it removes the cliff entirely.
Measured: units starved back 81 -> 33, game length unchanged (28 -> 29 rounds),
mean final population 15.0 -> 15.5.

Set Game.PROPORTIONAL_STARVATION = True to use it. Not written into the
rulebook yet - it is a design decision, not a bug fix.

PROPORTIONAL STARVATION + EFFECT C + FORTIFYING  (findings-economy.txt)
-----------------------------------------------------------------------
All three now on by default. Toggles: Game.PROPORTIONAL_STARVATION,
Game.USE_EFFECT_C, Game.USE_FORTIFY.

  Effect C     cash a victory card for gold by rank band (2/3/4/5). The card
               LEAVES THE GAME - conservation now tracks a `removed` pile so
               those cards are still accounted for. Bots spend the lowest rank
               first, and only when feeding would otherwise starve them.
  Fortifying   1 gold on a unit a rival can reach, own map phase only, at most
               one coin per unit. An attack takes the coin before the unit
               (§07); settling onto a fortified tile disturbs it and the coin
               is lost; a unit pulled off by starvation cannot leave its coin
               behind (take_unit_off trims it).

THE HEADLINE: THE GOLD SURPLUS IS GONE
  3 players   unspent at end  16.1 -> 5.0
  4 players   unspent at end  42.4 -> 7.1
Fortifying is what absorbs it - 18.6 gold a game at 3p, 37.4 at 4p, far more
than upgrades. The 4p economy is not soft after all; it only looked soft
because the sim was missing its largest sink.

STARVATION IS ESSENTIALLY GONE
  3 players   units returned  5.8 -> 0.4 per game
  4 players   units returned  8.8 -> 0.1 per game
Two changes contribute: the cliff is gone, and effect C gives a player a way
to buy their way out (used 3.4 times a game at 3p, worth 11.6 gold).

GAMES GOT SHORTER
  3 players  28 -> 25 rounds        4 players  36 -> 30 rounds
Fewer units bouncing back to the reserve means the end trigger arrives sooner.

SCORE SPLIT BARELY MOVED
  pop 47/48%, row 37/38%, dom 15/16% at 3p - so the balance between the three
  scoring routes is robust to all of this, which is reassuring.

CAVEAT: fortification absorbed only 2.1 attacks a game at 3p for 18.6 gold
spent. My bot fortifies whenever a rival is adjacent and it has 3+ gold, which
is almost certainly too eager. Read "fortifying soaks up the surplus" as
"there is a sink big enough to soak it up", not as a claim about correct play.

MELD LADDER USE  (findings-melds.txt)
-------------------------------------
The central mechanic, measured for the first time. Of every meld played:

              1 card   2 cards  3 cards  4 cards  5 cards
  2 players    26%       37%      24%      12%      1.2%
  3 players    36%       36%      18%       9%      0.6%
  4 players    42%       36%      17%       5%      0.1%

Players HOLD a limit of 4 about 30% of the time and a limit of 5 about 4-7% -
but melds of five are played 0.1-1.2% of the time. The straight of five and the
full house are, in practice, never played. Two pair and the ladder-shaped
placements (twoset) fall from 9% at two players to 3% at four.

Shapes: straights 44-53%, singles 26-42%, sets 10-11%, two-set melds 3-9%.

Reading it: the ladder's top two rungs are decoration. Reaching Empire is
mostly a way to end the game, not a way to play bigger melds. Whether that is
a problem depends on whether the ladder is meant to be a promise or a ceiling.
CAVEAT: my bots draft randomly and never shift units, so their hands are worse
at forming five-card melds than a drafting human's would be. This is a floor,
not a verdict.

SHOULD THE BANDS BE REDISTRIBUTED?  (findings-bands.txt)
--------------------------------------------------------
Tested 4/6/8/2 (current), 4/6/6/4, 3/5/6/6, 2/4/6/8 and 5/5/5/5 over 10
three-player games each.

  2/4/6/8 is the strongest: time at limit 5 goes 6% -> 24%, melds of five
  0.5% -> 3.0%, melds of four 9.1% -> 15.7%. It also shortens the game
  (25 -> 20 rounds) and raises upkeep paid (22.3 -> 26.5).

BUT the ceiling is not the bands. Measured at the moment of choosing a meld,
the band limit is the binding constraint only 35% of the time; the HAND binds
the other 65%. Nearly 40% of meld decisions are taken with three or fewer
cards left, because a hand is played down from ten to zero before it recycles.
No band layout can fix that.

So: redistribute if you want more time at the top rungs - 2/4/6/8 roughly
quadruples it - but expect melds of five to remain rare (3%, not 20%). If you
want the top of the ladder to be genuinely reachable, the lever is the hand:
its size, how it depletes, or letting a player hold back cards rather than
playing to empty.

FORTIFICATION POLICY  (findings-fortify.txt)
---------------------------------------------
The eager policy - fortify anything next to a rival whenever you hold 3 gold -
was spending 18.6 gold a game to absorb 2.1 attacks: 8.7 coins per hit.

Game.FORTIFY_POLICY now takes: off | eager | targeted | majority.
"targeted" is the new default. It spends only out of genuine surplus
(gold >= upkeep + 3) and only where the coin can actually pay:
  - a rival unit must be adjacent, AND able to afford that terrain's price;
  - a tile holding ONE unit scores higher, because losing it surrenders the
    tile outright while a stack merely gets shorter;
  - dear terrain scores lower - Forest and Mountain already defend themselves.
"majority" adds a bonus for the unit currently holding a terrain lead.

  policy     rounds  fortifs  absorbed  coins/hit  gold@fort  kills  unspent
  off           26      0.0       0.0         -        0.0     17.0    17.9
  eager         25     18.6       2.1       8.7       18.6     14.5     5.0
  targeted      28     11.9       2.8       4.3       11.9     15.6     8.6
  majority      28     11.6       2.9       4.0       11.6     15.1     8.2

Targeted spends 36% less and absorbs MORE attacks. Efficiency doubles.
"majority" is indistinguishable from "targeted" - the extra term is not
earning its complexity, so targeted is the default.

AND FORTIFYING IS WORTH DOING. Head to head, the fortifying seat wins 40% vs
25%/35%, and the result holds when the roles are swapped (38%/38% vs 25%).
Population carries it: 15.9 against 13.6 and 14.7. Note this contradicts the
back-of-envelope worry that a coin buys only one unit while an upgrade buys a
victory card - the coin also denies tempo and keeps a tile, which the score
picks up.

Gold flow moves accordingly: unspent at end 5.0 (eager) -> 8.6 (targeted), so
the surplus is partly back. Fortifying is no longer the sink that soaks up the
whole economy; upgrades (16.1) now outspend it (11.9).

EFFECTS A AND B  (findings-effects-ab.txt)
-------------------------------------------
Implemented per the rulebook's four bands, NOT the 1-10/11+ split:
  A  +1 card (bands 1-10) or +2 (11-20); wins ties in bands 6-10 and 16-20.
     Declared in the card phase as the meld is played, judged only against
     what is already on the table.
  B  1 extra settle (1-10) or 2 (11-20); own suit in bands 1-5 and 11-15,
     any suit in 6-10 and 16-20. Settles only - no explore, no attack.

              rounds  gold in  unspent  kills   row: kept / A / B / C
  C only         28     64.9      8.6    15.6     14.1 / 0.0 / 0.0 / 1.9
  A + B + C      18     48.8      5.6    12.6      7.1 / 5.6 / 5.8 / 2.9

THE ROW IS NOW GENUINELY CONTESTED. Two-thirds of victory cards get spent
rather than scored, and A and B are used almost equally (5.6 vs 5.8). The
rulebook's "score, war chest, trick insurance" tension is real and roughly
balanced - it simply could not be observed before.

GAMES GOT 36% SHORTER, 28 -> 18 rounds. Effect B places extra units straight
onto the map and the end trigger is "someone places their last unit", so B
pulls the finish forward hard. Combined with the 2/4/6/8 band test (which also
shortened games) there is now real room to lengthen the game elsewhere.

Score shifts: population 48->51%, victory row 37->29%, dominance 15->20%.
The row scores less precisely because it is being spent.

THE ONE THING TO WATCH: position. See findings-effects-ab.txt. A inverts the
turn-order advantage - the leader goes from 37.6% of tricks to 23.9%, the last
player from 31.5% to 45.3%. It does not compound, because the winner leads the
next round and the lead is the worst seat for A, so it oscillates. Final scores
stay within ~2 points. But it is a real structural asymmetry inside each trick,
and it is worth deciding whether "players after you can still answer it" was
meant to be worth that much.

MAP OBJECTIVES  (objectives-review.md, findings-objectives.txt)
---------------------------------------------------------------
objectives.py scores all twelve cards of the module against the final maps of
real simulated games. Five never score at all.

The cause is not the objectives. The SHAPES DO NOT EXIST on the map: a straight
line of four plains occurs 0.00 times per game, an ocean tile with four ocean
neighbours 0.00 times. Measured over 30 final maps, a tile's neighbours share
its terrain 22.9% of the time - chance with four terrains is 25.0% - and 61% of
same-terrain regions are a single tile.

The explore rule places a tile matching the played card's suit, and cards arrive
in mixed suits, so terrain interleaves at random. The map is salt-and-pepper: no
ranges, no forests, no seas. Every objective asking for SAMENESS is asking for
something the map cannot produce; the two best performers (Trade Delta 49%,
Coastal Control 44%) both ask for VARIETY.

See objectives-review.md for the two ways out and why this is really a question
about the map rather than about the objective deck.

SAMPLE SIZE - READ BEFORE TRUSTING ANY OBJECTIVE RATE
------------------------------------------------------
Objective achievement rates measured on 20-30 samples carry a 95% interval of
roughly +/- 20 percentage points. Coastal Chain read 43% in one run and 17% in
the next, on the same engine. Every per-objective number quoted before
findings-objective-difficulty.md was measured at that size and should not be
used to set point values.

seek3.py runs two objectives per batch so each gets 60-120 samples and prints a
95% interval. Use it, not seek2.py, for anything that informs a decision.
