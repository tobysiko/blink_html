# -*- coding: utf-8 -*-
import json, pathlib, re
from version import VTAG, RULES_HTML

# Anchored to this file. build_pdfs.sh always runs the builders from source/,
# so a bare name worked — but check_figs.py IMPORTS this module for its scale
# constants, and an import inherits the caller's working directory. Running a
# checker from the project root therefore died on a missing figs.json before it
# had checked anything. Reading an input by absolute path costs nothing; where
# this module WRITES is guarded by __main__ below, for the same reason.
F = json.loads((pathlib.Path(__file__).resolve().parent / "figs.json").read_text())

CSS = """
:root{
  --paper:#EDEAE1; --page:#FBFAF6; --ink:#1C1F1D; --ink-soft:#5A5F59;
  --plains:#C9992B; --forest:#37704A; --ocean:#256A8C; --stone:#8A837A;
  --red:#C0392B; --rule:#CDC7B8;
  --measure:38rem;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:"IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  font-size:16px; line-height:1.62; font-weight:400;
}
.sheet{max-width:60rem;margin:0 auto;background:var(--page);
  box-shadow:0 0 0 1px rgba(0,0,0,.07),0 18px 50px -30px rgba(0,0,0,.5);}
.pad{padding:0 clamp(1.25rem,5vw,4.5rem)}

/* ---------- masthead ---------- */
.mast{padding:clamp(2rem,6vw,4rem) 0 1.5rem;position:relative;overflow:hidden}
.eyebrow{font-family:"IBM Plex Mono",monospace;font-size:.7rem;letter-spacing:.22em;
  text-transform:uppercase;color:var(--ink-soft);margin:0 0 1rem}
.mast h1{font-family:Fraunces,Georgia,serif;font-variation-settings:"SOFT" 20,"WONK" 1;
  font-weight:600;font-size:clamp(3rem,12vw,6.5rem);line-height:.86;margin:0;
  letter-spacing:-.03em}
.mast .sub{font-family:Fraunces,Georgia,serif;font-weight:400;font-style:italic;
  font-size:clamp(1.05rem,3vw,1.5rem);color:var(--ink-soft);margin:.6rem 0 0;letter-spacing:-.01em}
.mast .meta{font-family:"IBM Plex Mono",monospace;font-size:.75rem;letter-spacing:.1em;
  color:var(--ink-soft);margin:1.4rem 0 0;text-transform:uppercase}
.mast .meta span{display:inline-block;margin-right:1.4rem;white-space:nowrap}
.herowrap{margin:1.5rem 0 0}
.herowrap svg{width:100%;height:auto;display:block;max-height:19rem}

/* ---------- stepped rule: the signature ---------- */
.steprule{display:flex;align-items:flex-end;height:16px;margin:0;gap:0}
.steprule i{display:block;flex:1}
.steprule i:nth-child(1){height:5px;background:var(--plains)}
.steprule i:nth-child(2){height:16px;background:var(--stone)}
.steprule i:nth-child(3){height:11px;background:var(--forest)}
.steprule i:nth-child(4){height:5px;background:var(--ocean)}

/* ---------- sections ---------- */
section{padding:2.4rem 0 .5rem;border-top:1px solid var(--rule)}
section:first-of-type{border-top:none}
.h2{display:flex;align-items:baseline;gap:1rem;margin:0 0 1.1rem}
.h2 .num{font-family:"IBM Plex Mono",monospace;font-size:.78rem;color:var(--stone);
  letter-spacing:.12em;padding-top:.35rem;min-width:2.2rem}
.h2 h2{font-family:Fraunces,Georgia,serif;font-variation-settings:"SOFT" 20,"WONK" 1;
  font-weight:600;font-size:clamp(1.5rem,4vw,2.15rem);line-height:1.06;margin:0;
  letter-spacing:-.02em}
h3{font-family:Fraunces,Georgia,serif;font-weight:600;font-size:1.12rem;margin:1.9rem 0 .5rem;
  letter-spacing:-.01em}
p{margin:0 0 .95rem;max-width:var(--measure)}
.lede{font-size:1.08rem;color:var(--ink-soft);max-width:44rem}
ul,ol{max-width:var(--measure);margin:0 0 1rem;padding-left:1.15rem}
li{margin:0 0 .42rem}
strong{font-weight:600}
em{font-style:italic}

/* ---------- terrain chips ---------- */
/* the swatch is absolutely positioned so its height — which encodes terrain
   elevation — never changes the line box, keeping table rows aligned */
.chip{display:inline-block;position:relative;padding-left:1.05em;font-weight:600;
  white-space:nowrap}
.chip::before{content:"";position:absolute;left:0;bottom:.16em;width:.62em;border-radius:1px}
.chip.plains::before{height:.34em;background:var(--plains)}
.chip.ocean::before{height:.34em;background:var(--ocean)}
.chip.forest::before{height:.72em;background:var(--forest)}
.chip.mountain::before{height:1.05em;background:var(--stone)}

/* ---------- figures ---------- */
figure{margin:1.6rem 0 1.8rem;max-width:none}
/* one scale for every diagram: the svg carries its own px size, we never stretch it */
figure svg{display:block;max-width:100%;height:auto}
.figbox{background:#F6F4ED;border:1px solid var(--rule);border-radius:4px;
  padding:1.1rem .9rem;display:flex;justify-content:center;align-items:center}
.figbox.plain{background:none;border:none;padding:.35rem 0}
figcaption{font-family:"IBM Plex Mono",monospace;font-size:.72rem;line-height:1.5;
  color:var(--ink-soft);margin-top:.6rem;letter-spacing:.02em;max-width:var(--measure)}
.fig-label{font-family:"IBM Plex Sans",sans-serif;fill:#5A5F59}
.fig-strong{font-family:"IBM Plex Sans",sans-serif;fill:#1C1F1D;font-weight:600}
.fig-step{font-family:"IBM Plex Mono",monospace;fill:#8A837A;letter-spacing:.06em}
.fig-rank{font-family:Fraunces,Georgia,serif;fill:#1C1F1D;font-weight:600}
.fig-attack{font-family:"IBM Plex Sans",sans-serif;fill:#C0392B;font-weight:600}
.fig-key{font-family:"IBM Plex Sans",sans-serif;fill:#1C1F1D;font-weight:600;letter-spacing:.04em}
.fig-num{font-family:"IBM Plex Mono",monospace;fill:#FBFAF6;font-weight:500}
.fig-fine{font-family:"IBM Plex Mono",monospace;fill:#8A837A}

/* ---------- meld grid ---------- */
.tiergroup{break-inside:avoid;margin-top:2rem}
.example h3{color:var(--ink)} .example .h2 .num{color:var(--forest)}.tier{display:flex;align-items:baseline;gap:.6rem;margin:0 0 .2rem;
  padding-bottom:.35rem;border-bottom:1.5px solid var(--ink)}
.tier-n{font-family:Fraunces,Georgia,serif;font-weight:600;font-size:1.9rem;
  line-height:1;letter-spacing:-.02em}
.tier-t{font-family:"IBM Plex Mono",monospace;font-size:.72rem;letter-spacing:.13em;
  text-transform:uppercase;color:var(--stone)}
.melds{display:grid;grid-template-columns:repeat(2,1fr);
  gap:1.4rem 1.6rem;margin:1.1rem 0 .5rem}
.melds figure{margin:0;max-width:none;display:flex;flex-direction:column;break-inside:avoid}
.melds figure svg{display:block;max-width:100%;height:auto;margin:0 auto}
.melds .name{font-family:Fraunces,Georgia,serif;font-weight:600;font-size:1rem;margin:0 0 .1rem}
.melds .rule{font-size:.82rem;color:var(--ink-soft);line-height:1.45;margin:0}
.melds .shape{font-size:.82rem;margin:.35rem 0 0;line-height:1.45}
.melds .shape b{font-weight:600}
@media (max-width:640px){.melds{grid-template-columns:repeat(2,1fr)}}

/* ---------- tables ---------- */
table{border-collapse:collapse;width:100%;max-width:var(--measure);margin:1rem 0 1.4rem;
  font-size:.92rem}
table.wide{max-width:none}
th{text-align:left;font-family:"IBM Plex Mono",monospace;font-size:.68rem;font-weight:500;
  letter-spacing:.13em;text-transform:uppercase;color:var(--stone);
  border-bottom:1.5px solid var(--ink);padding:0 .7rem .4rem 0;vertical-align:bottom}
td{padding:.5rem .7rem .5rem 0;border-bottom:1px solid var(--rule);vertical-align:top}
td:last-child,th:last-child{padding-right:0}
.num-cell{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums}

/* ---------- callout ---------- */
.note{border-left:3px solid var(--plains);padding:.1rem 0 .1rem 1rem;margin:1.3rem 0;
  max-width:var(--measure)}
.note p{margin:0 0 .5rem}
.note p:last-child{margin:0}
.note .tag{font-family:"IBM Plex Mono",monospace;font-size:.68rem;letter-spacing:.14em;
  text-transform:uppercase;color:var(--stone);display:block;margin-bottom:.3rem}

/* ---------- sequence ---------- */
.seq{list-style:none;padding:0;counter-reset:s;max-width:var(--measure)}
.seq>li{counter-increment:s;position:relative;padding-left:2.4rem;margin:0 0 .8rem}
.seq>li::before{content:counter(s);position:absolute;left:0;top:.05rem;
  font-family:"IBM Plex Mono",monospace;font-size:.72rem;color:var(--ink);
  background:var(--page);border:1.5px solid var(--ink);width:1.5rem;height:1.5rem;border-radius:50%;
  display:flex;align-items:center;justify-content:center}

/* ---------- reference back page ---------- */
.ref{background:var(--paper);color:var(--ink);border-top:2px solid var(--ink);
  margin-top:2.5rem;padding-bottom:3rem}
.ref section{border-top-color:var(--rule)}
.ref .h2 h2,.ref h3{color:var(--ink)}
.ref .h2 .num{color:#9A948A}
.ref p,.ref li{color:var(--ink-soft)}
.ref td{border-bottom-color:var(--rule)}
.ref th{color:var(--stone);border-bottom-color:var(--ink)}
.ref .cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1.6rem 2.4rem}
.ref .cols>div{max-width:none}
.ref .cols p,.ref .cols ul{max-width:none}
.ref .note{border-left-color:var(--plains)}
.ref .note .tag{color:#9A948A}

footer{padding:2rem 0 3rem;font-family:"IBM Plex Mono",monospace;font-size:.72rem;
  color:var(--ink-soft);letter-spacing:.06em}

@page{
  size:A4;
  margin:18mm 16mm 16mm 16mm;
}
@media print{
  html,body{background:#fff}
  .example{background:#F3F1EA;padding:.5rem 6mm;margin:0 -6mm;border-radius:4px}
  body{font-size:10.3pt;line-height:1.5}
  .sheet{box-shadow:none;max-width:none;margin:0;background:#fff}
  /* padding is provided by the @page margin, so drop the fluid inner pad */
  .pad{padding:0}
  .mast{padding:0 0 1rem}
  /* let text fill the printable width instead of the 38rem screen measure */
  p,ul,ol,figure,.lede,.melds figure,.note{max-width:none}
  figcaption{max-width:none}
  section{break-inside:auto;padding:1.2rem 0 .4rem}
  /* keep atomic blocks whole */
  figure,table,.note,.tiergroup,.pat,.seq li,tr{break-inside:avoid}
  .h2,h3,thead{break-after:avoid}
  h3{margin-top:1.3rem}
  .herowrap svg{max-height:15rem}
  /* figures keep their intrinsic size so the scale stays constant across the book */
  figure svg{max-width:100%;height:auto;display:block;margin:0 auto}
  .melds figure svg{max-width:100%;height:auto;margin:0 auto}
  .figbox{background:#F7F5EF;border-color:#DDD8CB}
  .ref{background:#fff;color:#000;border-top:2px solid #000}
  .ref .h2 h2,.ref h3,.ref p,.ref li{color:#000}
  .ref th{color:#555;border-bottom-color:#000}
  .ref td{border-bottom-color:#ccc}
  .ref .h2 .num{color:#777}
  .gloss{columns:2;column-gap:2rem}
  .gloss dt{break-inside:avoid}
  .gloss dd{break-inside:avoid}
  #quickref{break-before:page;padding-top:0}
  #quickref .cols{gap:.2rem 1.6rem}
  #quickref h3{margin:.55rem 0 .15rem;font-size:.98rem}
  #quickref p{font-size:8.6pt;line-height:1.38;margin:0 0 .3rem}
}
@media (max-width:640px){
  body{font-size:15px}
  .opener{break-after:page}
  .h2{gap:.7rem}
  .h2 .num{min-width:1.8rem}
}
/* SCREEN ONLY, and the word `screen` is load-bearing. This is the entrance
   animation for a sheet, and it starts at opacity:0. Chrome's
   `--print-to-pdf` takes its snapshot the moment the page loads, before an
   animation has advanced a frame - so with this rule live in print, every
   document built from this stylesheet rendered as the right number of
   correctly paginated, completely EMPTY pages. The 28-page rulebook came out
   at 13 kB, and the only visible symptom was check_fonts.py reporting that it
   had embedded no fonts, because there was no text to set. */
@media screen and (prefers-reduced-motion:no-preference){
  .sheet{animation:rise .5s ease-out}
  @keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
}
/* And nothing else animates on paper either, whatever gets added later. */
@media print{*,*::before,*::after{animation:none!important;transition:none!important}}
"""


