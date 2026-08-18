# -*- coding: utf-8 -*-
"""Blink — Variants & Shelved Rules.

Everything that is NOT in the base game but is worth keeping: rules retired
from earlier versions, and ideas simulated but not adopted. One document so
nothing has to live only in a chat log or a findings file.

Reuses the rulebook CSS, like the other booklets, so it is part of the set.
"""
import pathlib
from version import VTAG
from build_html import CSS

EXTRA = """
@page{size:A4;margin:16mm 16mm 16mm 16mm}
body{font-size:9.1pt;line-height:1.36}
.sheet{max-width:none;box-shadow:none;background:#fff}
.pad{padding:0}
.mast{padding:0 0 .8rem}
.badge{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:.62rem;
  letter-spacing:.12em;text-transform:uppercase;padding:.12rem .5rem;
  border-radius:.7rem;vertical-align:.18em;margin-left:.5rem;font-weight:500}
.b-retired{background:#EDE9F2;color:#4A3D78;border:.7px solid #A99FC9}
.b-sim{background:#E6EFDD;color:#3D6B1F;border:.7px solid #9DBB7E}
.b-untested{background:#F7E8D4;color:#8A5A1A;border:.7px solid #D9B384}
.rulebox{background:#F6F3EC;border:1px solid #D8D1C2;border-left:3px solid #37704A;
  border-radius:3px;padding:.5rem .8rem;margin:.5rem 0;break-inside:avoid}
.rulebox.prop{border-left-color:#C98A2E;background:#FAF5EC}
.rulebox p:first-child{margin-top:0}
.rulebox p:last-child{margin-bottom:0}
.rulebox ul{margin:.3rem 0 .3rem;padding-left:1.1rem}
.why{border-left:3px solid #B8952E;background:#FBF6EA;border:1px solid #E0D5B8;
  border-left:3px solid #B8952E;border-radius:3px;padding:.55rem .85rem;
  margin:.6rem 0;font-size:9pt;break-inside:avoid}
.why .tag{font-family:"IBM Plex Mono",monospace;font-size:.62rem;letter-spacing:.13em;
  text-transform:uppercase;color:#94742A;display:block;margin-bottom:.2rem}
.ex{background:#EEF3F6;border:1px solid #C6D4DC;border-left:3px solid #4A7D99;
  border-radius:3px;padding:.5rem .85rem;margin:.6rem 0;font-size:9pt;
  break-inside:avoid}
.ex .tag{font-family:"IBM Plex Mono",monospace;font-size:.62rem;letter-spacing:.13em;
  text-transform:uppercase;color:#4A7D99;display:block;margin-bottom:.2rem}
.intro{background:#F6F3EC;border:1px solid #D8D1C2;border-radius:3px;
  padding:.6rem .9rem;margin-bottom:.4rem;font-size:9.3pt}
table{font-size:8.5pt;margin:.4rem 0 .55rem}
section{padding:.7rem 0 .15rem}
h3{margin:.75rem 0 .25rem}
.lede{font-size:1rem;margin-bottom:.5rem}
footer{padding:.8rem 0 0;break-before:avoid}
"""


def sec(num, title, badge, cls, body):
    return f"""
<section>
  <div class="h2"><span class="num">{num}</span><h2>{title}<span class="badge {cls}">{badge}</span></h2></div>
  {body}
</section>"""


HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Blink — Variants &amp; Shelved Rules</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400..600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}{EXTRA}</style>
</head>
<body>
<div class="sheet"><div class="pad">

<header class="mast">
  <p class="eyebrow">Companion to the base rules {VTAG}</p>
  <h1 style="font-size:2.6rem;line-height:1">Variants &amp; shelved rules</h1>
  <p class="sub" style="font-size:1.05rem">Everything not in the base game, kept in one place</p>
</header>
<div class="steprule"><i></i><i></i><i></i><i></i></div>

<main>

