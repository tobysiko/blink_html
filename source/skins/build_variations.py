# -*- coding: utf-8 -*-
"""Four card treatments, and a player board wearing the same language."""

import json
import pathlib

import board_concept
import build_skin_aid
import face
import variants
from marks import COLOUR

HERE = pathlib.Path(__file__).resolve().parent
SKIN = json.loads((HERE / "civ-ladder.json").read_text(encoding="utf-8"))

SHOW = [("ocean", 12), ("plains", 18), ("forest", 4), ("mountain", 8)]


def card(suit, rank, treatment):
    return face.card(suit, rank, SKIN, treatment)


def treatment_rows():
    out = ""
    for cls, name, note in variants.TREATMENTS:
        out += (f'<div class="tr">'
                f'<div class="trhead"><h3>{name}</h3><p>{note}</p></div>'
                f'<div class="scroll"><div class="row">'
                + "".join(card(s, r, cls) for s, r in SHOW)
                + '</div></div></div>')
    return out


CSS = """
:root{
  --ground:#DCDBD5; --raise:#E7E6E1; --ink:#191A18; --soft:#5F5E58;
  --faint:#8B8A83; --rule:#C4C3BC; --seam:#9B7A16;
  --shadow:0 1px 2px rgba(30,28,22,.10), 0 10px 26px rgba(30,28,22,.16);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#151714; --raise:#1E211D; --ink:#E9E8E2; --soft:#A8A69E;
    --faint:#7C7A73; --rule:#33362F; --seam:#C9A94E;
    --shadow:0 1px 2px rgba(0,0,0,.5), 0 14px 34px rgba(0,0,0,.55);
  }
}
:root[data-theme="dark"]{
  --ground:#151714; --raise:#1E211D; --ink:#E9E8E2; --soft:#A8A69E;
  --faint:#7C7A73; --rule:#33362F; --seam:#C9A94E;
  --shadow:0 1px 2px rgba(0,0,0,.5), 0 14px 34px rgba(0,0,0,.55);
}
*{box-sizing:border-box}
body{background:var(--ground); color:var(--ink);
  font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif;
  font-size:15px; line-height:1.55; margin:0;}
.wrap{max-width:1180px; margin:0 auto; padding:0 26px 90px;}

.mast{padding:56px 0 30px; border-bottom:1px solid var(--rule);
  display:flex; flex-direction:column; gap:9px;}
.eyebrow{font-family:"IBM Plex Mono",monospace; font-size:11px;
  letter-spacing:.18em; text-transform:uppercase; color:var(--faint); margin:0;}
h1{font-family:"Fraunces",Georgia,serif; font-weight:600;
  font-size:clamp(34px,5.4vw,54px); line-height:1.02; letter-spacing:-.012em;
  margin:0; text-wrap:balance;}
.sub{margin:0; max-width:62ch; color:var(--soft); font-size:17px;}

section{padding-top:52px;}
.h2{display:flex; align-items:baseline; gap:14px; margin-bottom:6px;}
.h2 .num{font-family:"IBM Plex Mono",monospace; font-size:12px;
  color:var(--faint); letter-spacing:.12em; padding-top:4px;}
h2{font-family:"Fraunces",Georgia,serif; font-weight:600; font-size:27px;
  margin:0; letter-spacing:-.006em;}
.lede{max-width:66ch; color:var(--soft); margin:0 0 26px;}
.lede strong{color:var(--ink); font-weight:600;}

.scroll{overflow-x:auto; padding-bottom:6px;}
.row{display:flex; gap:15px; min-width:1052px;}
.card{flex:none; border-radius:2.6mm; box-shadow:var(--shadow);}

.tr{padding:26px 0; border-top:1px solid var(--rule);}
.tr:first-child{border-top:none; padding-top:0;}
.trhead{display:flex; align-items:baseline; gap:18px; margin-bottom:14px;
  flex-wrap:wrap;}
.trhead h3{font-family:"Fraunces",Georgia,serif; font-size:20px;
  font-weight:600; margin:0; min-width:120px;}
.trhead p{margin:0; font-size:13.8px; line-height:1.5; color:var(--soft);
  max-width:74ch; flex:1;}

.aidwrap{overflow-x:auto; padding-bottom:6px;}
.aidwrap .aid{box-shadow:var(--shadow);}

/* ---- the board ---------------------------------------------------------- */
.boardwrap{overflow-x:auto; padding-bottom:6px;}
.board{width:297mm; height:210mm; display:block; flex:none;
  box-shadow:var(--shadow); border-radius:2px;}

.notes{display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
  gap:2px; background:var(--rule); border:1px solid var(--rule);}
.note{background:var(--raise); padding:20px 22px 22px;}
.note h3{font-family:"Fraunces",Georgia,serif; font-size:17px; font-weight:600;
  margin:0 0 4px; text-wrap:balance;}
.note .tag{font-family:"IBM Plex Mono",monospace; font-size:10.5px;
  letter-spacing:.16em; text-transform:uppercase; color:var(--faint);
  display:block; margin-bottom:9px;}
.note p{margin:0 0 10px; font-size:14px; color:var(--soft); line-height:1.5;}
.note p:last-child{margin-bottom:0;}
.note.pick{border-left:3px solid var(--seam);}

footer{margin-top:56px; padding-top:20px; border-top:1px solid var(--rule);
  font-family:"IBM Plex Mono",monospace; font-size:11.5px; color:var(--faint);
  display:flex; flex-wrap:wrap; gap:6px 22px;}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""

HTML = f"""<title>The Skin, Five Ways</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400..600&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{CSS}{face.CARD_CSS}{variants.CSS}{build_skin_aid.CSS}</style>

