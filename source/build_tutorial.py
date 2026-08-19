# -*- coding: utf-8 -*-
"""Blink — Your First Game. Standalone teaching booklet.
Reuses the current stylesheet and figure set so the two documents match."""
import pathlib
from build_html import CSS, F, fig
from version import VTAG

EXTRA = """
.step{border-left:3px solid var(--gold);padding:.1rem 0 .1rem 1rem;margin:1.5rem 0}
.step .n{font-family:"IBM Plex Mono",monospace;font-size:.68rem;letter-spacing:.14em;
  text-transform:uppercase;color:var(--stone);display:block;margin-bottom:.2rem}
.step h3{margin:.1rem 0 .4rem}
.say{background:#F1EDE4;border-radius:3px;padding:.9rem 1.1rem;margin:1rem 0;
  font-style:italic;color:var(--ink)}
.say b{font-style:normal}
.wrong dt{font-weight:600;margin:.9rem 0 0}
.wrong dd{margin:.15rem 0 0;color:var(--stone)}
.seat{font-family:"IBM Plex Mono",monospace;font-size:.72rem;letter-spacing:.1em;
  text-transform:uppercase;color:var(--stone)}
"""

HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Blink — Your First Game</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400..600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}{EXTRA}</style>
</head>
<body>
<div class="sheet">

<header class="mast pad">
  <p class="eyebrow">Blink · a meld-building civilization game</p>
  <h1>Your First Game</h1>
  <p class="sub">A guided walkthrough — read this at the table, out loud</p>
  <p class="meta"><span>3 players</span><span>about 20 minutes to learn</span><span>Toby Siko</span></p>
</header>
<div class="steprule"><i></i><i></i><i></i><i></i></div>

<main class="pad">

<section>
  <div class="h2"><span class="num">—</span><h2>How to use this booklet</h2></div>
  <p class="lede">Don't read the rulebook first. Sit down with the box, put this booklet in the
  middle of the table, and work through it aloud. It sets the game up with you and then plays
  the first three rounds alongside you, introducing each rule at the moment you need it.</p>
  <p>The walkthrough is written for <strong>three players</strong> — we'll call them
  <b>Ada</b>, <b>Bex</b> and <b>Cy</b>; substitute your own names. At two or four players
  everything works the same way; the setup table in the rulebook covers the differences.</p>
  <p>Two things to leave in the box for now: the <b>map objectives</b> and <b>personal
  objectives</b> modules. They're good, and they're for your third game.</p>
  <p>Once you've played, the rulebook is the reference — every section number in these pages
  points into it.</p>
</section>

