# -*- coding: utf-8 -*-
"""Builds the proof sheet for the Blink civ-ladder card skin.

    python3 build_skin.py   ->  source/skins/Blink-skin-proof-1.html

Reads civ-ladder.json for the names, art.py for the tech drawings, marks.py for
the A/B/C effect marks and back.py for the card back. Nothing here changes a
rule: the effect bands and the rank/suit grid are read from the same shape the
rulebook prints, and the skin only decides what each card is called and what it
looks like. A second skin is a second JSON file.
"""
import json, pathlib
import art, marks, back
from marks import COLOUR

HERE = pathlib.Path(__file__).resolve().parent
SKIN = json.loads((HERE / "civ-ladder.json").read_text(encoding="utf-8"))

SUITS = ("plains", "forest", "ocean", "mountain")
SAMPLE_RANKS = (4, 8, 12, 18)

# terrain glyphs, lifted verbatim from source/cardstock.py so the skin cannot
# invent a different suit shape from the one the rest of the game prints
GLYPH = {
    "mountain": ('<path d="M2 20 L9 6.5 L13 13 L15.5 9.5 L22 20 Z" fill="{ink}"/>'
                 '<path d="M9 6.5 L6.2 11.9 L9 10.7 L11.3 12.1 Z" fill="#fff"/>'),
    "forest":   ('<path d="M12 2.6 L18.2 12 L14.8 12 L19.6 19 L4.4 19 L9.2 12'
                 ' L5.8 12 Z" fill="{ink}"/>'
                 '<rect x="11" y="18" width="2" height="3.6" fill="{ink}"/>'),
    "plains":   ('<path d="M2.6 19.6 h18.8" stroke="{ink}" stroke-width="1.8"'
                 ' fill="none" stroke-linecap="round"/>'
                 '<path d="M6 19.6 q0 -6 2.4 -8 M11.2 19.6 q-.6 -7.4 1.6 -10'
                 ' M16.6 19.6 q0 -6 2.2 -7.6" stroke="{ink}" stroke-width="1.6"'
                 ' fill="none" stroke-linecap="round"/>'),
    "ocean":    ('<path d="M2.4 8 q3 -3 6 0 t6 0 t5.4 0 M2.4 13.8 q3 -3 6 0 t6 0 t5.4 0'
                 ' M2.4 19.6 q3 -3 6 0 t6 0 t5.4 0" fill="none" stroke="{ink}"'
                 ' stroke-width="1.8" stroke-linecap="round"/>'),
}
GOLD = (2, 3, 4, 5)


def glyph(suit, ink):
    return (f'<svg class="gl" viewBox="0 0 24 24" aria-hidden="true">'
            f'{GLYPH[suit].format(ink=ink)}</svg>')


def card(suit, rank):
    band = (rank - 1) // 5
    age = SKIN["ages"][band]
    ink, pale = COLOUR[suit]["ink"], COLOUR[suit]["pale"]
    name = SKIN["cards"][suit][rank - 1]
    idx = (f'<span class="rk">{rank}</span>{glyph(suit, ink)}')
    ties = band in (1, 3)
    return f"""
<div class="card" style="--ink:{ink};--pale:{pale}">
  <span class="idx">{idx}</span>
  <span class="idx idx-r">{idx}</span>
  <div class="plate">{art.tech(suit, rank)}</div>
  <div class="title">
    <span class="nm">{name}</span>
    <span class="age">{age['numeral']} &middot; {age['name']}</span>
  </div>
  <div class="fx">
    <div class="fxr"><span class="k">A</span>{marks.mark_a(rank, ink, ties)}</div>
    <div class="fxr"><span class="k">B</span>{marks.mark_b(band, suit)}</div>
    <div class="fxr"><span class="k">C</span>{marks.mark_c(GOLD[band], ink)}</div>
  </div>
</div>"""