CSS += """
.opener .lede{font-size:1.06rem}
.contents{border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);
  padding:.7rem 0;margin:1.4rem 0 0}
.contents .tag{font-family:"IBM Plex Mono",monospace;font-size:.66rem;letter-spacing:.14em;
  text-transform:uppercase;color:var(--stone);display:block;margin-bottom:.3rem}
.contents p{margin:0;font-size:.86rem;line-height:1.7;color:var(--stone)}
.contents b{color:var(--ink)}
p.fine{font-size:.84rem;color:var(--stone);margin:.5rem 0 0}
.gloss dt{font-weight:600;margin:.7rem 0 0;break-after:avoid}
.gloss dd{margin:.1rem 0 0;color:var(--stone);break-before:avoid}
"""


# ---------------------------------------------------------------- figure scale
# Figures are sized in CSS px per SVG user unit, NOT stretched to the column.
# The rule: anything a reader might compare shares a scale; a close-up may
# deliberately break it. Three tiers, assigned by hand:
#
#   COMPARE (1.07) - every figure containing map hexes or hand cards that is
#       meant to be read against another: the meld panels, the starting maps,
#       explore, the terrain key. A hex is the
#       same size in all of them. 1.07 is the largest value at which the widest
#       of these still fits the print column and the widest meld panel still
#       fits its grid cell.
#   DETAIL (1.60) - single-mechanism close-ups with only a few objects, where
#       the point is to look closely: attacking, fortifying, the card market.
#       Larger on purpose, and never sitting beside a COMPARE figure.
#   COMPONENT (1.22) - schematics of physical components rather than of the
#       map: the player board and the victory row. Sized to fill the column.
COMPARE, DETAIL, COMPONENT = 1.07, 1.60, 1.22
# The market figure grew when the grid went from 2x3 to 3x3 and has overflowed
# the print column ever since — check_figs.py has been failing on it. It gets
# its own scale so nine positions fit the page instead of being clipped.
MARKET = 1.45
# The whole-table view is the widest thing in the book by some way — it has to
# hold the map, the market, the supply, the play area and three seats at once —
# so it gets a scale that lets it fill the column exactly rather than being
# shrunk to fit beside figures it has nothing to do with.
TABLE = 0.98
SCALE = {
    # Fortify grew a second half in v0.24 — a refusal beside a fight — and no
    # longer fits at DETAIL. It is still a close-up, just a wider one.
    "combat": DETAIL, "fortify": 1.35, "market": 1.1,
    "board": COMPONENT, "vprow": COMPONENT, "table": TABLE,
}
_VB = re.compile(r'viewBox="(-?[\d.]+) (-?[\d.]+) ([\d.]+) ([\d.]+)"')


def sized(markup, key):
    """Give an SVG an intrinsic px size from its viewBox at its tier's scale."""
    m = _VB.search(markup)
    if not m:
        return markup
    sc = SCALE.get(key, COMPARE)
    w = float(m.group(3)) * sc
    h = float(m.group(4)) * sc
    return markup.replace('<svg class="fig"',
                          f'<svg class="fig" width="{w:.1f}" height="{h:.1f}"', 1)


def fig(key, caption, wide=False):
    return (f'<figure><div class="figbox">{sized(F[key], key)}</div>'
            f'<figcaption>{caption}</figcaption></figure>')


def meld_tiers():
    """Removed in v0.22 — the meld taxonomy it listed no longer exists."""
    raise NotImplementedError("v0.21 API; v0.22 has one meld rule, see fig 'meld_rule'")


HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Blink — Rules {VTAG}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400..600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="sheet">

<header class="mast pad">
  <p class="eyebrow">A meld-building civilization game</p>
  <h1>Blink</h1>
  <p class="sub">Climbing the ladder of civilization</p>
  <p class="meta"><span>2–4 players</span><span>45–90 minutes</span><span>Toby Siko</span></p>
  <div class="herowrap">{F['hero']}</div>
</header>
<div class="steprule"><i></i><i></i><i></i><i></i></div>

<main class="pad">

<section class="opener">
  <div class="h2"><span class="num">—</span><h2>Start here</h2></div>
  <p class="lede">Each round you play a <b>meld</b> — a small run of cards. The meld
  competes for the trick, and then every card in it becomes something: a settler, a new
  tile, an attack — or a coin. Win the trick and you act first. Come last and you pocket a
  coin.</p>
  <ol class="seq">
    <li><b>Card phase.</b> Everyone plays a meld face down, then all are turned over at
    once. The highest total wins the trick.</li>
    <li><b>Map phase.</b> In trick order, each player spends their meld card by card —
    settling units, exploring new tiles, attacking rivals or cashing cards for gold — and
    takes their free actions: moving, fortifying, and improving their hand.</li>
    <li><b>Grow.</b> Units leave your board a tier at a time. Each tier you empty lets you
    play a bigger meld, research a stronger card and hold a taller wall.</li>
  </ol>
  <p>When someone has placed their last unit, one more round is played and the game
  ends. Most points wins: one per unit
  on the map, plus your <strong>victory row</strong>, plus your two <strong>map
  objectives</strong> &mdash; kinds of place, sung down the generations, that you score by
  holding.</p>
  {fig('table', 'The table, from your seat. The map in the middle is shared and grows all game. Beside it lie the innovation space, where research buys cards, and the face-down market, which only trade reaches. Every meld played stays in the play area until it is spent. Your board holds your reserve of units, your gold and your victory row — and your hand is yours alone.')}

  <div class="contents">
    <span class="tag">Contents</span>
    <p><b>01</b> The idea · <b>02</b> Components · <b>03</b> Setup ·
    <b>✦</b> A worked round · <b>04</b> The round · <b>05</b> Melds ·
    <b>06</b> Spending your meld · <b>07</b> Free actions · <b>08</b> The recycle ·
    <b>09</b> Research and trade · <b>10</b> The victory row · <b>11</b> End of the game ·
    <b>12</b> Map objectives · <b>13</b> Perks ·
    <b>—</b> Glossary · <b>—</b> Quick reference</p>
  </div>
</section>

<section>
  <div class="h2"><span class="num">01</span><h2>The idea</h2></div>
  <p class="lede">In Blink, the cards you play do two jobs at once: they compete for the
  trick, and they are the budget your civilization spends. A pair is two things done; a
  run of four is four. You never choose an action separately from the cards.</p>
  <p>Behind every card sits one plain question: <strong>is it people, or is it gold?</strong>
  Spent on the map, a card settles a unit, opens new ground or strikes a rival — always on
  terrain matching its suit. Cashed, it is a coin, and coins buy walls and better cards.
  Gold is tight, and good players cash cards constantly. The player who reads when a hand
  is people and when it is money — and when to spend a trick rather than win it — comes
  out ahead.</p>
</section>

<section>
  <div class="h2"><span class="num">02</span><h2>Components</h2></div>
  <ul>
    <li><strong>80 civilization cards</strong> — four suits (Plains, Forest, Ocean,
    Mountain), ranks 1–20</li>
    <li><strong>60 terrain tiles</strong> — 15 each of Plains, Forest, Ocean and Mountain</li>
    <li><strong>80 population units</strong> — 20 in each of four player colours</li>
    <li><strong>4 player boards</strong> — each with a <b>reserve</b> of five tiers, a
    <b>gold area</b> and a <b>victory row</b> of five slots</li>
    <li><strong>12 map objective cards</strong> (§12)</li>
    <li><strong>40 gold coins</strong> — if you run out, treat the supply as unlimited</li>
    <li><strong>4 dice</strong> — one <b>winner's die</b> in its own colour and three
    plain <b>initiative dice</b></li>
    <li><em>Perks module only:</em> perk tokens (§13)</li>
  </ul>
</section>

<section>
  <div class="h2"><span class="num">03</span><h2>Setup</h2></div>
  <ol class="seq">
    <li><b>Split the cards.</b> Divide the 80 cards by rank into a
    <strong>starting deck</strong> of ranks <b>1–11</b> (44 cards) and an
    <strong>upgrade deck</strong> of ranks <b>12–20</b> (36 cards), whatever the player
    count.</li>

    <li><b>Draft your hand.</b> Shuffle the starting deck and deal 10 cards to each player.
    <strong>Pass 6 to your left</strong>, then <strong>4</strong>, then <strong>2</strong>,
    each time from the ten cards you are holding — what you kept plus what just arrived. A
    card kept earlier is not locked in; pass it on if something better comes. The ten you
    end with are <strong>your hand for the whole game</strong>. Put the undrafted cards face
    down in the middle: this is the <strong>market</strong> (§09) — 24 cards at two players,
    14 at three, 4 at four.</li>

    <li><b>Take a board.</b> Fill its five tiers with your 20 units — 2, 3, 5, 5, 5 from the
    top. Everyone starts with no gold.</li>

    <li><b>Lay the starting map</b> shown for your player count, then each player places
    one unit from their top tier on the Plains nearest them — their homeland. Every layout follows three rules:
    <strong>one Mountain per player</strong> in a single block in the middle;
    <strong>one Plains per player</strong> around it, each touching exactly one Mountain;
    and <strong>no two starts closer than three tiles</strong>.
    <p class="fine">Cards only act next to your own civilization, so nobody can reach a
    rival's homeland in the opening rounds. The fight for the middle — the Mountains — comes
    first.</p></li>

    <li><b>Tile supply.</b> Sort the remaining tiles into four open piles by terrain,
    face up. Every tile laid during the game comes from here.</li>

    <li><b>Innovation space.</b> Shuffle the upgrade deck face down and deal
    <strong>nine cards face up in a 3 &times; 3 grid</strong> beside it (§09).</li>

    <li><b>Map objectives.</b> Shuffle the twelve objective cards and deal
    <strong>two</strong> to each player. <strong>Show one</strong> face up on your board and
    keep the other hidden (§12). Return the rest to the box unseen.</li>

    <li><b>First player.</b> Choose a start player. They take the <b>winner's die</b>, set
    to 1, and lead the first round.</li>
  </ol>
  {fig('setup_maps', 'The starting layouts for two, three and four players, each with every homeland unit in place.')}
</section>