<section>
  <div class="h2"><span class="num">1</span><h2>Set the table up together</h2></div>

  <div class="step">
    <span class="n">Step 1 · the cards</span>
    <h3>Split the deck by rank, not by suit</h3>
    <p>Find every card of ranks <b>3 to 10</b> — that's your <b>starting deck</b>. Ranks
    <b>11 to 20</b> are the <b>advanced deck</b> — the full range, whatever the player count.
    Put ranks 1 and 2 back in the box; they belong to the four-player starting deck.</p>
    <p>Ranks 3–10 give 32 cards and you only need 30. Shuffle the four rank-3 cards, keep two
    at random, and box the others. That keeps the starting deck at 30 cards.</p>
  </div>

  <div class="step">
    <span class="n">Step 2 · your hand</span>
    <h3>Draft ten cards you'll keep all game</h3>
    <p>Deal ten starting-deck cards to each player. Now draft: <b>keep 4, pass the rest
    clockwise</b>. From the six you receive, <b>keep 6, pass 4</b>. Then <b>keep 8, pass 2</b>.
    Then keep the last two. You end with ten cards.</p>
    <div class="say"><b>Say this out loud:</b> these ten cards are your civilization for the
    whole game. You will play them, pick them back up, and play them again. You'll only change
    them by buying better ones later — one at a time, and never more than ten.</div>
    <p>Drafting well is a skill for game two. For now, a rough guide: pairs and consecutive
    ranks are worth more than high cards on their own, because they let you play more cards at
    once.</p>
  </div>

  <div class="step">
    <span class="n">Step 3 · your board</span>
    <h3>Load all twenty units, top tier first</h3>
    <p>Take a player board and fill all five tiers — <b>2, 3, 5, 5, 5</b> from the top. Every unit
    you'll ever place is here. Put the <b>ascension coins</b> on their printed spots: 1, 2, 3, 4.</p>
    {fig('board', 'Your reserve empties from the top band down. The tier you are currently drawing from prints four numbers: the meld you may play, your free moves, the gold your people cost to feed, and the highest rank you may buy. Right now that is Tribe — melds of two, one free move, food free, cap 11.')}
    <div class="say"><b>Say this out loud:</b> this board is the engine. Emptying a tier makes you stronger and
    more expensive at the same moment — and pays you a one-off ascension coin for doing it.</div>
  </div>

  <div class="step">
    <span class="n">Step 4 · the map</span>
    <h3>Three Mountains, three Plains</h3>
    <p>Take three <b>Mountain</b> tiles and put them in a triangle in the middle of the table.
    Now put one <b>Plains</b> against each outer face of the triangle, spaced as in the picture,
    so that <b>every Plains is three tiles from every other</b>. Each player takes one unit from
    their top band and puts it on a Plains — that's their homeland.</p>
    <div class="say"><b>Why three apart:</b> cards only act next to your civilization. Three apart
    means nobody can be attacked in the opening rounds, whatever they draw.</div>
    {fig('setup_maps', 'The starting layouts. One Mountain per player in the middle, one Plains per player around it — and every start three tiles from every other, which is what keeps you out of reach in the opening rounds.')}
  </div>

  <div class="step">
    <span class="n">Step 5 · the supply and the market</span>
    <h3>Tiles in the open, nine cards face up</h3>
    <p>Sort the remaining tiles into four open piles by terrain, in easy reach of everyone.
    This is the <b>tile supply</b> — nothing is hidden and nothing is rationed. When you need a
    Forest, you take a Forest, until the Forests run out.</p>
    <p>Now shuffle the whole advanced deck together, face down. Deal <b>nine cards face up in a
    3&times;3 grid</b> beside it. That is the market — a spread of ranks, not one per suit.
    Leave a gap beside it for the <b>shared pile</b>, which starts empty.</p>
    {fig('market', 'One shuffled deck, nine positions. Every research turns a card onto the position showing the highest rank — burying it. Nobody chooses where it lands, so the top of the market keeps sinking out of reach. Your tier&rsquo;s rank cap decides how much of the spread you can actually take; the rest is visible and out of bounds.')}
  </div>

  <div class="step">
    <span class="n">Step 6 · who goes first</span>
    <h3>Hand out the dice</h3>
    <p>Pick a start player — Ada, say. She takes initiative die <b>“1”</b>. The others take 2
    and 3. You're ready.</p>
  </div>
</section>

