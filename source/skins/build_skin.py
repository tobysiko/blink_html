# -*- coding: utf-8 -*-
"""Builds the proof sheet for the Blink civ-ladder skin."""
import json, pathlib
import back, face, marks
from marks import COLOUR
from face import SUITS, GOLD

HERE = pathlib.Path(__file__).resolve().parent
SKIN = json.loads((HERE / "civ-ladder.json").read_text(encoding="utf-8"))

SAMPLE_RANKS = (4, 8, 12, 18)


def ladder_table():
    head = "".join(
        f'<th style="--ink:{COLOUR[s]["ink"]}">'
        f'{face.glyph(s, COLOUR[s]["ink"])}<span>{SKIN["aspects"][s]["label"]}</span>'
        f'<em>{SKIN["aspects"][s]["long"]}</em></th>' for s in SUITS)
    rows = ""
    for rank in range(1, 21):
        band = (rank - 1) // 5
        if rank % 5 == 1:
            a = SKIN["ages"][band]
            rows += (f'<tr class="ageband"><td colspan="5">'
                     f'<span class="rn">{a["numeral"]}</span>'
                     f'<span class="an">{a["name"]}</span>'
                     f'<span class="ar">ranks {a["ranks"]} &middot; '
                     f'{a["half"]} half of the deck</span></td></tr>')
        cells = "".join(
            f'<td>{SKIN["cards"][s][rank - 1]}</td>' for s in SUITS)
        rows += f'<tr><td class="rk">{rank}</td>{cells}</tr>'
    return (f'<div class="scroll"><table class="ladder">'
            f'<thead><tr><th class="rk">Rank</th>{head}</tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')


