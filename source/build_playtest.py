# -*- coding: utf-8 -*-
"""Blink v0.21 playtest sheet — one A4 page, filled in at the table.

Deliberately NOT a general feedback form (there is one of those already). This
sheet asks only the questions the v0.21 redesign left open and the simulator
could not answer:

  1. free moves      the sim could not validate the allowance at all
  2. meld shape      shapes no longer reach the map; do they still feel worth
                     building?
  3. trick reward    winner +1 card, last place +1 gold — NEW in v0.21,
                     never played; plus the voluntary cashing rate
  4. end trigger     the sim says the market clock always fires first
  5. food            reallocation is new and untested

Reuses the rulebook CSS so it looks like the rest of the set.
"""
import pathlib
from version import VTAG
from build_html import CSS

EXTRA = """
@page{size:A4;margin:12mm 12mm 10mm 12mm}
body{font-size:9.1pt;line-height:1.3}
.sheet{max-width:none;box-shadow:none;background:#fff}
.pad{padding:0}
h1{font-family:Fraunces,Georgia,serif;font-size:19pt;margin:0;letter-spacing:-.02em;white-space:nowrap}
.sub{font-family:"IBM Plex Mono",monospace;font-size:7.6pt;letter-spacing:.12em;
  text-transform:uppercase;color:#8A837A;margin:.2rem 0 0}
.top{display:flex;justify-content:space-between;align-items:flex-end;gap:1rem;
  border-bottom:2px solid #1C1F1D;padding-bottom:.3rem;margin-bottom:.5rem}
.q{break-inside:avoid;margin:0 0 .38rem;padding-left:1.5rem;position:relative}
.q .n{position:absolute;left:0;top:.05rem;font-family:"IBM Plex Mono",monospace;
  font-size:.66rem;border:1.2px solid #1C1F1D;border-radius:50%;
  width:1.15rem;height:1.15rem;display:flex;align-items:center;justify-content:center}
.q h3{font-family:"IBM Plex Sans",sans-serif;font-size:9.6pt;font-weight:600;
  margin:0 0 .1rem}
.q p{margin:0 0 .18rem;font-size:8.7pt;color:#5A5F59;max-width:none}
.rule-line{border-bottom:1px dotted #B4AFA3;height:.78rem}
.rule-line.tall{height:1.5rem}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:.4rem 1.6rem}
.box{border:1px solid #CDC7B8;border-radius:3px;padding:.35rem .5rem;
  background:#FBFAF6}
.tally{font-family:"IBM Plex Mono",monospace;font-size:8pt;color:#8A837A}
.scale{font-family:"IBM Plex Mono",monospace;font-size:8.4pt;letter-spacing:.08em}
.setup{font-size:8.4pt;color:#5A5F59;border:1px solid #CDC7B8;border-radius:3px;
  padding:.35rem .55rem;background:#F6F4ED;margin-bottom:.55rem}
.foot{border-top:1px solid #CDC7B8;margin-top:.5rem;padding-top:.3rem;
  font-family:"IBM Plex Mono",monospace;font-size:7.2pt;color:#8A837A}
table.tick{width:100%;font-size:8.4pt;margin:.15rem 0 .1rem}
table.tick td{border-bottom:1px dotted #B4AFA3;padding:.2rem .3rem .2rem 0}
table.tick td.k{width:38%;color:#5A5F59}
"""


def q(n, title, prompt, body):
    return (f'<div class="q"><span class="n">{n}</span><h3>{title}</h3>'
            f'<p>{prompt}</p>{body}</div>')


LINES = lambda k=2, tall=False: "".join(
    f'<div class="rule-line{" tall" if tall else ""}"></div>' for _ in range(k))

HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Blink {VTAG} — playtest sheet</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}{EXTRA}</style>
</head>
<body>
<div class="sheet"><div class="pad">

<div class="top">
  <div>
    <h1>Blink — playtest sheet</h1>
    <p class="sub">rules {VTAG} · one sheet per game</p>
  </div>
  <div class="tally" style="text-align:right;line-height:1.7">
    players ____ &nbsp; date __________<br>
    start ______ &nbsp; end ______</div>
</div>

<div class="setup">
  <b>Play the base game only.</b> No objectives module, no expansions — those are
  not tuned for these rules. The five questions below are the ones the design is
  actually stuck on; everything else can wait for the feedback form.
</div>