<section>
  <div class="h2"><span class="num">2</span><h2>Round one — play it with us</h2></div>
  <p>Everyone still has a unit sitting in Tribe — setup spent one of the two — so everybody's
  meld limit is <strong>2</strong>. You may play one card or two, never more. Note how short that
  is: the first unit any of you settles clears Tribe and lifts that player to melds of
  three.</p>

  <h3>The card phase</h3>
  <p>Ada leads, then Bex, then Cy. Nobody may pass, and — unlike most trick-taking games —
  <strong>nobody has to follow suit</strong>. Play whatever combination you like.</p>
  <p>What counts as a legal meld? Just one rule: the ranks must form an <b>unbroken run</b>.
  Duplicates are free, suits are irrelevant. At limit 2 that means a single card, two of the
  same rank, or two consecutive ranks.</p>
  <ul>
    <li><span class="seat">Ada</span> plays <b>5 of Plains + 6 of Plains</b> — the run 5-6.</li>
    <li><span class="seat">Bex</span> plays <b>8 of Mountain + 8 of Ocean</b> — the run 8, doubled.</li>
    <li><span class="seat">Cy</span> plays a single <b>4 of Mountain</b>.</li>
  </ul>
  <p>Now resolve it. <strong>Highest total wins</strong> — add the ranks up. Bex played
  8 + 8 = <b>16</b>, Ada 5 + 6 = <b>11</b>, Cy a single 4 = <b>4</b>. <b>Bex wins the
  trick.</b> She takes die 1, Ada die 2, Cy die 3.</p>
  <p>Ada matched Bex's two cards and lost, so one of the two cards <b>she already played</b>
  is <b>set aside</b>: she chooses which, it pays her <b>1 gold</b> instead of acting on the
  map, and it goes face down to the shared pile. Cy played fewer than the winner, so he gives
  up nothing. <span class="fine">That rule counts CARDS, not the total — Ada played two and
  so did Bex.</span></p>
  <div class="say"><b>Notice:</b> Cy could have won this trick with a single card, if it had
  been a 17 or better. One big card is a real play. But it would have been one card to spend
  on the map afterwards, against Bex's two — which is the choice the whole game turns on.</div>

  <h3>The map phase</h3>
  <p>Here's the move that makes Blink what it is: <strong>you now spend those same
  cards</strong>, one by one, as your actions on the map. Each card does one of four things:
  <b>settle</b> a unit, <b>explore</b> a tile, <b>attack</b> a rival, or <b>take 1 gold</b> —
  always on terrain matching its suit, always next to your civilization.</p>
  <p><b>The winner spends every card they played</b>, and so does anyone who played
  <em>fewer</em> than the winner. Only a player who <b>matched</b> the winner and lost gives
  one up — set aside for a gold, as Ada just did. The player whose meld <b>ranked last takes
  1 gold</b>. Act in initiative order.</p>

  <p><span class="seat">Bex — 2 cards, and she won</span><br>
  Only Plains and Mountain are on the table yet, so her <b>Mountain</b> card is the one that
  can settle: the Mountain beside her homeland is in reach, and she takes a unit from her top
  band. Mountain holds one, so that tile is hers alone now. She spends her <b>Ocean</b> card
  on an <b>explore</b>: she picks an empty space beside her civilization, checks that it
  touches at least two tiles already on the table, takes an Ocean tile from the supply, and
  puts it down empty for now. Both her cards reached the map — that is what winning the trick
  is worth, along with going first.</p>

  <p><span class="seat">Ada — 2 cards, one of them set aside</span><br>
  She keeps the <b>6 of Plains</b> and sets the 5 aside. The only Plains she can reach is her
  own homeland, so she settles the 6 by <b>stacking</b> a second unit on it — Plains holds
  three. The 5 goes face down to the shared pile and pays her <b>1 gold</b>: that is the
  price of matching Bex's two cards and losing on rank.</p>
  <div class="say"><b>Notice:</b> at the start there is no Forest and no Ocean anywhere. The only
  way to use those cards is to <em>build</em> the ground first — that is what exploring is for,
  and it is why nobody's hand is dead on turn one.</div>

  <p><span class="seat">Cy — 1 card, and last place</span><br>
  His single ranked last this trick, so he takes <b>1 gold</b> for that. He cashes the 4 of
  Mountain for a second gold — nothing on the map is worth reaching for yet. He has built
  nothing and is not behind; he's saving.</p>

  <p>To finish: pass the lead to Bex. Put your
  played cards face up in front of you — that pile is your <b>personal discard</b>, and it will
  become your next hand.</p>
  <div class="say"><b>What just happened:</b> one meld did two jobs. Bex's slightly higher card
  bought her initiative <em>and</em> a third card to spend. Cy's caution came last and paid
  him for it. That trade — tempo now against resources later — is the whole game.</div>
</section>

