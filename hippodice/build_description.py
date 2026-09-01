import re, sys
fig = open('figs/0.svg', encoding='utf-8').read()
HERO_MM = sys.argv[1] if len(sys.argv) > 1 else "150"
FS      = sys.argv[2] if len(sys.argv) > 2 else "9.2"

HTML = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Blink — game description</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400..600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--paper:#EDEAE1;--page:#FBFAF6;--ink:#1C1F1D;--ink-soft:#5A5F59;
 --plains:#C9992B;--forest:#37704A;--ocean:#256A8C;--stone:#8A837A;--red:#C0392B;--rule:#CDC7B8;}}
@page{{size:A4;margin:0}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0}}
body{{width:210mm;height:297mm;background:var(--page);color:var(--ink);
 font-family:"IBM Plex Sans",-apple-system,sans-serif;font-size:{FS}pt;line-height:1.42;
 padding:12mm 13mm 9mm;display:flex;flex-direction:column}}
.fig-label{{font-family:"IBM Plex Sans",sans-serif;fill:#5A5F59}}
.fig-strong{{font-family:"IBM Plex Sans",sans-serif;fill:#1C1F1D;font-weight:600}}
.fig-step{{font-family:"IBM Plex Mono",monospace;fill:#8A837A;letter-spacing:.06em}}
.fig-rank{{font-family:Fraunces,Georgia,serif;fill:#1C1F1D;font-weight:600}}
.fig-attack{{font-family:"IBM Plex Sans",sans-serif;fill:#C0392B;font-weight:600}}
header{{display:flex;justify-content:space-between;align-items:flex-end;gap:8mm;
 border-bottom:1.5px solid var(--ink);padding-bottom:2.5mm}}
.eyebrow{{font-family:"IBM Plex Mono",monospace;font-size:6.6pt;letter-spacing:.18em;
 text-transform:uppercase;color:var(--ink-soft);margin:0 0 1mm}}
h1{{font-family:Fraunces,Georgia,serif;font-size:33pt;line-height:.9;margin:0;letter-spacing:-.01em}}
.tagline{{font-family:Fraunces,Georgia,serif;font-style:italic;font-size:10.5pt;color:var(--ink-soft);margin:1.5mm 0 0}}
.specs{{text-align:right;font-family:"IBM Plex Mono",monospace;font-size:7.2pt;
 color:var(--ink-soft);line-height:1.75;white-space:nowrap}}
.specs b{{color:var(--ink);font-weight:500}}
.rulebar{{display:flex;height:2.6mm;margin:0 0 3.5mm}}
.rulebar i{{flex:1}}
.rulebar i:nth-child(1){{background:var(--plains)}}.rulebar i:nth-child(2){{background:var(--stone)}}
.rulebar i:nth-child(3){{background:var(--forest)}}.rulebar i:nth-child(4){{background:var(--ocean)}}
.lede{{font-family:Fraunces,Georgia,serif;font-size:10.6pt;line-height:1.3;margin:0 0 3mm}}
.lede b{{font-weight:600}}
.wide{{max-width:{HERO_MM}mm;margin:0 auto 3mm}}
.wide svg{{width:100%;height:auto;display:block}}
.wide figcaption{{font-family:"IBM Plex Mono",monospace;font-size:6.8pt;line-height:1.5;
 color:var(--ink-soft);margin-top:1.5mm;text-align:center}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:0 7mm;flex:1;min-height:0;align-content:start}}
h2{{font-family:"IBM Plex Mono",monospace;font-size:7pt;letter-spacing:.16em;text-transform:uppercase;
 color:var(--ink-soft);margin:0 0 1.2mm;padding-top:2.5mm;border-top:1px solid var(--rule)}}
.cols > section > h2:first-child{{padding-top:0;border-top:0}}
p{{margin:0 0 2.4mm}}
strong{{font-weight:600}}
footer{{border-top:1.5px solid var(--ink);margin-top:2mm;padding-top:2mm;
 display:flex;justify-content:space-between;gap:6mm;
 font-family:"IBM Plex Mono",monospace;font-size:7pt;color:var(--ink-soft)}}
footer b{{color:var(--ink);font-weight:500}}
</style></head><body>

<header>
  <div>
    <p class="eyebrow">A meld-building civilization game</p>
    <h1>Blink</h1>
    <p class="tagline">Climbing the ladder of civilization</p>
  </div>
  <div class="specs">
    <b>2–4 players</b> · age 10+<br>
    <b>60–90 minutes</b> · competitive<br>
    Toby Siko · Deep Diversions<br>
    deep-diversions.com/blink
  </div>
</header>
<div class="rulebar"><i></i><i></i><i></i><i></i></div>

<p class="lede">A game of tricks and territory, in which the cards you play are also the budget you
spend. Win the trick and you act first — but every card in that winning meld still has to become a
settler, a new tile, an attack, or a coin.</p>

<figure class="wide">{fig}<figcaption>The table from your seat. The map in the middle is shared and
grows all game; the market beside it is where cards are bought; every meld played stays in the play
area until it is spent.</figcaption></figure>

<div class="cols">
  <section>
    <h2>The round</h2>
    <p>Everyone plays a meld at the same time — <strong>any cards whose ranks form an unbroken
       run</strong>. Duplicates are free and suits are irrelevant, so one rule replaces straights,
       sets and full houses. The highest total wins the trick and acts first; matching the winner's
       card count and losing costs you a card; the meld that ranks last takes a coin.</p>
    <p>Then, in that order, every player spends the very cards they just played. Each one settles a
       unit, explores a new tile, attacks a neighbour, or is cashed for gold — always on terrain
       matching the card's suit, always beside ground you already hold. You never choose a move
       separately from the cards: <strong>the meld is the budget</strong>.</p>
    <h2>Growth is the clock, and the bill</h2>
    <p>Your twenty units sit in five tiers and leave from the top. Each tier you empty raises your
       meld size, your free movement and the rank you may buy — and raises the food your people cost
       every time your hand recycles.</p>
  </section>
  <section>
    <h2>Combat is a duel</h2>
    <p>An attack <em>is</em> the card you spent. The defender answers with a card from hand plus the
       terrain's defence — forest one, mountain two — and the higher rank wins. Clear the last
       defender and the ground changes hands on the spot. It is the only moment you act on somebody
       else's turn, and it makes the cards you hold back worth holding.</p>
    <h2>How it ends</h2>
    <p>The game ends when a player places their last unit, or the market thins to its last layer.
       Finish the round, play one more, then score: a point per unit on the map; one per card in
       your victory row, plus the rank in its centre slot; three for each terrain where you hold the
       largest connected stretch.</p>
    <h2>Why it plays differently</h2>
    <p>Trick-taking asks one question — can I win this? Blink asks it twice, in opposite
       directions: the meld that takes the trick is the meld you must now spend.</p>
  </section>
</div>

<footer>
  <span><b>Components</b> · 80 cards · 60 terrain tiles · 80 units · 4 player boards · coins · dice</span>
  <span>deep-diversions.com/blink</span>
</footer>
</body></html>'''
open('onepager.html','w',encoding='utf-8').write(HTML)
txt=re.sub(r'(?s)<svg.*?</svg>',' ',HTML)
txt=re.sub(r'(?s)<(style|script|head)\b.*?</\1>',' ',txt)
body=re.search(r'(?s)<body.*?</body>',txt).group(0)
body=re.sub(r'(?s)<figcaption.*?</figcaption>',' ',body)
print('prose words:', len(re.findall(r"[A-Za-z][A-Za-z'’-]*", re.sub(r'<[^>]+>',' ',body))))