{q(1, "Free moves — the big unknown",
   "Each turn your band gives you 1–4 free moves (land across your own units, or sea). "
   "Tick roughly how many you actually used, and say what for.",
   '<table class="tick">'
   '<tr><td class="k">moves used per turn, typically</td>'
   '<td class="scale">none &nbsp; 1 &nbsp; 2 &nbsp; 3 &nbsp; 4 &nbsp; wanted more</td></tr>'
   '<tr><td class="k">mostly used to…</td>'
   '<td class="scale">reinforce &nbsp; escape &nbsp; claim ground &nbsp; didn&rsquo;t bother</td></tr>'
   '<tr><td class="k">did anyone forget they had them?</td>'
   '<td class="scale">yes &nbsp; no</td></tr></table>'
   + LINES(1))}

{q(2, "Did the shape of a meld ever matter?",
   "Melds now only decide how many cards you spend. Straight of four and quadruple "
   "do the same work. Did anyone care which they held — and did anyone build toward "
   "a bigger meld on purpose?",
   '<table class="tick">'
   '<tr><td class="k">shape felt…</td>'
   '<td class="scale">irrelevant &nbsp; mildly &nbsp; still interesting</td></tr>'
   '<tr><td class="k">anyone hold cards to build a big meld?</td>'
   '<td class="scale">yes &nbsp; no</td></tr></table>'
   + LINES(1))}

{q(3, "The new trick reward — and how often you cashed",
   "Winner spends one extra card; the meld that ranked last takes 1 gold. Tally one mark "
   "per card <b>you</b> cashed instead of using on the map (the sim predicts about one "
   "in three). Count for yourself only.",
   '<div class="box" style="height:1.7rem"></div>'
   '<p style="margin-top:.2rem">cards cashed ______ of ______ played &nbsp;·&nbsp; '
   'did cashing ever feel like the <i>obvious</i> choice, with no decision in it? '
   'yes / no</p>'
   '<table class="tick">'
   '<tr><td class="k">did anyone ask how many cards they could use?</td>'
   '<td class="scale">yes &nbsp; no &nbsp; (the rule exists to stop that)</td></tr>'
   '<tr><td class="k">the winner&rsquo;s extra card felt…</td>'
   '<td class="scale">a real prize &nbsp; barely noticed &nbsp; too strong</td></tr>'
   '<tr><td class="k">the last-place coin felt…</td>'
   '<td class="scale">welcome &nbsp; pointless &nbsp; like charity</td></tr></table>')}

{q(4, "What ended the game, and did it land?",
   "The simulator says a suit's advanced deck always runs dry before anyone places "
   "a twentieth unit. If that happened, did the ending feel earned or abrupt?",
   '<table class="tick">'
   '<tr><td class="k">ended because…</td>'
   '<td class="scale">a suit ran out &nbsp; someone placed 20 units</td></tr>'
   '<tr><td class="k">the ending felt…</td>'
   '<td class="scale">earned &nbsp; abrupt &nbsp; nobody noticed it coming</td></tr>'
   '</table>' + LINES(1))}

{q(5, "Food and the coin shuffle",
   "Coins sit on your band's food slots and your people eat them at each recycle; "
   "you may move coins between reserve, food and fortifications freely on your turn.",
   '<table class="tick">'
   '<tr><td class="k">did anyone starve (return units)?</td>'
   '<td class="scale">yes, ___ times &nbsp; never</td></tr>'
   '<tr><td class="k">pre-placing food on the slots was…</td>'
   '<td class="scale">clear &nbsp; fiddly &nbsp; forgotten &nbsp; pointless</td></tr>'
   '<tr><td class="k">anyone pull coins off a fortification to eat?</td>'
   '<td class="scale">yes &nbsp; no</td></tr></table>')}

<div class="grid2">
  <div>
    <h3 style="font-family:'IBM Plex Sans';font-size:9.6pt;margin:.2rem 0 .1rem">
    Anything you had to look up, argue about, or invent</h3>
    {LINES(3)}
  </div>
  <div>
    <h3 style="font-family:'IBM Plex Sans';font-size:9.6pt;margin:.2rem 0 .1rem">
    Best and worst moment</h3>
    {LINES(3)}
  </div>
</div>

<p style="margin:.45rem 0 .1rem;font-size:8.7pt"><b>Scores</b> — seat / total /
population / victory row / dominance / gold left</p>
{LINES(3, tall=True)}

<p class="scale" style="margin:.35rem 0 0">
would play again &nbsp; 1 &nbsp; 2 &nbsp; 3 &nbsp; 4 &nbsp; 5 &nbsp;&nbsp;·&nbsp;&nbsp;
rules were clear &nbsp; 1 &nbsp; 2 &nbsp; 3 &nbsp; 4 &nbsp; 5</p>

<div class="foot">Blink · {VTAG} · playtest sheet · Toby Siko ·
the longer feedback form covers everything this page does not</div>

</div></div>
</body>
</html>
"""

out = pathlib.Path("./Blink-playtest-sheet.html")
out.write_text(HTML, encoding="utf-8")
print("wrote", out, len(HTML), "bytes")