<section style="border-top:none;padding-top:.9rem">
  <div class="intro">
    <p><b>None of these are part of Blink.</b> Some were in earlier versions and were
    retired; some were designed and simulated but never adopted. They are written out
    properly so that a decision can be revisited later without reconstructing it from
    memory.</p>
    <p style="margin-bottom:0">Badges say how much is known:
    <span class="badge b-retired">Retired</span> was once a base rule ·
    <span class="badge b-sim">Simulated</span> measured, never played ·
    <span class="badge b-untested">Untested</span> written only.
    Add one at a time, and only after the base game is familiar. The
    <b>Wasteland &amp; Disaster</b> and <b>Trade</b> modules are larger and live in their
    own documents.</p>
  </div>
</section>

{sec("01", "Pattern placement", "Retired in v0.21", "b-retired", '''
  <p class="lede">The spatial heart of Blink up to v0.20: a meld did not just decide
  <em>how many</em> cards you spent, it decided <em>what shape</em> your civilization
  took. This is the single biggest rule the game has ever dropped, and the one most
  worth being able to put back.</p>

  <div class="rulebox">
    <p><b>Instead of spending each card independently (§06), a meld lands as a
    pattern</b> — one cell per card, resolved as a single piece. Three rules govern it:</p>
    <ul>
      <li><b>Connected.</b> The cells of a piece touch each other, and at least one sits
      on — or next to — a tile you already occupy. A straight or a single set is one
      piece. A <b>two-set meld</b> (two pair, full house) lands as <b>two clusters</b>,
      each touching your civilization on its own; they need not touch each other, and you
      choose where each goes.</li>
      <li><b>In rank order.</b> A straight is walked from its lowest rank to its highest.
      The order is fixed; the direction of each step is not — a straight of three is any
      three connected cells you can walk in rank order. A line, a chevron, a bend, a curl
      around a mountain.</li>
      <li><b>Suit matches terrain.</b> Each card acts on a cell whose terrain matches its
      suit.</li>
    </ul>
    <p>Each cell then does one of the four things a card can do — settle, explore, attack,
    or take gold. A cell whose terrain does not match its card simply <b>takes gold</b>
    and stays empty; the rest of the pattern still lands.</p>
    <p><b>Legality is judged once</b>, when you begin placing the meld. A tile you lay
    with one card does not open a space for a later card of the same meld — you work from
    the map as you found it.</p>
    <p><b>Shift.</b> A settle may take a unit already on the map, from any tile connected
    to your population, instead of one from the reserve. Free, but it grows nothing.</p>
    <p><b>Swept off the map.</b> With no units on the map at the start of your map phase,
    the pattern is exempt from the connection rule: place it on any unoccupied tiles
    matching its suits, anywhere.</p>
  </div>

  <div class="ex">
    <span class="tag">What it buys, in one line</span>
    A straight of four must walk four connected, terrain-matching cells in rank order.
    That constraint is the whole spatial game — the map stops being a list of legal
    squares and becomes a route you have to find.
  </div>

  <div class="why">
    <span class="tag">Why it was retired, and the case for putting it back</span>
    <p>It was cut for <b>simplification</b>: the pattern rules were the largest single
    block in the rulebook, and the tight gold economy meant strong play cashed cards
    constantly — which broke patterns up anyway. It was also hard to justify thematically:
    a civilization does not expand in poker shapes.</p>
    <p>The cost is that <b>meld shape no longer reaches the table</b>. Under v0.21 a
    straight of four and a quadruple do exactly the same work — four things done — so the
    five tiers of meld diagrams describe a distinction with no consequence. If v0.21
    playtests as flat, this is the first thing to try restoring, possibly only at the
    larger melds.</p>
    <p>Note that this variant also restores <b>shift</b>, which the base game replaced
    with free moves. Running both is untested and probably too much movement.</p>
  </div>'''
)}