<section class="example">
  <div class="h2"><span class="num">✦</span><h2>A worked round</h2></div>
  <p>Three players — <strong>Ada</strong>, <strong>Bex</strong> and <strong>Cy</strong> —
  play their first round. Read it for the shape of a turn; every rule used here is set out
  properly in the sections that follow.</p>

  <h3>Setting up</h3>
  <p>They draft their hands of ten; fourteen starting cards are left over and go face down
  as the market. Each loads a board with twenty units and lays the three-player map — three
  Mountains in a triangle, a Plains beyond each outer face — putting one unit on their own
  Plains. The upgrade deck deals nine cards into the innovation space; with a Tribe's rank
  cap of 12, only the 12s there are within reach for now. Each is dealt two map objectives
  and shows one. Ada starts, with the winner's die set to 1.</p>

  <h3>The card phase</h3>
  <p>Everyone's meld limit is <strong>2</strong>. Ada lays first, face down, then Bex, then
  Cy. All anyone sees is the count: two, two, one. Then they turn them over together:</p>
  <ul>
    <li><strong>Ada</strong>: <strong>5 of Plains + 6 of Plains</strong> — a run, total
    <strong>11</strong>.</li>
    <li><strong>Bex</strong>: <strong>8 of Mountain + 8 of Ocean</strong> — one rank twice,
    total <strong>16</strong>. Suits do not matter in a meld.</li>
    <li><strong>Cy</strong>: a single <strong>4 of Mountain</strong>, total
    <strong>4</strong>.</li>
  </ul>
  <p>Nobody has a victory card yet, so nobody declares. <strong>Bex wins the trick</strong>
  with 16 and takes the winner's die, set to <strong>2</strong> — the size of her meld.
  Ada, second, takes the plain die 2; Cy takes 3.</p>
  <p>Because <strong>Ada matched Bex's two cards and lost</strong>, she must set one of
  hers aside. Cy played fewer cards than Bex, so he gives up nothing — and as the
  last-ranked meld he takes <strong>1 gold</strong>.</p>

  {fig('trick', "Round one, the moment after the reveal. Add each row: Bex's 16 beats Ada's 11 and Cy's 4, so Bex takes the trick and the winner's die — set to the size of her meld, two cards. Ada matched that count and lost, so one of her cards will be set aside for a coin.")}

  <h3>The map phase</h3>
  <p>They act in initiative order: Bex, then Ada, then Cy.</p>
  <ul>
    <li><strong>Bex</strong> spends both cards. The Mountain beside her Plains is in reach,
    so her <strong>8 of Mountain</strong> settles a unit there — Mountain holds one, so it is
    hers alone. Her <strong>8 of Ocean</strong> explores: she picks an empty space beside
    her civilization that touches at least two tiles, and lays an Ocean tile from the supply.
    The card is rank 10 or under, so the frontier pays her <strong>1 gold</strong>.</li>
    <li><strong>Ada</strong> sets aside the 5 — it pays her <strong>1 gold</strong> and goes
    to her own discard — and spends the <strong>6 of Plains</strong> to settle a second unit
    on her homeland, which holds three.</li>
    <li><strong>Cy</strong> cashes his 4 for a second gold: nothing on the map is worth
    reaching for yet, and he is saving for research.</li>
  </ul>
  <p>Each card spent also carried one movement — two for Bex, one each for Ada and Cy — but
  everyone's units already stand where they want them, so nobody moves.</p>
  <p>Look at the reserves. Bex and Ada have now each placed both units of their Tribe tier,
  so they are <strong>Settlements</strong>: next round they may play melds of three and
  research up to rank 14. Cy is still a Tribe. Nobody's reserve is empty, so play goes on,
  and <strong>Bex leads the next round</strong>.</p>
  {fig('worked_map', 'The map at the end of round one: three Mountains in a triangle, a Plains beyond each outer face, and the new Ocean. Bex holds a Mountain as well as her homeland; Ada has two units on her Plains; Cy has his starting unit and two coins.')}

  <div class="note">
    <span class="tag">What just happened</span>
    <p>One meld did two jobs for each player: it fought for the trick, then became the
    budget they spent on the map. Bex won initiative and a full turn; Cy's cautious single
    let him bank gold instead. That trade — tempo now against resources later — is the whole
    game in miniature.</p>
  </div>
</section>

<section>
  <div class="h2"><span class="num">04</span><h2>The round</h2></div>
  <p>Every round has two halves. First everyone plays cards; then everyone spends those
  same cards, in the order the cards decided.</p>

  <h3>Your tier</h3>
  <p>Your board holds your 20 units in <strong>five tiers</strong> — 2, 3, 5, 5, 5 — and
  you always take units from the <b>topmost tier that still holds any</b>. That is your
  current tier, and it sets three numbers: the <strong>meld</strong> you may play, the
  highest <strong>rank</strong> you may research, and the <strong>wall</strong> your
  fortifications hold at.</p>
  <table>
    <thead><tr><th>Tier</th><th>Units</th><th>Meld limit</th><th>Rank cap</th><th>Wall</th></tr></thead>
    <tbody>
      <tr><td>Tribe</td><td class="num-cell">2</td><td class="num-cell">2</td><td class="num-cell">12</td><td class="num-cell">10</td></tr>
      <tr><td>Settlement</td><td class="num-cell">3</td><td class="num-cell">3</td><td class="num-cell">14</td><td class="num-cell">12</td></tr>
      <tr><td>Kingdom</td><td class="num-cell">5</td><td class="num-cell">4</td><td class="num-cell">16</td><td class="num-cell">14</td></tr>
      <tr><td>Empire</td><td class="num-cell">5</td><td class="num-cell">5</td><td class="num-cell">18</td><td class="num-cell">16</td></tr>
      <tr><td>Civilization</td><td class="num-cell">5</td><td class="num-cell">6</td><td class="num-cell">20</td><td class="num-cell">18</td></tr>
    </tbody>
  </table>
  <p>Read only the row you are on — <strong>nothing is cumulative</strong>. Empty a tier and
  all three numbers step up together, at once. Growing costs nothing; if units come back to
  your board (§06), the numbers step back down.</p>
  {fig('board', 'The reserve empties from the top tier down. Here Tribe is spent and one Settlement unit placed, so this player reads the Settlement row: melds of three, research up to 14, a wall at 12.')}

  <h3>Card phase</h3>
  <ol class="seq">
    <li><b>Lead.</b> The leader lays a meld from their hand <strong>face down</strong>: one
    card up to their meld limit, forming an unbroken run of ranks (§05).</li>
    <li><b>Follow.</b> Clockwise, every other player lays a meld of their own, face down,
    one card up to their own limit. You may not pass, and nothing has to follow what was
    led. <strong>All anyone sees is how many cards each player laid.</strong></li>
    <li><b>Reveal.</b> When the last meld is down, everyone turns theirs over at once.</li>
    <li><b>Declare.</b> Starting with the leader and going clockwise, each player may spend
    one card from their victory row on its <strong>A</strong> effect (§10), adding its rank
    to their total. You can see every meld and every earlier declaration before you
    decide.</li>
    <li><b>Compare.</b> The <strong>highest total</strong> — the ranks of the meld added
    together, plus any A effect — wins the trick. If totals are equal, the meld with
    <strong>more cards</strong> wins; then a tie-winning A effect; then whoever spent the
    higher victory card on A; then the <strong>highest card</strong>, then the
    second-highest, and so on; and finally the meld laid <strong>earlier</strong>. There is
    never a tie.</li>
    <li><b>Set the dice.</b> The winner takes the <strong>winner's die</strong> and sets it
    to the <strong>number of cards in their meld</strong>. The others take plain dice
    showing <strong>2, 3, 4</strong> in finishing order. This is the initiative order for
    the map phase.</li>
  </ol>
  <div class="note">
    <span class="tag">Why the winner's die shows a card count</span>
    <p>It carries the one number the map phase needs: how many cards the winner played,
    because anyone who matched that count and lost gives a card up. The winner acts first
    because theirs is the winner's die, whatever number it shows.</p>
  </div>

  <h3>Map phase</h3>
  <p>In initiative order, each player takes their whole turn before the next begins:
  spend the cards of your meld (§06) and take your free actions (§07), in any order you
  like.</p>
  <ul>
    <li><strong>Everyone who played exactly as many cards as the winner, and lost, sets one
    card aside.</strong> You choose which. Instead of acting on the map it pays you
    <strong>1 gold</strong>. Everyone else — the winner included — spends every card of
    their meld.</li>
    <li><strong>The player whose meld ranked last takes 1 gold.</strong> Only one player
    takes this coin; if they also set a card aside, they take both.</li>
  </ul>
  <p>Every card you resolve, and the one you set aside, goes face up into your own
  <strong>discard</strong>. None of them is lost: the discard becomes your hand again when
  your hand runs out (§08).</p>
  <p>When everyone has finished, the trick winner leads the next round.</p>
</section>

<section>
  <div class="h2"><span class="num">05</span><h2>Melds</h2></div>
  <div class="note" style="border-left-color:var(--forest)">
    <span class="tag">The meld rule</span>
    <p>A meld is <strong>any cards whose ranks form an unbroken run</strong> — every rank
    from your lowest to your highest must be present. <strong>How many cards you hold of
    each rank does not matter, and suits do not matter at all.</strong> One card is always a
    legal meld.</p>
  </div>

  {fig('meld_rule', 'The whole rule in five rows. Every rank between your lowest and your highest must be present; how many of each you hold does not matter, and suits are irrelevant. Only the last row is illegal, because nothing sits at rank 3.')}

  <p>If you know rummy or poker, set that vocabulary aside: there are no straights, sets or
  full houses, only runs, and duplicates inside a run are free.</p>
  <p>Your <strong>meld limit</strong> is a ceiling, never a quota. A short meld is a real
  line, not a failure: it still reaches the map card for card, and only a player who
  <em>matches</em> the winner's count and loses gives a card up.</p>
</section>