def sample_grid():
    out = ""
    for rank in SAMPLE_RANKS:
        age = SKIN["ages"][(rank - 1) // 5]
        out += (f'<div class="rowlabel"><span class="rn">{age["numeral"]}</span>'
                f'<span class="an">{age["name"]}</span>'
                f'<span class="ar">rank {rank}</span></div>')
        out += '<div class="row">' + "".join(face.card(s, rank, SKIN) for s in SUITS) + '</div>'
    return f'<div class="scroll"><div class="deck">{out}</div></div>'


KEY = [
    ("A", marks.mark_a("#3C3833", False),
     "Add this card&rsquo;s own rank to your meld&rsquo;s total for the trick. The "
     "badge is card-shaped because A is the only effect that happens in the card "
     "phase; it does not restate the rank, which is printed in all four corners "
     "already, and a plus sign survives a half turn where a numeral does not."),
    ("A", marks.mark_a("#3C3833", True),
     "The same, and this meld wins ties &mdash; the equals sign is the tie itself, "
     "and it too is unchanged upside-down. Ranks 6&ndash;10 and 16&ndash;20 only."),
    ("B", marks.mark_b(0, "ocean"),
     "Found a colony: one new tile of this card&rsquo;s suit, one unit standing "
     "on it, fortified. The hex is pointy-top, the orientation the map is "
     "actually laid in; the ring around it is the fortification."),
    ("B", marks.mark_b(1, "ocean"),
     "The same colony, but the tile may sit up to two out from your "
     "civilisation &mdash; the dotted run counts the gap."),
    ("B", marks.mark_b(2, "ocean"),
     "Open a frontier: two new tiles of this suit, a unit on one of them, "
     "fortified."),
    ("B", marks.mark_b(3, "ocean"),
     "Two colonies on any terrain, a unit on each, both fortified. The four "
     "strata are the deck&rsquo;s only way of saying &ldquo;any&rdquo;."),
    ("C", marks.mark_c(4, "#3C3833"),
     "Take that many gold from the bank &mdash; counted in coins rather than "
     "written as a numeral, so it reads from either end. Two to five, which is "
     "inside the range a person counts at a glance."),
]


def key_list():
    return "".join(
        f'<div class="keyrow"><span class="k">{k}</span>'
        f'<span class="kmk">{svg}</span><p>{txt}</p></div>'
        for k, svg, txt in KEY)


CSS = """
:root{
  --ground:#DCDBD5; --raise:#E7E6E1; --ink:#191A18; --soft:#5F5E58;
  --faint:#8B8A83; --rule:#C4C3BC; --seam:#9B7A16;
  --shadow:0 1px 2px rgba(30,28,22,.10), 0 10px 26px rgba(30,28,22,.16);
}
:root:not([data-theme="light"]){ }
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

/* ---- masthead ---- */
.mast{padding:56px 0 30px; border-bottom:1px solid var(--rule);
  display:flex; flex-direction:column; gap:9px;}
.eyebrow{font-family:"IBM Plex Mono",monospace; font-size:11px;
  letter-spacing:.18em; text-transform:uppercase; color:var(--faint); margin:0;}
h1{font-family:"Fraunces",Georgia,serif; font-weight:600; font-size:clamp(34px,5.4vw,54px);
  line-height:1.02; letter-spacing:-.012em; margin:0; text-wrap:balance;}
.sub{margin:0; max-width:60ch; color:var(--soft); font-size:17px;}
.meta{display:flex; flex-wrap:wrap; gap:6px 22px; margin:10px 0 0; padding:0;
  list-style:none; font-family:"IBM Plex Mono",monospace; font-size:11.5px;
  letter-spacing:.06em; color:var(--faint);}

/* ---- sections ---- */
section{padding-top:52px;}
.h2{display:flex; align-items:baseline; gap:14px; margin-bottom:6px;}
.h2 .num{font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--faint);
  letter-spacing:.12em; padding-top:4px;}
h2{font-family:"Fraunces",Georgia,serif; font-weight:600; font-size:27px;
  margin:0; letter-spacing:-.006em;}
.lede{max-width:66ch; color:var(--soft); margin:0 0 26px;}
.lede strong{color:var(--ink); font-weight:600;}

.scroll{overflow-x:auto; padding-bottom:8px;}
/* the proof floats the cards on a proofing ground; the deck sheet does not */
.card{flex:none; border-radius:2.6mm; box-shadow:var(--shadow);}
.deck{display:flex; flex-direction:column; gap:8px; min-width:1052px;}
.row{display:flex; gap:16px;}
.rowlabel{display:flex; align-items:baseline; gap:11px; padding:20px 0 4px;
  border-top:1px solid var(--rule);}
.rowlabel:first-child{border-top:none; padding-top:0;}
.rowlabel .rn{font-family:"Fraunces",Georgia,serif; font-size:20px;
  font-weight:600; color:var(--seam); min-width:26px;}
.rowlabel .an{font-family:"IBM Plex Mono",monospace; font-size:11.5px;
  letter-spacing:.17em; text-transform:uppercase;}
.rowlabel .ar{font-family:"IBM Plex Mono",monospace; font-size:11.5px;
  color:var(--faint); letter-spacing:.06em;}

/* ---- backs ---- */
.backs{display:flex; gap:22px; flex-wrap:wrap; align-items:flex-start;}
.cardback{width:63mm; height:88mm; flex:none; border-radius:2.6mm;
  box-shadow:var(--shadow); display:block;}
.backnote{max-width:34ch; color:var(--soft); font-size:14px;}
.backnote h3{font-family:"Fraunces",Georgia,serif; font-size:17px; font-weight:600;
  margin:0 0 8px; color:var(--ink);}
.backnote p{margin:0 0 12px;}

/* ---- key ---- */
.keys{display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr));
  gap:0 34px; background:var(--raise); border-radius:4px; padding:8px 22px;}
.keyrow{display:grid; grid-template-columns:16px 92px 1fr; align-items:center;
  gap:14px; padding:13px 0; border-bottom:1px solid var(--rule);}
.keyrow:last-child{border-bottom:none;}
.keyrow .k{font-family:"IBM Plex Mono",monospace; font-size:12px; font-weight:600;
  color:var(--faint);}
.keyrow .kmk{display:flex; align-items:center;}
.keyrow .kmk .mk{height:26px;}
.keyrow p{margin:0; font-size:13.6px; line-height:1.45; color:var(--soft);}

/* ---- the ladder ---- */
.ladder{border-collapse:collapse; width:100%; min-width:860px;}
.ladder th{text-align:left; vertical-align:bottom; padding:0 16px 12px 0;
  border-bottom:1.5px solid var(--ink); width:23%;}
.ladder th .gl{width:15px; height:15px; display:block; margin-bottom:6px;}
.ladder th span{display:block; font-family:"IBM Plex Mono",monospace; font-size:11.5px;
  letter-spacing:.17em; text-transform:uppercase; color:var(--ink);}
.ladder th em{display:block; font-style:normal; font-size:11.5px; color:var(--faint);
  font-weight:400; letter-spacing:0; text-transform:none; margin-top:3px;
  max-width:22ch; line-height:1.35;}
.ladder th.rk{width:52px;}
.ladder td{padding:6px 16px 6px 0; border-bottom:1px solid var(--rule);
  font-size:14.4px;}
.ladder td.rk{font-family:"IBM Plex Mono",monospace; font-variant-numeric:tabular-nums;
  color:var(--faint); font-size:12.5px;}
.ladder tr.ageband td{border-bottom:none; padding:22px 0 6px;}
.ladder tr.ageband .rn{font-family:"Fraunces",Georgia,serif; font-size:17px;
  font-weight:600; color:var(--seam); margin-right:11px;}
.ladder tr.ageband .an{font-family:"IBM Plex Mono",monospace; font-size:11.5px;
  letter-spacing:.17em; text-transform:uppercase; margin-right:14px;}
.ladder tr.ageband .ar{font-family:"IBM Plex Mono",monospace; font-size:11.5px;
  color:var(--faint);}

/* ---- notes ---- */
.notes{display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
  gap:2px; background:var(--rule); border:1px solid var(--rule);}
.note{background:var(--raise); padding:20px 22px 22px;}
.note h3{font-family:"Fraunces",Georgia,serif; font-size:17px; font-weight:600;
  margin:0 0 4px; text-wrap:balance;}
.note .tag{font-family:"IBM Plex Mono",monospace; font-size:10.5px;
  letter-spacing:.16em; text-transform:uppercase; color:var(--faint);
  display:block; margin-bottom:9px;}
.note p{margin:0; font-size:14px; color:var(--soft); line-height:1.5;}
.note.open{border-left:3px solid var(--seam);}

footer{margin-top:56px; padding-top:20px; border-top:1px solid var(--rule);
  font-family:"IBM Plex Mono",monospace; font-size:11.5px; color:var(--faint);
  display:flex; flex-wrap:wrap; gap:6px 22px;}

@media print{
  body{background:#fff;}
  .wrap{max-width:none; padding:0;}
  .card,.cardback{box-shadow:none; border:.2mm dashed #bbb;}
  section,.mast,.notes,.keys{break-inside:avoid;}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""

HTML = f"""<title>The Civilisation Ladder</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{CSS}{face.CARD_CSS}</style>

<div class="wrap">

<header class="mast">
  <p class="eyebrow">Blink &middot; card skin &middot; proof 1</p>
  <h1>The Civilisation Ladder</h1>
  <p class="sub">A naming and drawing skin for the eighty-card main deck. Rank
  is the age axis, suit is the aspect axis, and the four ages are exactly the
  four rank bands the rules already print &mdash; so the theme never has to be
  reconciled with the mechanics. No rule changes.</p>
  <ul class="meta">
    <li>80 cards &middot; 4 suits &times; ranks 1&ndash;20</li>
    <li>63 &times; 88 mm</li>
    <li>rules v0.24</li>
    <li>same either way up</li>
    <li>16 of 80 illustrations drawn</li>
  </ul>
</header>

<section>
  <div class="h2"><span class="num">01</span><h2>The face</h2></div>
  <p class="lede">Sixteen cards &mdash; one suit per column, one age per row &mdash;
  covering every variant of every effect in the deck. <strong>Rank and suit hold
  both top corners</strong>: the numeral in the suit&rsquo;s saturated tone, the
  terrain glyph knocked out of a solid hex the same shape as the tiles on the
  table. The illustration sits in a tinted plate; the tech name and its age sit
  under it; the three effects sit along the bottom <strong>as marks, never as
  sentences</strong>, pulled in on both sides so they stay on the card&rsquo;s centre
  axis while the rotated index keeps its corner. Shown at print size.</p>
  {sample_grid()}
</section>

<section>
  <div class="h2"><span class="num">02</span><h2>The back</h2></div>
  <p class="lede">One diagonal, drawn corner to corner. Below it the made world
  in parchment and sepia &mdash; a cartwheel, an amphora, an arch, a ship, the
  furrows of a field. Above it the world still being drawn, in cold blue: orbits,
  a printed trace, a lattice, a signal. Both ornament layers run the full height
  of the card and are then cut by the seam, so the drawings themselves are
  severed rather than politely arranged around it.</p>
  <div class="backs">
    {back.back("a")}
    <div class="backnote">
      <h3>The wordmark is set twice</h3>
      <p>BLINK runs down the centre in one continuous stack. The same five
      letters are drawn once in sepia, clipped to the parchment side, and once
      in near-white, clipped to the blue &mdash; so the letter the seam happens
      to cross is <em>split along the diagonal</em>, ink above the cut and light
      below it. Nothing is positioned by hand; move the seam and the split
      follows.</p>
      <h3>Before this is printed</h3>
      <p>A full-bleed back is unforgiving on a home printer: a millimetre of
      trim error shows on all four edges, and nine gradients to an A4 sheet is
      a lot of toner. Two options &mdash; add 3&nbsp;mm bleed and trim, or pull
      the art in to leave a quiet parchment margin that hides the error. Worth
      deciding before the next print run.</p>
    </div>
  </div>
</section>

<section>
  <div class="h2"><span class="num">03</span><h2>The marks</h2></div>
  <p class="lede">There are only twelve effects in the whole deck &mdash; four
  rank bands &times; A / B / C &mdash; which is why the bottom of the card can be
  drawn instead of written. Six pieces build all of them: a <strong>hex</strong>,
  a unit, a rampart, a reach, a coin, and a card. Every one of the six is unchanged
  by a half turn &mdash; and <strong>the shape says which phase the effect belongs
  to</strong>: hexes act on the map, discs are coins, and A&rsquo;s badge is a
  little card, in the same 0.72 proportion as the card it is printed on, because it
  acts in the card phase. The hex is taken from <code>figs.py</code>, so the mark on
  the card and the tile in the box are the same object. They are listed here A&ndash;C, but <strong>printed on the card
  in reverse</strong>: C at the top, A at the bottom, so a card turned around in
  the victory row leads with&nbsp;A.</p>
  <div class="keys">{key_list()}</div>
</section>

<section>
  <div class="h2"><span class="num">04</span><h2>All eighty names</h2></div>
  <p class="lede">Read down a column and one aspect of a civilisation climbs.
  Read across a row and the four aspects sit in roughly the same age, which is
  what makes rank feel like progress rather than a bigger number. The break at
  rank&nbsp;10 is not decorative: it is where the deck itself splits into the
  half you start with and the half you research.</p>
  {ladder_table()}
</section>

<section>
  <div class="h2"><span class="num">05</span><h2>What is settled and what is not</h2></div>
  <div class="notes">
    <div class="note">
      <span class="tag">Settled</span>
      <h3>Hexes, pointy-top</h3>
      <p>The B marks drew rounded squares, which said &ldquo;square grid&rdquo;.
      They are now hexes at the same orientation <code>figs.py</code> lays the
      map in, so the mark on the card and the tile in the box are the same
      object. &ldquo;Any terrain&rdquo; is four strata rather than four quarters,
      and <strong>fortified became a ring around the tile</strong> rather than a
      shield badge beside it &mdash; at 6&nbsp;mm a hex, a disc and a badge in
      one square simply merged into a blob.</p>
    </div>
    <div class="note">
      <span class="tag">Settled</span>
      <h3>Four corners, and a mirrored face</h3>
      <p>A meld is played face up to the table, and the players opposite have to
      read its ranks &mdash; to check the run is unbroken and to total it for
      initiative. They never need the name or the picture, and those are the only
      things on the card with a definite up. <strong>The rank is the one element
      that becomes unreadable upside-down</strong>, so the index is the one
      element made rotationally symmetric: rotate the card and top-left lands on
      bottom-right, top-right on bottom-left.</p>
    </div>
    <div class="note">
      <span class="tag">Settled</span>
      <h3>Printed C, B, A &mdash; and A set apart by shape</h3>
      <p>The rows run C, B, A down the face, so a card turned around in the
      victory row &mdash; where its effects are actually spent &mdash; leads with
      A, the one that decides a trick. In hand the order is upside-down, which
      costs nothing: you never spend an effect from your hand.</p>
      <p>C and B are both map phase; A is not. Rather than label the seam, the
      <strong>shape</strong> carries it: hexes for the map, discs for coins, and a
      little card for the card phase. A slightly firmer rule sits above A as a
      second, quieter signal. Both travel with the rows, so a turned card still
      shows the break between A and B.</p>
    </div>
    <div class="note">
      <span class="tag">Settled</span>
      <h3>Four ages, not five</h3>
      <p>The ages match the effect bands (1&ndash;5, 6&ndash;10, 11&ndash;15,
      16&ndash;20), not the five player tiers. Tiers keep their own names &mdash;
      Tribe, Settlement, Kingdom, Empire, Civilisation &mdash; and they describe
      you, while ages describe the card.</p>
    </div>
    <div class="note open">
      <span class="tag">Open &middot; your call</span>
      <h3>Rotated text always looks like a mistake</h3>
      <p>The first attempt at a mirrored centre band printed the age line twice,
      once upside-down, and doubled the A&nbsp;/&nbsp;B&nbsp;/&nbsp;C letters the
      same way. Both read as typos rather than as symmetry &mdash; corner numerals
      only get away with it because playing cards have trained everyone to expect
      exactly that. So the letters are gone from the face and the age is
      <strong>pips</strong>, which are countable from either end. The aid names
      A&nbsp;/&nbsp;B&nbsp;/&nbsp;C; the three marks are distinct enough to carry
      themselves.</p>
    </div>
    <div class="note open">
      <span class="tag">Open &middot; your call</span>
      <h3>Ascending left to right</h3>
      <p>Worth encouraging, not requiring. Melds are runs, so players sort
      ascending on their own; hands are private, so a standard order leaks
      nothing; and the strong top-left index rewards it. That makes it a line in
      the player aid &mdash; &ldquo;keep your hand in rank order, melds are
      runs&rdquo; &mdash; and not a rule. An unenforceable rule that changes no
      legality is exactly the kind of weight the deck has been shedding.</p>
    </div>
    <div class="note">
      <span class="tag">Settled</span>
      <h3>The name stays single</h3>
      <p>Setting the tech name twice &mdash; once at the top, once rotated at the
      bottom &mdash; would complete the mirror, but it would put the largest text
      on the card into the quiet corner zones and hand the most prominence to the
      element with the least consequence. It is flavour. It sits once, on the
      mirror axis itself, which is the one place a single asymmetric element is
      defensible.</p>
    </div>
    <div class="note open">
      <span class="tag">Open</span>
      <h3>Sixty-four drawings, and the names</h3>
      <p>Ranks 4, 8, 12 and 18 are drawn in all four suits; the rest follow the
      same rules once the style is approved. Names live in
      <code>source/skins/civ-ladder.json</code>, so renaming is a one-line edit.
      Rank&nbsp;10 is the loosest row &mdash; Census, Waterwheel, The Keep and
      The Compass are not really contemporaries.</p>
    </div>
    <div class="note open">
      <span class="tag">Open</span>
      <h3>The b/w deck and the back</h3>
      <p>Every drawing is a stroke with no fill, so the faces survive a mono
      printer unchanged. The back does not: parchment and blue both flatten to
      mid-grey. It would need the hatch treatment the terrain tiles already use.
      The full-bleed back also still wants either 3&nbsp;mm of bleed or a quiet
      margin before it meets a home printer.</p>
    </div>
  </div>
</section>

<footer>
  <span>Blink &middot; skin proof 1</span>
  <span>civ-ladder</span>
  <span>rules v0.24</span>
  <span>no rule changes</span>
</footer>

</div>
"""

out = HERE / "Blink-skin-proof.html"
out.write_text(HTML, encoding="utf-8")
print("wrote", out, len(HTML), "bytes")