def ladder_table():
    head = "".join(
        f'<th style="--ink:{COLOUR[s]["ink"]}">'
        f'{glyph(s, COLOUR[s]["ink"])}<span>{SKIN["aspects"][s]["label"]}</span>'
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
        out += '<div class="row">' + "".join(card(s, rank) for s in SUITS) + '</div>'
    return f'<div class="scroll"><div class="deck">{out}</div></div>'


KEY = [
    ("A", marks.mark_a(12, "#3C3833", False),
     "Add this card&rsquo;s own rank to your meld&rsquo;s total for the trick. "
     "The number on the badge is the number already on the card, so nothing "
     "has to be looked up."),
    ("A", marks.mark_a(18, "#3C3833", True),
     "The same, and this meld wins ties. Ranks 6&ndash;10 and 16&ndash;20 only."),
    ("B", marks.mark_b(0, "ocean"),
     "Found a colony: one new tile of this card&rsquo;s suit, one unit standing "
     "on it, fortified."),
    ("B", marks.mark_b(1, "ocean"),
     "The same colony, but the tile may sit up to two out from your "
     "civilisation &mdash; the dotted run counts the gap."),
    ("B", marks.mark_b(2, "ocean"),
     "Open a frontier: two new tiles of this suit, a unit on one of them, "
     "fortified."),
    ("B", marks.mark_b(3, "ocean"),
     "Two colonies on any terrain, a unit on each, both fortified. The "
     "quartered tile is the deck&rsquo;s only way of saying &ldquo;any&rdquo;."),
    ("C", marks.mark_c(4, "#3C3833"),
     "Take that many gold from the bank."),
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

/* ---- the card face: 63 x 88 mm ---- */
.card{position:relative; width:63mm; height:88mm; flex:none; background:#fff;
  border-radius:2.6mm; box-shadow:var(--shadow); overflow:hidden;
  display:flex; flex-direction:column; color:#191713;}
.idx{position:absolute; top:3.6mm; left:4.4mm; display:flex; flex-direction:column;
  align-items:center; line-height:1; z-index:2;}
.idx-r{left:auto; right:4.4mm; transform:scale(.74); transform-origin:top right;}
.idx .rk{font-family:"Fraunces",Georgia,serif; font-weight:600; font-size:19pt;
  line-height:.82; color:var(--ink);}
.idx .gl{width:4.4mm; height:4.4mm; margin-top:1.1mm; display:block;}

.plate{margin:16mm 4.5mm 0; height:28mm; border-radius:1.6mm;
  background:var(--pale); display:flex; align-items:center; justify-content:center;}
.plate .tech{width:21mm; height:21mm; fill:none; stroke:var(--ink);
  stroke-width:1.75; stroke-linecap:round; stroke-linejoin:round;}
.plate .ghost{opacity:.3;}

.title{margin:4.2mm 4.5mm 0; display:flex; flex-direction:column; gap:1.2mm;
  align-items:center; text-align:center;}
.nm{font-family:"Fraunces",Georgia,serif; font-weight:600; font-size:11.4pt;
  line-height:1.05; letter-spacing:.005em; color:#17150F;}
.age{font-family:"IBM Plex Mono",monospace; font-size:6.2pt; letter-spacing:.19em;
  text-transform:uppercase; color:#8C877D;}

.fx{margin:auto 4.5mm 4.2mm; display:flex; flex-direction:column;}
.fxr{display:flex; align-items:center; gap:2.6mm; padding:1.3mm 0;
  border-top:.22mm solid #E2DFD8;}
.fxr .k{font-family:"IBM Plex Mono",monospace; font-size:7.4pt; font-weight:600;
  color:#A9A49A; width:3mm; flex:none;}
.mk{height:5.2mm; width:auto; display:block; overflow:visible;}

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
.keyrow{display:grid; grid-template-columns:16px 62px 1fr; align-items:center;
  gap:14px; padding:13px 0; border-bottom:1px solid var(--rule);}
.keyrow:last-child{border-bottom:none;}
.keyrow .k{font-family:"IBM Plex Mono",monospace; font-size:12px; font-weight:600;
  color:var(--faint);}
.keyrow .kmk{display:flex; align-items:center;}
.keyrow .kmk .mk{height:23px;}
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
<style>{CSS}</style>

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
    <li>16 of 80 illustrations drawn</li>
  </ul>
</header>

<section>
  <div class="h2"><span class="num">01</span><h2>The face</h2></div>
  <p class="lede">Sixteen cards &mdash; one suit per column, one age per row &mdash;
  covering every variant of every effect in the deck. <strong>Rank and suit hold
  the top corners</strong>, so a fanned hand reads and sorts from the left edge
  alone. The illustration sits in a tinted plate, the tech name and its age sit
  under it, and the three effects sit along the bottom <strong>as marks, never
  as sentences</strong>. Shown at print size.</p>
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
  drawn instead of written. Six pieces build all of them: a tile, a unit, a
  fortification, a reach, a coin, and a numeral.</p>
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
      <h3>Suit still means terrain first</h3>
      <p>The aspect meaning lives entirely in the names. Colour, glyph and the
      tinted plate keep saying &ldquo;this card acts on ocean tiles&rdquo;, which
      is the thing a player needs in the map phase.</p>
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
      <span class="tag">Open</span>
      <h3>Both indices are at the top</h3>
      <p>The printed deck repeats the index upside-down in the bottom-right so a
      card works either way up. That corner is now effects. A second top-corner
      index keeps the bottom clean but costs you nothing only if hands are always
      fanned the same way.</p>
    </div>
    <div class="note open">
      <span class="tag">Open</span>
      <h3>Sixty-four drawings to go</h3>
      <p>Ranks 4, 8, 12 and 18 are drawn in all four suits. The rest follow the
      same rules &mdash; one stroke weight, silhouette first, no interior detail
      &mdash; once this style is approved.</p>
    </div>
    <div class="note open">
      <span class="tag">Open</span>
      <h3>Names are a first pass</h3>
      <p>They live in <code>source/skins/civ-ladder.json</code> as plain data, so
      renaming a card is a one-line edit and a second skin is a second file.
      Rank&nbsp;10 is the loosest row &mdash; Census, Waterwheel, The Keep and
      The Compass are not really contemporaries.</p>
    </div>
    <div class="note open">
      <span class="tag">Open</span>
      <h3>The b/w deck</h3>
      <p>Every drawing is a stroke with no fill, so it survives a mono printer
      unchanged. The back does not: parchment and blue both flatten to mid-grey.
      It would need the hatch treatment the terrain tiles already use.</p>
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

out = HERE / "Blink-skin-proof-1.html"
out.write_text(HTML, encoding="utf-8")
print("wrote", out, len(HTML), "bytes")