<section>
  <div class="h2"><span class="num">06</span><h2>Spending your meld</h2></div>
  <p>Take the cards of your meld one at a time, <strong>in any order you like</strong>, and
  do <em>one</em> of four things with each: <strong>settle</strong>,
  <strong>explore</strong>, <strong>attack</strong> or <strong>take gold</strong>. Each card
  resolves fully before the next, so a tile you lay with one card can be settled by the
  next.</p>
  <p>Every card except one taken as gold obeys two rules:</p>
  <ol class="seq">
    <li><b>Reach.</b> The card acts on a single cell <strong>next to your
    civilization</strong>: a tile you occupy, or a tile or empty space adjacent to one you
    occupy. Cards of one meld need not act near each other.</li>
    <li><b>Suit matches terrain.</b> A Forest card acts on Forest, an Ocean card on Ocean,
    and so on.</li>
  </ol>

  <p>The four terrains differ in two ways. <b>Holds</b> is how many units a tile can take:
  Plains 3, Forest 2, Ocean 1, Mountain 1. <b>Defence</b> is added to a defender in a fight:
  Plains +0, Ocean +0, Forest +1, Mountain +2. Defended ground is moulded taller, so a glance
  at the map tells you how hard it will fight.</p>
  {fig('terrain', "Everything that differs between the four terrains: how many units the ground holds, and what it adds to a defender. The dashed panel is the one thing only the sea can do — the water advantage, explained in §07.")}

  <div class="note">
    <span class="tag">If you are swept off the map</span>
    <p>Losing your last unit does not end your game. While you have <b>no units on the
    map</b>, your cards ignore the reach rule and may act anywhere on the map. The exemption
    ends the moment one of your units is back on it.</p>
  </div>

  <h3>Settle</h3>
  <p>Put one unit from your reserve on the tile — always from the topmost tier that still
  holds any. You may stack your own units on a tile up to what its terrain holds. Drawing
  down your reserve is how your civilization grows, and how the game ends (§11). With no
  unit left in your reserve, the card takes gold instead.</p>

  <h3>Explore</h3>
  <p>On an <strong>empty space</strong>, lay a tile of the card's suit from the supply
  instead. No unit goes down — settle it with a later card, or leave it as open ground.</p>
  <p><strong>A new tile must touch at least two tiles already on the map.</strong> The map
  grows as one compact body; there are no bridges into open table. If that terrain has run
  out of the supply, the card takes gold instead.</p>
  <p><strong>The frontier pays.</strong> If the card you explored with is <strong>rank 10
  or under</strong>, take <strong>1 gold</strong>. Your weakest cards are worth something
  on the edge of the map, and the tap closes by itself as your hand improves.</p>
  {fig('explore', "Exploring lays new ground beside your civilization. The tile matches the suit of the card and must touch at least two tiles already on the map — and the very next card may settle it. A card of rank 10 or under also pays a coin.")}

  <h3>Attack</h3>
  <p>A tile a rival occupies cannot be settled. Spending a card on it <strong>declares an
  attack</strong> instead, and the attack is a <strong>duel</strong>:</p>
  <ol class="seq">
    <li><b>Attack.</b> Your attack is the rank of the card you spent. You commit nothing
    else.</li>
    <li><b>Defence.</b> The defender may answer with <strong>one card from their
    hand</strong>, of any suit, face up — or decline. Their defence is that card's rank
    <strong>plus the terrain's defence</strong>; a card not committed counts as nothing. If
    the tile is fortified, the higher of the wall and their card defends (§07).</li>
    <li><b>Compare.</b> The higher total wins. A level total goes to <strong>you</strong> —
    unless the defender's card is also of that terrain, in which case they hold. (Your card
    always matches the ground; that is how it got there.)</li>
    <li><b>You win:</b> one defending unit <strong>falls back</strong>. Its owner moves it to
    an adjacent tile they already hold that has room, and chooses if there are several. With
    nowhere to go, the unit goes home to their board, into the <strong>lowest tier with a
    free slot</strong> — which can cost them a tier.
    <br>If that was the <strong>last</strong> unit on the tile, <strong>the ground changes
    hands</strong>: place a unit from your reserve on it and take <strong>1 gold</strong>
    from the supply. With no unit left in your reserve, the tile is simply left empty, and
    pays nothing.
    <br><b>They win:</b> nothing happens. Your card is spent.</li>
  </ol>
  <p>Cards used in the duel go to their owners' discards. Clearing a tile holding several
  units takes one won duel per unit, and the coin comes only with the last.</p>
  {fig('combat', 'Attacking is not moving a unit across the map. The card you spent is the attack; the defender answers from hand, and the ground adds to them. Clear the last defender and the tile is yours — and pays a coin.')}
  <div class="note">
    <span class="tag">Where a retreat can go</span>
    <p>Ocean and Mountain hold one unit each, so a neighbouring one of yours is always full:
    a retreat can only reach <strong>Plains or Forest</strong>. And a unit with nothing of
    yours beside it has nowhere to fall back to at all — a lone outpost goes home.</p>
  </div>
  <div class="note">
    <span class="tag">Your hand does three jobs</span>
    <p>Your cards fight for the trick, pay for your turn — and defend your ground. A hand
    played down to its last cards is a frontier with nobody on the walls, and everyone at
    the table can count your cards.</p>
  </div>

  <h3>Take gold</h3>
  <p>Instead of using a card on the map, take <strong>1 gold</strong>. Any card, any number
  of them — a whole meld can be cashed. It is not a fallback: gold buys walls, research and
  trade.</p>
</section>

<section>
  <div class="h2"><span class="num">07</span><h2>Free actions</h2></div>
  <p>Besides your cards, your map phase offers actions that cost no card. Take them
  whenever you like during your turn, between card plays or after them:</p>
  <ul>
    <li><strong>move</strong> your units, and once a turn take the
    <strong>water advantage</strong>;</li>
    <li><strong>fortify</strong> your units with gold;</li>
    <li><strong>research</strong> or <strong>trade</strong>, up to twice a turn between
    them (§09);</li>
    <li>spend a victory card on its <strong>B</strong> or <strong>C</strong> effect
    (§10).</li>
  </ul>

  <h3>Movement</h3>
  <p><strong>Each card of your meld carries one movement</strong> — including cards cashed
  for gold, but not a card you set aside. Lay three and you may make three moves this turn.
  A movement need not be spent by the card that paid for it. Each move takes one of your
  units:</p>
  <ul>
    <li><strong>By land</strong> — through any chain of tiles you occupy, and onto a tile
    beside it that is empty or yours and has room.</li>
    <li><strong>By sea</strong> — a unit standing on Ocean may sail across
    <strong>unoccupied Ocean</strong>, as far as the open water reaches, to an empty Ocean
    tile.</li>
  </ul>
  <p>Movement is never an attack: you may not move onto or through a rival. You may empty a
  tile by moving its last unit away — an empty tile is nobody's, and your neighbours will
  notice.</p>

  <h3>The water advantage</h3>
  <p><strong>Once per turn</strong>, a unit standing on Ocean may <strong>sail out onto a
  new Ocean tile</strong>. Lay an Ocean tile from the supply on an empty space that touches
  the water the ship could sail through — its own tile, or unoccupied Ocean joined to it —
  and move the unit onto it. This uses one movement and no card. The space must touch at
  least two tiles, like any explore, but it does <strong>not</strong> need to be in your
  reach.</p>
  <p>That is the difference between a voyage and a card: a ship pushes the charted sea
  outward, so a later card can act on ground it could not reach before. It never brings you
  ashore — real Plains, Forest or Mountain still takes a card of that suit.</p>
  <p class="fine">Reaching the water is an ordinary land move, so the advantage usually
  costs two movements: one to put a unit out to sea, one to sail. A single-card meld can
  only take it with a unit already waiting on the water.</p>

  <h3>Fortify</h3>
  <p>Pay <strong>1 gold</strong> and place the coin on one of your units on the map — at
  most <strong>one coin per unit</strong>. The coin stays until a fight spends it or the unit
  is disturbed: moved, or stacked onto by another unit (which strips every coin on that
  tile). A coin on a unit never comes back to your gold.</p>
  <p>A coin on a unit is a <strong>wall</strong>, and a wall fights. When the tile is
  attacked:</p>
  <ul>
    <li>The coin defends at <strong>your tier's wall</strong> (§04) <strong>plus the
    terrain's defence</strong>, and it counts as a card of that terrain.</li>
    <li>It is a <strong>floor, not a substitute</strong>: you may still answer with a card
    from hand, and if that card is higher, it fights instead. If it is not, it stays in your
    hand.</li>
    <li>The attacker still spends <strong>one</strong> card. Beat the wall and the duel is
    won: a defender falls back, and the ground changes hands if that was the last of them.</li>
    <li>The <strong>coin goes to the supply</strong> either way. One coin, one attack made
    much harder.</li>
  </ul>
  <p>The starting deck tops out at 11, so a dealt card can break a Tribe's wall only on
  Plains or Ocean — an 11 against 10 — and never on Forest or Mountain. Every higher wall
  needs a researched card. You cannot fortify in answer to an attack, because attacks come
  on someone else's turn: a wall is a read on your neighbours, paid for in advance.</p>
  {fig('fortify', "A wall does not save the unit — it raises the rank needed to come for it. The coin holds at your tier's number, your own card fights instead if it is higher, and the coin is spent either way.")}