<section>
  <div class="h2"><span class="num">3</span><h2>Round two — spend them your way</h2></div>
  <p>Bex leads. Before you play, here is the rule that new players most often miss.</p>
  <p>A meld is a <strong>combination of cards</strong>, nothing more. Once the trick is
  settled, the meld has done its job — each card is then spent <b>on its own</b>, in any
  order you like, and each one sees the map as the last one left it. Explore a tile with one
  card and settle it with the next. Send one card to a border and cash the other for a coin.
  The meld decides <em>how much</em> you do, never <em>what</em> you do.</p>
  <div class="say"><b>Say this out loud:</b> every card is the same question — is it a person,
  or is it gold? There is no wrong terrain to hold cards for: a card with no useful place on
  the map is a coin, and coins are never wasted.</div>
  <p>Play round two normally. Four things to watch for as they come up:</p>
  <ul>
    <li><b>A card with nowhere useful to go</b> — wrong terrain, or boxed in — simply
    <b>takes 1 gold</b> instead. You are never stuck.</li>
    <li><b>Landing on a rival's tile</b> is an <b>attack</b>, not a move. The card is spent
    removing <em>one</em> of their units; your own unit stays in your reserve. Taking a tile
    always takes more than one turn. (You won't manage it this round — the Mountain is in the
    way, which is why it's there.)</li>
    <li><b>Your free move.</b> Once per turn at Tribe — no card needed — you may move one
    unit: across your own connected units onto a free tile beside them, or across open Ocean.
    Never onto a rival.</li>
    <li><b>Your top tier empties fast.</b> Tribe holds only two units and setup already
    spent one, so the first unit you settle clears it — take the <b>1 ascension coin</b> from
    the Settlement row. Your meld limit goes to <b>3</b>, your
    free moves to <b>2</b> — and your food bill starts at <b>1 gold</b> per recycle. You pay
    whatever your current band shows and nothing more.</li>
  </ul>
</section>

<section>
  <div class="h2"><span class="num">4</span><h2>Round three — spend a coin</h2></div>
  <p>By now someone has two or three gold. Here's what it buys.</p>
  <p>The most important purchase is an <strong>upgrade</strong>, and it is a straight trade:
  <b>your worst card out, a better one in</b>. Retire the <b>lowest-ranked card in your
  hand</b> into your <b>victory row</b>, pay <b>1 gold</b>, and take any one of the nine
  face-up market cards <b>straight into your hand</b>. You still hold exactly ten cards; one
  of them is just much better — and you can play it next round.</p>
  <p>It has to come out of your <b>hand</b> — cards you have already played to the table this
  turn are spent, and cannot be retired. So a turn where you dump your whole hand is a turn
  you do not research.</p>
  <p>You never choose <em>which</em> card leaves: it is always your lowest. That is what makes
  research feel like progress rather than shopping — the old idea is what pays for the new
  one, and nothing reaches your victory row that was not once the worst card you owned.</p>
  <p>Early on that means giving up a 3 or a 4. Later, when your hand is all upgrades, your
  lowest card <em>is</em> a good one. Don't hold back waiting for that: a card in the row is
  a point whatever its rank, so researching whenever you can afford it beats saving up for a
  perfect one.</p>
  <p>The card you retired is not wasted — it sits in your victory row and <b>scores at the end
  of the game</b>: a point for being there, and, once you hold three, its rank may land in the
  centre slot and score again. Or you can spend it later for a one-shot effect, at the cost of never scoring
  it. One of those effects is declared at the very top of a round, before anybody plays a card,
  so it is a bet rather than an answer; the other two — extra units, and taking gold — are
  used when you can already see the board. That choice is the heart of the game's second half;
  ignore it for now and just keep them.</p>
  <p>Gold also pays for: attacking into Forest (1) or Mountain (2), fortifying a unit against
  one attack (1), and — from the moment you empty your first band — <b>feeding your people</b>.
  Put the coins on your band's food slots during your turn; when your hand recycles, that is
  what your people eat.</p>
  <div class="say"><b>A warning worth hearing early:</b> expanding fast is how you lose your
  first game. Every band you empty moves you onto a costlier row — free, then 1, then 2, then 3
  gold every time your hand recycles, and you pay only the row you are on. Losing tricks pays you
  a coin per unused card, so falling a little behind is how you stay fed.</div>
</section>

<section>
  <div class="h2"><span class="num">5</span><h2>Now play on</h2></div>
  <p>You know enough. Play to the end — the game finishes when someone places their last unit
  or a suit's advanced deck runs out, then you finish the round and play one more.</p>
  <p>At the end, count: <b>1 point per unit on the map</b>, plus the <b>centre card of your
  victory row</b> (once you have three or more), plus <b>3 points for each terrain where you
  have the most units</b>. Gold breaks ties.</p>
  <p>Then read the rulebook. It will take twenty minutes and it will make sense, because you've
  already seen every part of it move.</p>
</section>

<section class="example">
  <div class="h2"><span class="num">✦</span><h2>Six things first-timers get wrong</h2></div>
  <dl class="wrong">
    <dt>Treating gold as a fallback.</dt>
    <dd>Cashing good cards on purpose is how food, fortresses and research get paid for.
    The strongest players convert constantly. (§06)</dd>
    <dt>Trying to win every trick.</dt>
    <dd>Coming last pays you a gold, and you'll need it. Deliberately playing a single is a
    real strategy, not a failure. (§04)</dd>
    <dt>Expecting to capture a tile in one turn.</dt>
    <dd>One card removes one defender and places nothing. You empty a tile one round and settle
    it the next. (§06)</dd>
    <dt>Emptying bands as fast as possible.</dt>
    <dd>Bigger melds put you on a costlier row, and that gold has three other jobs. Growth is
    a decision, not a goal. (§09)</dd>
    <dt>Hoarding cards in the victory row and never spending one.</dt>
    <dd>They're also your emergency gold and your trick insurance. A row of five you never
    touched may mean you played too safely — though every card is worth a point on its own,
    so spending one always costs you something. (§10)</dd>
    <dt>Forgetting the discard is your next hand.</dt>
    <dd>What you play this round is what you'll hold next time round. Cards bought late arrive
    later than you think. (§09)</dd>
  </dl>
</section>

</main>

<div class="pad"><footer>Blink · Your First Game · companion to base game rules {VTAG} ·
Toby Siko · deep-diversions.com/blink · @tobysiko.bsky.social</footer></div>

</div>
</body>
</html>
"""

out = pathlib.Path("./Blink-first-game.html")
out.write_text(HTML, encoding="utf-8")
print("wrote", out, len(HTML), "bytes")