<div class="wrap">

<header class="mast">
  <p class="eyebrow">Blink &middot; civ-ladder &middot; variations</p>
  <h1>The Skin, Five Ways</h1>
  <p class="sub">The card skeleton does not move in any of these &mdash; same
  four corners, same two mirrored panels, same C&nbsp;/&nbsp;B&nbsp;/&nbsp;A.
  What changes is how much ink the panels carry, which is the one dial that
  actually decides how a card reads across a table and what a sheet costs to
  print. Then a player board wearing the same language.</p>
</header>

<section>
  <div class="h2"><span class="num">01</span><h2>Five treatments</h2></div>
  <p class="lede">Four suits, four ranks, so each row shows every colour and a
  different effect band. Shown at print size.</p>
  {treatment_rows()}
</section>

<section>
  <div class="h2"><span class="num">02</span><h2>A board that climbs</h2></div>
  <p class="lede">The printed board is a table: five rows, five columns, tiers
  as rows. Nothing about reading it feels like climbing. This draws the tier
  track as what it actually is &mdash; <strong>a staircase you ascend by
  emptying your reserve</strong>, so your tier is a silhouette rather than a
  number to look up &mdash; and runs the <strong>Lean</strong> configuration:
  food and ascension gone, which takes two columns off the sheet and a recurring
  step out of the phase. The bands run from parchment at Tribe to a cold horizon
  at Civilization, the card back&rsquo;s past-to-future axis laid flat. Above
  each tread, the two <em>ranks</em>: what you may buy, and
  <strong>what your wall holds</strong>. On each step, the two <em>counts</em>:
  melds and free moves, on a shelf shared by all five so you read across.
  A4 landscape, at print size.</p>
  <div class="boardwrap">{board_concept.SVG}</div>
</section>

<section>
  <div class="h2"><span class="num">03</span><h2>The aid, which now owes the deck a debt</h2></div>
  <p class="lede">The cards no longer print A, B and C as letters &mdash; they print
  three marks, in the order <strong>C, B, A downward</strong>, so a card turned
  around in the victory row shows A first. That was right for the card and it
  puts a debt on the aid: <strong>this is now the only place the three marks are
  named.</strong> So the marks legend is the back&rsquo;s headline rather than a
  footnote, and every mark on it is imported from <code>marks.py</code> rather
  than redrawn &mdash; the aid and the deck are the same code and cannot drift.
  A fold-over, 88&nbsp;&times;&nbsp;63&nbsp;mm finished, four to an A4 page. Shown
  at print size, unfolded.</p>
  <div class="aidwrap">{build_skin_aid.AID}</div>
</section>