{sec("02", "Population limits that grow with your board", "Simulated", "b-sim", '''
  <p class="lede">In the base game a terrain holds the same number all game — Plains 3,
  Forest 2, Ocean 1, Mountain 1. This variant makes the limits climb with your band, so
  the player board teaches you what your civilization can now support.</p>

  <div class="rulebox">
    <p><b>Population limits are printed per band, and the limit that applies to a tile is
    its owner&rsquo;s.</b> Two players may legally stack the same terrain differently.</p>
    <table>
      <thead><tr><th>Band</th><th>Plains</th><th>Forest</th><th>Ocean</th><th>Mountain</th></tr></thead>
      <tbody>
        <tr><td>Founding</td><td class="num-cell">2</td><td class="num-cell">1</td><td class="num-cell">1</td><td class="num-cell">1</td></tr>
        <tr><td>Growth</td><td class="num-cell">2</td><td class="num-cell">2</td><td class="num-cell">1</td><td class="num-cell">1</td></tr>
        <tr><td>Expansion</td><td class="num-cell">3</td><td class="num-cell">2</td><td class="num-cell">1</td><td class="num-cell">1</td></tr>
        <tr><td>Empire</td><td class="num-cell">3</td><td class="num-cell">3</td><td class="num-cell">2</td><td class="num-cell">2</td></tr>
      </tbody>
    </table>
    <p>Mountain and Ocean stay low throughout: hostile ground never becomes comfortable.</p>
    <p><b>If starvation drops your band, your cities shed the difference.</b> After you
    return units for missing food, every tile of yours holding more than your
    <em>new</em> limit sends the surplus back to the reserve. Famine hits the crowded
    places first.</p>
    <p class="fine">Those returned units refill your reserve, which can drop your band
    again — repeat until no stack is over its limit. Only <b>starvation</b> culls: units
    lost in combat lower your band without emptying your cities, so a stack can sit above
    your current limit until the next famine.</p>
  </div>

  <div class="rulebox prop">
    <p><b>Wider variant — flat start, wide Empire</b> <span class="badge b-sim">Simulated</span><br>
    Founding <b>1/1/1/1</b>, Growth 2/2/1/1, Expansion 3/2/1/1, Empire <b>4/3/2/2</b>.
    A stronger arc: every terrain holds exactly one at the start, and Empire opens
    everything. Measurably more runaway — see below.</p>
  </div>

  <div class="why">
    <span class="tag">Designer&rsquo;s notes — 40 games, 3 players, identical seeds</span>
    <table>
      <thead><tr><th></th><th>base (fixed)</th><th>wider</th><th>the table above</th></tr></thead>
      <tbody>
        <tr><td>units per occupied tile</td><td class="num-cell">1.23</td><td class="num-cell">1.37</td><td class="num-cell">1.30</td></tr>
        <tr><td>leader minus last place</td><td class="num-cell">15.8</td><td class="num-cell">19.5</td><td class="num-cell">17.1</td></tr>
        <tr><td>leader&rsquo;s units on map</td><td class="num-cell">10.9</td><td class="num-cell">12.9</td><td class="num-cell">11.9</td></tr>
        <tr><td>last place&rsquo;s units</td><td class="num-cell">5.6</td><td class="num-cell">5.6</td><td class="num-cell">5.8</td></tr>
        <tr><td>rounds · mean score · kills</td><td class="num-cell" colspan="3">unchanged within noise</td></tr>
      </tbody>
    </table>
    <p><b>The whole benefit goes to whoever is already ahead.</b> The leader gains up to
    two units; last place gains none — reaching Empire is what unlocks the wide limits, so
    the player who got there first is the only one who banks them. The final gap widens
    23% under the wider ladder, 8% under the gentler one.</p>
    <p><b>The flat start does more work than the wide end.</b> Climbing to Empire takes
    most of the game, so the generous limits exist only for the last few rounds. Stacking
    rises, but the map is still mostly one unit per tile.</p>
    <p>Small bonus: the twentieth-unit end trigger — which never fires in the base game
    under skilled play — fires in 4 games of 40 with either ladder, because stacking gives
    late units somewhere to go.</p>
    <p><b>The famine cull is a rule for a situation that does not arise.</b> Across 20
    games with the bot&rsquo;s safety valves deliberately switched off, starvation returned
    <b>0.1 units per game</b> and the cull never fired once, let alone cascaded. Food costs
    roughly 13 gold a game against 47 earned — a real tax, but never an unpayable one. The
    rule is correct and closes a genuine hole; it is also, at these numbers, dormant.</p>
    <p>Neither ladder is an improvement on the numbers alone. The case for them is
    <em>tactile</em>: a board that visibly grants you more room as you grow. That is
    exactly the kind of thing a simulation cannot score and a table can.</p>
  </div>'''
)}