</section>

<section id="recycle">
  <div class="h2"><span class="num">08</span><h2>The recycle</h2></div>
  <p>Your hand is <strong>ten cards</strong>, and nothing you play ever leaves you: every
  card goes to your own discard. When your hand is empty <strong>and</strong> every card of
  your meld has been resolved, your hand <b>recycles</b> — at once, in the middle of your
  turn:</p>
  <ol class="seq">
    <li><strong>Collect your income:</strong> 1 gold for each of your map objectives, shown
    or hidden, whose pattern you hold right now (§12).</li>
    <li><strong>Arm a perk</strong>, if you are playing with perks (§13).</li>
    <li><strong>Pick up your whole discard</strong> as your new hand — ten cards — and carry
    on with your turn. You never draw cards to refill.</li>
  </ol>
  {fig('recycle', 'The recycle, in order: income first, then the perk (a module), and the hand comes back last. Your map phase — moves, walls, research — is still in front of you.')}
  <p>If you spend your last card defending on someone else's turn, you recycle as soon as
  your own meld is resolved — or at the end of the round, if your turn has already
  passed.</p>
  <p>Only research and trade ever change which ten cards you hold (§09). A hand drifts
  because you paid to make it drift, never because the deal moved underneath you.</p>
</section>

<section>
  <div class="h2"><span class="num">09</span><h2>Research and trade</h2></div>
  <p>Two piles of cards sit beside the map:</p>
  <ul>
    <li>the <strong>innovation space</strong> — nine face-up cards from the upgrade deck in
    a 3 &times; 3 grid. <strong>Research</strong> reaches into it.</li>
    <li>the <strong>market</strong> — the face-down pile that began as the undrafted cards.
    <strong>Trade</strong> reaches into it.</li>
  </ul>
  <p><strong>Up to twice per turn</strong>, during your map phase, you may improve your
  hand: research twice, trade twice, or one of each. The <strong>first improvement of a turn
  costs 1 gold, the second costs 2</strong>, whichever kind it is.</p>

  <h3>Research</h3>
  <ol class="seq">
    <li><b>Draw the top card</b> of the upgrade deck and place it face up on the grid
    position showing the <b>highest rank</b>, covering it (if tied, the first in reading
    order). Nobody chooses; a covered card is out of reach until the one on top of it is
    taken.</li>
    <li><b>Retire the lowest-ranked card in your hand</b> to your <strong>victory
    row</strong> (§10). If you hold several of that rank, choose which suit. With no card
    in hand you cannot research.</li>
    <li><b>Pay</b> — 1 gold, or 2 for your second improvement this turn — and
    <b>take any visible card at or below your rank cap</b> (§04). Put it into your
    <strong>hand</strong>, to use this cycle, or your <strong>discard</strong>, so your hand
    runs out and recycles sooner.</li>
    <li><b>Refill</b> any empty grid positions from the deck. Once the deck is empty,
    positions stay empty.</li>
  </ol>
  {fig('market', 'The innovation space. Each draw covers the highest rank showing, so the tallest idea is always the one buried next. A player with a rank cap of 16 may buy any visible card up to 16; the taller ones are in view but out of reach until they grow.')}
  <div class="note">
    <span class="tag">When there is nothing you may take</span>
    <p>Draw first, then look. If nothing on the grid is at or below your rank cap, the
    research ends: the drawn card stays, and you retire nothing and pay nothing. It still
    counts as <strong>one of your two</strong> improvements — the deck has moved — but
    because you bought nothing, your next one this turn still costs 1.</p>
  </div>
  <p>The rank cap only limits what you <em>take</em>. A card you already hold is yours to
  use whatever your tier. And because research always retires your <em>lowest</em> card,
  your victory row is a record of what your civilization outgrew: 3s and 4s early on,
  perhaps a 12 by the end.</p>

  <h3>Trade</h3>
  <p>Where research reaches <strong>up</strong> — a stronger card, paid for by retiring
  your weakest — trade reaches <strong>sideways</strong>: two cards for two, no rank gained
  and nothing retired.</p>
  <ol class="seq">
    <li><b>Draw the top two cards</b> of the market into your hand, blind. There must be at
    least two.</li>
    <li><b>Pay</b> — 1 gold, or 2 for your second improvement this turn.</li>
    <li><b>Bury any two cards</b> from your hand — the two you drew, two you already held,
    or one of each — face down at the <strong>bottom of the market</strong>. Your hand is
    back to its size.</li>
  </ol>
  <p>The draw commits you: once you have seen the two cards, you must bury exactly two. The
  market is never shuffled after setup, so what you bury comes back up in its own time, in
  somebody's trade.</p>
</section>

<section>
  <div class="h2"><span class="num">10</span><h2>The victory row</h2></div>
  <p>Every card you retire by research goes to your <strong>victory row</strong>: five
  slots on your board, filled from the right. A card there does two jobs. It
  <strong>scores</strong> at the end of the game (§11), and until then it can be
  <strong>spent once</strong> on one of three printed effects.</p>
  <p>The row holds at most <strong>five cards</strong>. Retire a sixth and the lowest of the
  six goes to the bottom of the market — even if that is the card you just retired. A full
  row never stops you researching.</p>

  <h3>Spending a victory card</h3>
  <p>Every card prints three effects, growing with its rank. Spend a card on
  <strong>one</strong> of them, then put it at the bottom of the market: your row shrinks,
  and your score with it.</p>
  <table>
    <thead><tr><th>Rank</th><th>A · after the reveal</th><th>B · your map phase</th><th>C · your map phase</th></tr></thead>
    <tbody>
      <tr><td>1–5</td><td>Add this card's <b>rank</b> to your total</td><td><b>Found a colony</b> — 1 new tile of this suit, 1 unit on it, fortified</td><td><b>2</b> gold</td></tr>
      <tr><td>6–10</td><td>Add its <b>rank</b>, and <b>win ties</b></td><td><b>Found a distant colony</b> — as above, up to 2 tiles out</td><td><b>3</b> gold</td></tr>
      <tr><td>11–15</td><td>Add this card's <b>rank</b> to your total</td><td><b>Open a frontier</b> — 2 new tiles of this suit, 1 unit on one of them, fortified</td><td><b>4</b> gold</td></tr>
      <tr><td>16–20</td><td>Add its <b>rank</b>, and <b>win ties</b></td><td><b>Two colonies</b> — 2 new tiles of any terrain, 1 unit on each, both fortified</td><td><b>5</b> gold</td></tr>
    </tbody>
  </table>
  <ul>
    <li><strong>A</strong> is declared in the card phase, after the reveal (§04). It counts
    only toward winning the trick, never toward what you spend on the map. "Win ties" places
    you ahead of an equal total with the same number of cards (§04).</li>
    <li><strong>B</strong> is used in your own map phase. Lay the new tile or tiles from the
    supply, settle a unit from your reserve on each one the card provides for, and fortify
    each of those units with a coin <strong>from the general supply</strong>. Each tile is an
    explore: it must touch two tiles and lie <strong>within your reach</strong> — or, for the
    6–10 band, <strong>up to two tiles out</strong>. You need at least one unit in your
    reserve and a tile of the right terrain in the supply; lay what you can. A colony does
    not pay the frontier coin.</li>
    <li><strong>C</strong> is taken in your own map phase, at any point in it.</li>
  </ul>
  <div class="note" style="border-left-color:var(--forest)">
    <span class="tag">One effect per round</span>
    <p>A, B and C share <strong>one allowance per round</strong>: at most one victory card
    leaves your row each round, whichever effect it pays for. Declare A and you may not also
    found a colony or cash a card this round, and so on.</p>
  </div>
  <div class="note">
    <span class="tag">One row, three appetites</span>
    <p>The same five slots are your <em>score</em>, your <em>war chest</em> and your
    <em>trick insurance</em>. High cards score best — and their effects are also the
    strongest, so the card you most want to keep is the card you most want to spend.</p>
  </div>