<section>
  <div class="h2"><span class="num">04</span><h2>What I would pick, and why</h2></div>
  <div class="notes">
    <div class="note pick">
      <span class="tag">The pick</span>
      <h3>Plate for the prototype, Deep weave for the pitch</h3>
      <p>Plate is right while sixty-four illustrations are still missing: it is
      the quietest ground, so a dashed placeholder does not look like a hole in
      a decorated card. It is also the cheapest to reprint every time a name
      changes.</p>
      <p><strong>Deep weave is the one to finish.</strong> Combining the two
      fixed both of their faults rather than adding them: a lattice that had to
      be held back on white can go to full strength on a tint because it is
      <em>lighter</em> than its ground, and the tint that was killing the line
      art stops doing so once the stroke is darkened for it. It also does
      something neither did alone &mdash; the white name band and the white
      corner zones become the only unfilled parts of the card, which makes the
      mirror axis visible instead of merely true.</p>
    </div>
    <div class="note">
      <span class="tag">Found</span>
      <h3>A lattice on a tint must go lighter</h3>
      <p>The instinct is to darken it, as on white. On a mid ground that adds
      weight exactly where the illustration is already short of contrast. Going
      lighter than the ground reads as weave in the paper and sits behind
      everything &mdash; which is why the lattice can be at full strength in
      Deep weave and had to be pulled to a fifth in Weave.</p>
    </div>
    <div class="note">
      <span class="tag">Found</span>
      <h3>Full bleed dims the line art</h3>
      <p>The illustration is drawn in the suit&rsquo;s ink, which was chosen
      against white. On a mid tint it loses contrast &mdash; plains worst, a dark
      gold line on a mid gold ground. Taking this direction means darkening the
      art stroke for it, which is a one-line change but a real one, and it would
      make the deck two sets of drawings unless the darker stroke is adopted
      everywhere.</p>
    </div>
    <div class="note">
      <span class="tag">Watch</span>
      <h3>Weave against the B mark</h3>
      <p>The B mark is hexes and the Weave ground is hexes. At 6&nbsp;mm the first
      pass had them the same size and the mark vanished into the ground; the
      lattice is now down to 3.3&nbsp;mm cells at a fifth of the ink. Still the
      one pairing to check on paper rather than on a screen, because a laser
      printer thickens hairlines.</p>
    </div>
    <div class="note">
      <span class="tag">Watch</span>
      <h3>Full bleed needs bleed</h3>
      <p>Edge-to-edge panels put colour exactly where the guillotine lands.
      Both Full bleed and Deep weave want 3&nbsp;mm of bleed and trim &mdash;
      the same decision the card back is already waiting on, so taking either
      means solving the back at the same time. That is the real cost of Deep
      weave, and it is a production cost rather than a design one.</p>
    </div>
    <div class="note">
      <span class="tag">Board</span>
      <h3>The wash is the only new idea</h3>
      <p>Everything else on the board concept is a relabel. The graded ground
      is the one thing that adds information the printed board does not carry:
      where you are on the ladder is visible from across the table, without
      reading a word.</p>
    </div>
    <div class="note">
      <span class="tag">Board</span>
      <h3>The terrain strip is a duplicate</h3>
      <p>Holds and attack already live on the player aid. Putting them on the
      board too is either a kindness (it is the thing in front of you during the
      map phase) or a second source of truth to keep in sync. Easy to drop
      &mdash; it is four hexes in the header.</p>
    </div>
    <div class="note">
      <span class="tag">Not done</span>
      <h3>This board is a treatment, not a build</h3>
      <p><code>board_a4.py</code> is still the source of truth for geometry and
      for every number. Nothing here has been checked against
      <code>check_rules.py</code>, the WALL column is not drawn, and the
      initiative-die corners are missing. It exists to be judged, not printed.</p>
    </div>
  </div>
</section>

<footer>
  <span>Blink &middot; civ-ladder</span>
  <span>5 card treatments</span>
  <span>deep weave = bleed + weave</span>
  <span>1 board concept</span>
  <span>1 player aid</span>
  <span>lean ladder board</span>
  <span>wall = cap &minus; 2</span>
</footer>

</div>
"""

out = HERE / "variations.html"
out.write_text(HTML, encoding="utf-8")
print("wrote", out, len(HTML), "bytes")