{sec("03", "Dock the losers a card", "Retired in v0.21", "b-retired", '''
  <p class="lede">How the trick paid out until v0.21, and the reason it changed. Kept
  because the rule contains a subtlety that is easy to lose sight of.</p>

  <div class="rulebox">
    <p><b>The trick winner spends every card of their meld. Everyone else spends one card
    fewer than they played, and takes 1 gold for the card they had to leave out</b> —
    their choice which.</p>
    <p>Nobody gets an extra card, and the trick&rsquo;s last place is not singled out.</p>
  </div>

  <div class="why">
    <span class="tag">Why it was replaced</span>
    <p><b>It asks every player to remember a number.</b> "How many may I use this round?" is
    a question the current rule never poses.</p>
    <p><b>It throws a card away against its owner&rsquo;s wishes</b> every round, for every
    non-winner. Roughly a quarter more happens on the map once that stops.</p>
    <p><b>It produced the worst score floor of any structure measured</b>, at every player
    count: last place finished on 24.1 / 14.6 / 12.6 at two, three and four players, against
    27.8 / 19.0 / 15.1 under the rule that replaced it. Those differences sit outside their
    confidence intervals; the gap differences between structures do not.</p>
    <p><b>Its headline economy number was inflated.</b> It showed the highest share of cards
    turned to gold — 47–50% — but part of that was the compulsory docked card. Under the
    current rule every coin is chosen, and the genuine rate is about a third.</p>
    <p><b>The subtlety worth remembering:</b> the coin paid for the docked card was an
    unconditional subsidy to whoever lost most tricks — a rubber band disguised as a
    penalty. Any replacement has to put that band back somewhere, which is exactly what the
    coin to last place does.</p>
  </div>

  <div class="ex">
    <span class="tag">If you want to A/B it at the table</span>
    Play one game each way. The number to bring back is not who won — it is whether anyone
    had to ask how many cards they were allowed to use.
  </div>'''
)}

{sec("04", "Combination melds", "Simulated", "b-sim", '''
  <p>Four- and five-card melds are rare in practice: the material seldom lines up. This
  lets smaller melds join forces.</p>
  <div class="rulebox">
    <p><b>You may combine two or more multi-card melds</b> (sets and/or straights) into one
    <em>combination meld</em>:</p>
    <ul>
      <li>Every component must be a valid meld of <b>at least two cards</b>. Single cards
      may never be part of a combination.</li>
      <li>Each card belongs to exactly one component; the total must fit your meld limit.</li>
      <li>Trick score and tie-breaks work exactly as normal.</li>
    </ul>
    <p><em>With pattern placement (§01):</em> each component is placed separately, as its
    own piece. <em>In the base game:</em> a combination changes nothing about placement —
    it only lets you play more cards at once.</p>
  </div>
  <div class="ex">
    <span class="tag">Example</span>
    The pair <em>4 Plains + 4 Forest</em> with the straight <em>7-8-9 Forest</em> is a
    five-card meld scoring 32.
  </div>
  <div class="why">
    <span class="tag">Designer&rsquo;s notes — measured under v0.20 pattern rules</span>
    <p>Five-card melds went from 0.65 to 1.43 per game at three players (+119%) and 0.55 to
    1.68 at four (+205%); combinations settled at 12% of everything played. The game did
    <b>not</b> speed up — the end trigger is placing units, and combinations only batch
    placements. Straights were partly absorbed (45%→37% of melds) and singles rose
    slightly, so the distribution polarised.</p>
    <p><b>These numbers predate v0.21</b> and were measured with patterns on the map. Under
    the base game the placement objection disappears entirely, which makes this variant
    both safer and less interesting — it becomes purely "play more cards at once".</p>
  </div>
  <div class="rulebox prop">
    <p><b>Sub-variant — connected combinations</b> <span class="badge b-untested">Untested</span><br>
    Only meaningful alongside pattern placement (§01): all components must together form
    one connected group on the map, restoring the placement discipline a 2+2 split would
    otherwise sidestep.</p>
  </div>'''
)}