</section>

<section>
  <div class="h2"><span class="num">11</span><h2>End of the game</h2></div>
  <p>One trigger, and you can see it coming from across the table: if, at the end of a
  round, any player's reserve is <strong>empty</strong> — all twenty units on the map —
  play <strong>one more full round</strong>. Then score.</p>
  <table>
    <thead><tr><th>Score</th><th></th></tr></thead>
    <tbody>
      <tr><td><strong>Population</strong></td><td>1 point per unit you have on the map.</td></tr>
      <tr><td><strong>Victory row</strong></td><td><strong>1 point per card</strong> in the row. <em>In addition</em>, lay the cards out in rank order <strong>pushed to the right</strong> of the five slots: if you hold three or more, also score the <strong>rank in the centre slot</strong>.</td></tr>
      <tr><td><strong>Map objectives</strong></td><td><strong>2 points for each arrangement</strong> you hold of each of your two objectives, shown and hidden (§12).</td></tr>
    </tbody>
  </table>
  {fig('vprow', 'The empty slots sit on the left, so the centre slot only reaches your true middle card once all five are filled. A half-full row scores a lower card — and slipping a low card in can push your centre down.')}
  <table>
    <thead><tr><th>Your victory row</th><th>Laid out in five slots</th><th>Scores</th></tr></thead>
    <tbody>
      <tr><td>2 cards — 9, 17</td><td>· · · 9 17</td><td class="num-cell">2</td></tr>
      <tr><td>3 cards — 6, 9, 17</td><td>· · <b>6</b> 9 17</td><td class="num-cell">3 + 6 = <b>9</b></td></tr>
      <tr><td>4 cards — 6, 9, 14, 17</td><td>· 6 <b>9</b> 14 17</td><td class="num-cell">4 + 9 = <b>13</b></td></tr>
      <tr><td>5 cards — 6, 9, 14, 16, 17</td><td>6 9 <b>14</b> 16 17</td><td class="num-cell">5 + 14 = <b>19</b></td></tr>
    </tbody>
  </table>
  <p>With fewer than three cards the row pays only its point per card; the third card is
  where it starts paying properly, and the fifth is where it pays best.</p>
  <p>Most points wins. If tied, the tied player with more gold wins; if still tied, share
  the victory.</p>
  <div class="note">
    <span class="tag">For a first game</span>
    <p><strong>Map objectives</strong> (§12) are part of the base game, but you may leave
    them out of a first game — the rest stands without them. <strong>Perks</strong> (§13)
    are an optional module and do not belong in a first game at all.</p>
  </div>
</section>

<section id="objectives">
  <div class="h2"><span class="num">12</span><h2>Map objectives</h2></div>
  <p class="lede">The only points in the game about the <em>shape</em> of what you hold
  rather than its size.</p>

  <p>Each objective card names <strong>three tiles</strong>: a <b>middle</b> of one terrain,
  and two <b>ends</b> that each touch the middle. The ends need not touch each other, so a
  bend counts exactly as a straight line does.</p>
  <ul>
    <li>All three must be tiles <strong>you occupy</strong> — at least one of your units on
    each. An empty tile, or one held by a rival, never counts.</li>
    <li>The terrains must match exactly. <em>Fjord</em> is Ocean between two Mountains;
    two Oceans around a Mountain is <em>Mountain Lookout</em>, a different card.</li>
    <li>An objective scores <strong>2 points for each arrangement</strong> you hold at the
    end: count each tile of the middle terrain that has both its ends beside it. A tile may
    serve as an end for more than one arrangement, but each middle pays once. Holding none
    costs nothing.</li>
    <li>While you hold it, an objective also pays <strong>1 gold at each recycle</strong>
    (§08) — one coin per objective, however many arrangements.</li>
  </ul>
  <p>There are twelve objective cards. You are dealt two <em>after</em> the starting map is laid, so they reward where you go,
  not where you began. <strong>Show one and keep one.</strong> Showing tells the table what
  you are building — and which single tile would break it.</p>

  <div class="note">
    <span class="tag">At the table</span>
    <p>Hold your <strong>hidden</strong> card with your hand of cards — it is not one of
    your ten — so you can check it after every tile you place. Keep your
    <strong>shown</strong> card face up on your board, where everyone can read it without
    asking.</p>
  </div>

  <h3>Other ways to play it</h3>
  <p>Show one is the printed game. Agree on another before setup if your table prefers.</p>
  <table>
    <thead><tr><th>Mode</th><th>Setup</th><th>Character</th></tr></thead>
    <tbody>
      <tr><td><strong>Secret</strong></td>
        <td>Deal <b>two</b> to each player before the draft. Keep <b>one</b>, hidden; return
        the other unseen.</td>
        <td>The tightest. Nobody knows what anyone is building.</td></tr>
      <tr><td><strong>Open</strong></td>
        <td>Turn <b>two</b> face up in the middle. They belong to everyone.</td>
        <td>The most contested — everyone wants the same shapes.</td></tr>
      <tr><td><strong>Keep both</strong></td>
        <td>Deal <b>two</b> to each player and keep both hidden.</td>
        <td>The loosest: two shapes to steer between and nothing declared.</td></tr>
    </tbody>
  </table>
  <p>In every mode, hidden objectives are revealed together at the end, after the rest of
  the score is counted.</p>

  <div class="note">
    <span class="tag">Why it changes the map</span>
    <p>Without objectives, ground is ground. With them, a particular empty space beside your
    Forest is suddenly worth exploring <em>specifically</em>. They are worth steering toward
    when the map offers them — but many players end with none, so they are never worth
    wrecking your position over.</p>
  </div>
</section>

<section id="perks">
  <div class="h2"><span class="num">13</span><h2>Perks</h2></div>
  <p class="lede">An optional module. Everything in sections 01 to 12 still applies.</p>

  <p>Perks give the slots of your victory row a job of their own. <strong>Exactly one perk runs at a time</strong>, and you choose which at every
  recycle (§08), from the perks your row is deep enough to reach <em>at that moment</em>. A
  deep row does not run four perks — it chooses from four. No perk runs before your first
  recycle.</p>
  <p>Once armed, a perk <strong>keeps running until your next recycle</strong>, even if you
  spend the card that unlocked it. Spending a victory card costs you nothing now; it shows
  up at the next recycle, as a shorter menu.</p>

  <h3>Setup</h3>
  <ol class="seq">
    <li>Shuffle the perk tokens and <b>deal four to each player</b>.</li>
    <li>Put one on each of <strong>slots 1, 2, 3 and 4</strong> of your victory row, face
    up, in any order. <strong>Slot 5 stays empty</strong>: it fills on your first research,
    so a perk there would be a gift.</li>
    <li>You may rearrange them until your first card reaches the row. After that the
    arrangement is <strong>permanent</strong>.</li>
  </ol>

  <h3>Which slot</h3>
  <p>The row fills from the <strong>right</strong>, so the slot decides how long you
  wait:</p>
  <table>
    <thead><tr><th>Slot</th><th>Reachable when your row holds</th><th>The bet</th></tr></thead>
    <tbody>
      <tr><td class="num-cell">4</td><td class="num-cell">2 cards</td>
        <td>Working almost at once. The safe place for the perk you want most.</td></tr>
      <tr><td class="num-cell">3</td><td class="num-cell">3 cards</td>
        <td>Reachable in most games.</td></tr>
      <tr><td class="num-cell">2</td><td class="num-cell">4 cards</td>
        <td>Late, and only if you keep researching.</td></tr>
      <tr><td class="num-cell">1</td><td class="num-cell">all 5</td>
        <td>A long shot: fill the row and never spend it down.</td></tr>
    </tbody>
  </table>
  <p>Every perk is equal in strength; what differs is how soon you want each one, and how
  much of your row you will tie up to reach it.</p>

  <h3>The two kinds</h3>
  <ul>
    <li><strong>SPEND</strong> — use it once, then turn the token face down. It turns face
    up again at your next recycle.</li>
    <li><strong>STANDING</strong> — it simply works for as long as it is armed. These tokens
    never turn over.</li>
  </ul>
  <p>Each token says which kind it is.</p>
  <div class="note">
    <span class="tag">The price of a perk</span>
    <p>Every victory card you spend on A, B or C is a slot your row may no longer reach at
    the next recycle. The more you value your perks, the fewer effects you will spend — a
    player who wants everything running has quietly given up their war chest.</p>
  </div>
</section>

</main>