{sec("05", "Super melds", "Retired", "b-retired", '''
  <p>Part of Blink before v0.20, removed to streamline the meld vocabulary.</p>
  <div class="rulebox">
    <p><b>A super meld is any overlapping combination of melds</b> — one card may belong to
    several components at once. Each component must be valid on its own, and both the meld
    limit and the trick score count each <b>physical card once</b>.</p>
  </div>
  <div class="ex">
    <span class="tag">Example</span>
    <em>9 Plains, 9 Forest, 10 Forest</em>: the 9 of Forest belongs to both the set 9+9 and
    the straight 9-10. Three cards, meld score 28.
  </div>
  <div class="why">
    <span class="tag">Designer&rsquo;s notes</span>
    <p>Removed on publisher feedback: spotting and verifying overlaps slows the trick for
    little gain, since each card still counts once. Not recommended together with
    combination melds — they cover the same ground, and combinations are simpler.</p>
  </div>'''
)}

{sec("06", "Friends of 10s", "Retired", "b-retired", '''
  <p>An extra two-card meld from earlier versions, cut for simplicity.</p>
  <div class="rulebox">
    <p><b>Two cards of any suits whose ranks sum to exactly 10, 20 or 30</b> form a valid
    meld — 1+9, 2+8, 3+7, 4+6, 11+9, 12+8, 11+19, and so on.</p>
  </div>
  <div class="why">
    <span class="tag">Designer&rsquo;s notes</span>
    <p>Gives low ranks a late-game purpose and creates cross-suit pairs that sets and
    straights cannot. Cut because it adds an arithmetic check to every hand evaluation.
    Effect on balance never measured.</p>
  </div>'''
)}

{sec("07", "Awakenings — one terrain power per terrain, per game", "Proposal · untested", "b-untested", '''
  <p class="lede">Four moments in a game where the ground you hold does something for you.
  Each terrain grants one power, once per game, and its strength is whatever you have
  standing on that terrain at the moment you use it. Mountains raise an army, forests
  think, plains breed, and the sea finds new land.</p>

  <div class="rulebox">
    <p><b>Once per game, for each terrain, on your map turn, as a free action.</b> No card,
    no move, no gold. You must hold at least one unit on that terrain. Announce it, work
    out its strength <b>S</b>, resolve it. That terrain is then spent for the rest of the
    game — four awakenings in total, and no more.</p>

    <p><b>Strength is counted in tiles&rsquo; worth of people, not in bodies.</b> Divide
    your units on that terrain by the number below and round down, minimum 1.</p>
    <table>
      <thead><tr><th></th><th>Plains</th><th>Forest</th><th>Mountain</th><th>Ocean</th></tr></thead>
      <tbody>
        <tr><td>population limit</td><td class="num-cell">3</td><td class="num-cell">2</td><td class="num-cell">1</td><td class="num-cell">1</td></tr>
        <tr><td><b>units per point of S</b></td><td class="num-cell"><b>3</b></td><td class="num-cell"><b>2</b></td><td class="num-cell"><b>2</b></td><td class="num-cell"><b>1</b></td></tr>
      </tbody>
    </table>
    <p class="fine">Three of the four are simply the terrain&rsquo;s own population limit:
    one point per full tile&rsquo;s worth. Mountain is the exception — two tiles to the
    point — because mountains are held in numbers rather than in depth. See the notes.</p>

    <p><b>Mountain — Muster.</b> Remove <b>S</b> rival units from tiles touching your
    Mountains. Settle each tile you empty, if you have a unit in reserve.</p>
    <p><b>Forest — Study.</b> Make <b>S</b> researches this turn, paying no gold and
    retiring nothing, with your rank cap raised by <b>S</b> for those purchases.</p>
    <p><b>Plains — Harvest.</b> Place <b>S</b> units from your reserve onto tiles you
    already occupy that have room.</p>
    <p><b>Ocean — Expedition.</b> Lay <b>S</b> new tiles of any terrain, each touching
    water you occupy, and put one unit on one of them. Touch-two still applies: Blink has
    no bridges, and a voyage does not get to build one.</p>
  </div>

  <div class="rulebox prop">
    <p><b>Tighter variant — one awakening a game.</b> Instead of one per terrain, each
    player gets a single awakening for the whole game and chooses which terrain it comes
    from. Four one-shots per player over thirteen rounds is a lot of swing at a
    four-player table; one is a decision you remember.</p>
  </div>

  <div class="why">
    <span class="tag">Designer&rsquo;s notes — where the numbers come from</span>
    <p>The powers themselves are <b>untested</b>. What has been measured is the thing the
    scale rests on: how much of each terrain a player actually holds. Sixty three-player
    games, base rules, peak holdings over the whole game.</p>
    <table>
      <thead><tr><th></th><th>Plains</th><th>Forest</th><th>Mountain</th><th>Ocean</th></tr></thead>
      <tbody>
        <tr><td>units held (peak)</td><td class="num-cell">6.3</td><td class="num-cell">5.0</td><td class="num-cell">4.4</td><td class="num-cell">2.2</td></tr>
        <tr><td>tiles held</td><td class="num-cell">2.4</td><td class="num-cell">2.6</td><td class="num-cell">4.3</td><td class="num-cell">1.7</td></tr>
        <tr><td>units per occupied tile</td><td class="num-cell">2.6</td><td class="num-cell">1.9</td><td class="num-cell">1.0</td><td class="num-cell">1.0</td></tr>
        <tr><td><b>resulting S</b></td><td class="num-cell"><b>2.1</b></td><td class="num-cell"><b>2.5</b></td><td class="num-cell"><b>2.2</b></td><td class="num-cell"><b>2.2</b></td></tr>
      </tbody>
    </table>
    <p><b>Counting bodies would have been wrong.</b> Plains hold three to a tile and are
    filled nearly to the brim; Ocean holds one and is barely used. A flat per-unit scale
    makes the Plains power three times the Ocean one. Dividing by the population limit
    lines three of the four up almost exactly — 2.1, 2.5, 2.2 — which is the whole reason
    the limits belong in the scale.</p>
    <p><b>Mountain is the one that does not fall out of the arithmetic.</b> Its limit is 1,
    so dividing by it leaves S at 4.4 — twice everything else. Not because mountains are
    generous but because players hold <em>many</em> mountain tiles: 4.3 of them, against
    2.4 plains, while having fewer units on them. Two tiles to the point brings it back to
    2.2. It is a calibration, not a derivation, and it is printed rather than hidden.</p>
    <p><b>This gives Plains a reason to exist that the base game does not.</b> Because a
    plains tile holds three, you need very few of them — 2.4 on average — and dominance is
    scored on your biggest connected <em>stretch</em>, counted in tiles. So plains are
    doubly discouraged as a presence on the map: efficient to stack, worthless to spread.
    Harvest is the one thing in Blink that pays for depth rather than breadth.</p>
    <p><b>Twenty units across four terrains is the balance.</b> Nobody gets four powers at
    full strength. Concentrating gives you one large awakening and a dominance score;
    spreading gives you four modest ones. That the choice is forced by the unit supply,
    rather than by a rule, is the part worth keeping.</p>
    <p><b>What to watch for.</b> It double-dips: dominance already pays for massing on a
    terrain, and these pay again on the same count, in a game where the leader already
    finishes 15 to 19 points clear. Expedition is the one to suspect — map size feeds
    everything downstream. And Study taking cards for nothing may distort the victory row,
    which is also points.</p>
    <p><b>Open questions.</b> Should an awakening spend the units — exhaust them, or return
    one to the reserve? That is the cleanest brake if the double-dip proves real. Should it
    be once per terrain or once per game? Is Expedition simply the best of the four,
    whatever the numbers say?</p>
  </div>'''
)}

</main>

<div class="pad"><footer>Blink · variants and shelved rules · companion to base rules {VTAG} ·
Toby Siko · deep-diversions.com/blink · wasteland and trade modules are published
separately</footer></div>

</div></div>
</body>
</html>
"""

out = pathlib.Path("./Blink-variants.html")
out.write_text(HTML, encoding="utf-8")
print("wrote", out, len(HTML), "bytes")