<div class="ref">
<div class="pad">
<section>
  <div class="h2"><span class="num">—</span><h2>Glossary</h2></div>
  <dl class="gloss">
    <dt>Meld</dt><dd>The cards you play in one round — one up to your meld limit, forming an
    unbroken run of ranks. It competes for the trick, then each card is spent (§05).</dd>
    <dt>Cell</dt><dd>The single hex a card acts on — a tile of the card's suit, or an empty
    space where a tile of that suit will go — in your reach.</dd>
    <dt>Reach</dt><dd>Any tile you occupy, or any tile or empty space adjacent to one you
    occupy (§06).</dd>
    <dt>Civilization</dt><dd>All your units on the map, and the tiles they stand on.</dd>
    <dt>Tier</dt><dd>One of the five rows of your reserve — Tribe, Settlement, Kingdom,
    Empire, Civilization. Your <em>current tier</em> is the topmost one still holding units;
    it sets your meld limit, rank cap and wall (§04).</dd>
    <dt>Set aside</dt><dd>The card you give up for matching the winner's card count and
    losing. It pays 1 gold instead of acting, and goes to your own discard (§04).</dd>
    <dt>Movement</dt><dd>One per card of your meld, except a card set aside. By land through
    your own tiles, or by sea across open Ocean. Never an attack (§07).</dd>
    <dt>Wall</dt><dd>A fortification coin on a unit. It defends at your tier's wall plus the
    terrain, and is spent by the next attack (§07).</dd>
    <dt>Recycle</dt><dd>When your hand is empty and your meld spent: collect income, arm a
    perk if playing with them, and pick up your discard as your new hand of ten (§08).</dd>
    <dt>Innovation space</dt><dd>The nine face-up upgrade cards in a 3 &times; 3 grid.
    Research takes from it, up to your rank cap (§09).</dd>
    <dt>Market</dt><dd>The face-down pile: the undrafted cards, plus spent and bumped victory cards and cards buried by trade. Only trade
    draws from it, and it is never shuffled after setup (§09).</dd>
    <dt>Victory row</dt><dd>The five slots holding your retired cards. They score at the
    end, or can each be spent once on an effect (§10).</dd>
  </dl>
</section>

<section id="quickref">
  <div class="h2"><span class="num">—</span><h2>Quick reference</h2></div>
  <div class="cols">
    <div>
      <h3>Tiers</h3>
      <p>Units in tiers of 2 / 3 / 5 / 5 / 5, taken from the top. Meld, rank cap, wall:
      <b>Tribe</b> 2, 12, 10 · <b>Settlement</b> 3, 14, 12 · <b>Kingdom</b> 4, 16, 14 ·
      <b>Empire</b> 5, 18, 16 · <b>Civilization</b> 6, 20, 18. Read your current tier only.</p>
      <h3>Card phase</h3>
      <p>Leader lays a meld face down → others follow clockwise, face down → reveal
      together → declare A effects, leader first → highest total wins; ties: more cards,
      then tie-winning A, then higher A card, then highest card down, then earliest laid →
      <b>winner's die = their meld size</b>, others 2 / 3 / 4.</p>
      <h3>Melds</h3>
      <p>An <b>unbroken run</b> of ranks; duplicates free, suits irrelevant, one card always
      legal. 2 ✓ · 2-2 ✓ · 2-3 ✓ · 2-3-3-4-4 ✓ · <b>2-2-4-4 ✗</b></p>
      <h3>Map phase</h3>
      <p>In initiative order. Anyone who played <b>exactly</b> the winner's card count and
      lost sets one card aside for 1 gold; everyone else spends every card. Last-ranked meld
      takes 1 gold.</p>
      <h3>Each card of your meld</h3>
      <p>ONE of: <b>settle</b> a unit · <b>explore</b> a tile · <b>attack</b> · take
      <b>1 gold</b>. In your reach, suit matches terrain. No units on the map? Reach does not
      apply.</p>
      <h3>Explore</h3>
      <p>New tile touches <b>at least two</b> tiles. Terrain run out → gold instead.
      Rank 10 or under → +1 gold.</p>
      <h3>Duel</h3>
      <p>Attack = your card's rank. Defence = their card from hand (or their wall) + terrain
      (Plains 0 · Ocean 0 · Forest 1 · Mountain 2). Higher wins; level goes to you unless
      their card also matches the ground. Win: one defender falls back (or goes home). Last
      one gone: place your unit, +1 gold.</p>
    </div>
    <div>
      <h3>Terrain</h3>
      <p>Plains 3 · Forest 2 (defends +1) · Ocean 1 · Mountain 1 (defends +2)</p>
      <h3>Free actions</h3>
      <p><b>Move</b>: one per meld card (not the set-aside card); by land through your
      tiles, by sea across open Ocean. · <b>Water advantage</b>, once a turn: a unit on Ocean
      sails onto a new Ocean tile laid on its coast; touch-two applies, reach does not. ·
      <b>Fortify</b>: 1 gold onto a unit, one per unit; wall 10 / 12 / 14 / 16 / 18 +
      terrain; spent by the next attack. · <b>Research or trade</b>: up to two a turn,
      1 gold then 2. · Victory effects <b>B</b>, <b>C</b>.</p>
      <h3>Research</h3>
      <p>Draw onto the highest rank showing → retire your <b>lowest</b> hand card to your
      victory row → pay → take any visible card <b>at or below your rank cap</b>
      (12/14/16/18/20), to hand or discard → refill. Nothing to take: stop, pay nothing, still counts.</p>
      <h3>Trade</h3>
      <p>Draw the market's top two → pay → bury any two hand cards at its bottom.</p>
      <h3>Recycle</h3>
      <p>Hand empty and meld spent, at once: income (1 gold per objective you hold) → arm a
      perk → pick up your discard. Ten cards; no drawing.</p>
      <h3>Victory row — one effect per round</h3>
      <p><b>A</b> add its rank to your total (6–10 and 16–20 also win ties) ·
      <b>B</b> found a colony: tiles, units and walls from the supply · <b>C</b> 2 / 3 / 4 /
      5 gold. A after the reveal; B and C in your map phase. Spent cards go to the bottom of
      the market. A sixth card bumps the lowest there.</p>
      <h3>Gold in</h3>
      <p>1 each: cash a card · explore with rank 10 or under · last-ranked meld · set-aside
      card · take the ground in a duel. Also: 1 per objective held, at each recycle ·
      effect C.</p>
      <h3>End and scoring</h3>
      <p>Any reserve empty at the end of a round → one more round. Score 1 per unit on the map + 1 per
      victory card + the centre-slot rank (three or more cards) + 2 per objective arrangement.
      Ties: most gold.</p>
    </div>
  </div>
</section>
</div>
</div>

<div class="pad"><footer>Blink · base game · draft rules {VTAG} · Toby Siko ·
deep-diversions.com/blink · @tobysiko.bsky.social · the disasters and events expansion is
published separately</footer></div>

</div>
</body>
</html>
"""

# ONLY WHEN RUN, NEVER WHEN IMPORTED.
#
# check_figs.py does `from build_html import SCALE, COMPARE`, and until this
# guard existed that import EXECUTED this line — writing a complete rulebook
# into whatever directory the checker happened to be run from. Run the checks
# from the project root and you got Blink-rules-v0.26.html one level above the
# real one, byte-identical on the day and stale by morning.
#
# That is this project's oldest and most expensive bug: figs.json,
# Blink-rules-v0.24.html and game-description.html all lived in two places at
# once, measurements were taken from the wrong copy, and a PDF shipped from a
# file five days old. The note above about the write being "left alone on
# purpose" was the wrong call — a module that writes a file as a side effect of
# being imported manufactures the decoy.
#
# The path is still relative, so `python3 build_html.py` from source/ behaves
# exactly as it always has and build_pdfs.sh is unaffected.
if __name__ == "__main__":
    # BESIDE THIS SCRIPT. It used to be "./" + RULES_HTML, which is relative to
    # the directory the builder was RUN from, so `python3 source/build_html.py`
    # from the repo root wrote a second rulebook at the root and left the one
    # in source/ - the copy check_rules.py reads - untouched. The rebuild
    # printed a filename and a byte count and looked entirely successful.
    # Resolving from __file__ gives the identical path when run from source/,
    # so build_pdfs.sh is unaffected; it just no longer depends on the cwd.
    out = pathlib.Path(__file__).resolve().parent / RULES_HTML
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(HTML, encoding="utf-8")
    print("wrote", out, len(HTML), "bytes")
