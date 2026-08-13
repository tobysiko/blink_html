# -*- coding: utf-8 -*-
import json, pathlib, re
from version import VTAG

# reuse the rulebook CSS
src = pathlib.Path("build_html.py").read_text()
CSS = src.split('CSS = """', 1)[1].split('"""', 1)[0]

PF = json.loads(pathlib.Path("pattern_figs.json").read_text())

# deck: (key, name, points, tagline, counting rule)
DECK = [
    # (key, name, points, tagline, exact requirement)
    # Ordered easiest to hardest AS MEASURED ON v0.20. That ordering no longer
    # holds: see sim/findings-v021-objectives.md. All are worth 4 for now.
    ("foothills", "Foothills", 4,
     "Where the stone gives way to soil.",
     "A mountain, next to a forest, next to a plains."),
    ("watershed", "Watershed", 4,
     "Every drop from here reaches the sea.",
     "A mountain, next to a plains, next to an ocean."),
    ("highland_rivers", "Highland Rivers", 4,
     "Snowmelt finds its way down.",
     "A mountain, next to a forest, next to an ocean."),
    ("fjord", "Fjord", 4,
     "Deep water between two shoulders of rock.",
     "A mountain, next to an ocean, next to another mountain."),
    ("mountain_pass", "Mountain Pass", 4,
     "The one way through, and everyone knows it.",
     "A plains, next to a mountain, next to another plains."),
    ("coastal_chain", "Coastal Chain", 4,
     "Two shores and the water between.",
     "A plains, next to an ocean, next to another plains."),
    ("clearing", "Clearing", 4,
     "Open sky in the middle of the wood.",
     "A forest, next to a plains, next to another forest."),
    ("mountain_lookout", "Mountain Lookout", 4,
     "One peak, and the sea on either hand.",
     "An ocean, next to a mountain, next to another ocean."),
    ("riverbank", "Riverbank", 4,
     "Soft ground, and everything grows.",
     "A plains, next to a forest, next to an ocean."),
    ("timberline", "Timberline", 4,
     "The last trees before the rock.",
     "A forest, next to a mountain, next to another forest."),
    ("river_delta", "River Delta", 4,
     "Where the water spreads and slows.",
     "An ocean, next to a plains, next to a forest."),
    ("sheltered_water", "Sheltered Water", 4,
     "Wooded on both sides, calm between.",
     "A forest, next to an ocean, next to another forest."),
]


def card_block(key, name, pts, tag, rule, reusable=False):
    badge = (f'<span class="pts">{pts}</span>'
             f'<span class="pts-l">{"pt" if pts==1 else "pts"}</span>')
    note = ""
    return (f'<div class="pat">'
            f'<div class="pat-fig">{PF[key]}</div>'
            f'<div class="pat-body">'
            f'<div class="pat-head"><h3>{name}</h3><div class="pat-badge">{badge}</div></div>'
            f'<p class="tag-line">{tag}</p>'
            f'<p class="pat-rule">{rule}</p>{note}'
            f'</div></div>')


cards_html = ""
for key, name, pts, tag, rule in DECK:
    cards_html += card_block(key, name, pts, tag, rule,
                             reusable=(key == "river_flow"))

EXTRA_CSS = """
.pat{display:grid;grid-template-columns:230px 1fr;gap:1.6rem;align-items:center;
  padding:1.1rem 0;border-bottom:1px solid var(--rule);break-inside:avoid}
.pat-fig svg{width:100%;height:auto;max-height:170px;display:block}
.pat-head{display:flex;align-items:baseline;justify-content:space-between;gap:1rem;margin:0 0 .15rem}
.pat-head h3{font-family:Fraunces,Georgia,serif;font-size:1.15rem;margin:0;font-weight:600}
.pat-badge{display:flex;align-items:baseline;gap:.3rem;white-space:nowrap}
.pts{font-family:Fraunces,Georgia,serif;font-size:1.5rem;font-weight:600;color:var(--red)}
.pts-l{font-family:"IBM Plex Mono",monospace;font-size:.66rem;letter-spacing:.1em;
  text-transform:uppercase;color:var(--stone)}
.tag-line{font-style:italic;color:var(--ink-soft);margin:0 0 .35rem;font-size:.9rem}
.pat-rule{margin:0;font-size:.9rem;line-height:1.5}
.reuse{margin:.35rem 0 0;font-size:.82rem;color:var(--ink-soft)}
.pat-rule b{font-weight:600}
@media print{.pat{break-inside:avoid}}
"""

HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Blink \u2014 Map Objectives</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400..600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}{EXTRA_CSS}</style>
</head>
<body>
<div class="sheet">

<header class="mast pad">
  <p class="eyebrow">Advanced module \u00b7 secret objectives</p>
  <h1>Map Objectives</h1>
  <p class="sub">A secret shape to build toward</p>
</header>

<main class="pad">
<section>
  <p>Once the base game feels familiar, add this layer. Every player is dealt a
  <strong>secret goal for the shape of their world</strong> \u2014 a river running down from
  the highlands, a range of peaks, a stretch of coast \u2014 and spends the game quietly
  steering their expansion toward it. The map stops being a place to spread and becomes
  a place to compose.</p>

  <div class="h2"><span class="num">01</span><h2>Setup &amp; scoring</h2></div>
  <ol class="seq">
    <li><b>Deal two, keep one.</b> Shuffle the objective cards and deal <strong>two to each
    player, face down</strong>. Look at both, keep one, and return the other to the box
    unseen. Choose before the card draft if you can \u2014 the objective you keep should
    inform the hand you build.</li>
    <li><b>Keep it hidden.</b> Your objective stays secret for the whole game. Nobody is
    told what anyone is chasing.</li>
    <li><b>Reveal together.</b> At the end of the game, after the base score is counted,
    every player turns their objective face up at the same moment and adds its points if
    they completed it.</li>
  </ol>

  <div class="note">
    <span class="tag">Completed or not \u2014 there is no half</span>
    <p>An objective scores its <strong>full value once</strong>, or nothing. You cannot
    score it twice by building the pattern twice, and there is no penalty for failing.
    Every pattern is exactly <strong>three tiles</strong>, and every tile must be one you
    <strong>occupy</strong> \u2014 a tile with at least one of your units standing on it.
    Empty tiles, and tiles held only by a rival, never count.</p>
  </div>

  <p>Every objective is worth <strong>4 points</strong>. For scale, a finished game usually
  scores somewhere between twenty and thirty, so an objective is worth roughly a fifth of a
  good result \u2014 enough to steer a game, not enough to decide one on its own.</p>
  <p>All twelve ask for the same thing in different terrain: <strong>three tiles you occupy
  in a chain</strong>, the middle one touching both ends. They are alike in
  shape so that the choice you make when you keep one is about <em>your hand</em>, not about
  which card is easiest. If you drafted Ocean, the Fjord and the Lookout are close; if you
  drafted Plains, the Mountain Pass is.</p>
  <div class="note">
    <span class="tag">Not yet re-tuned for v0.21 — play the base game first</span>
    <p>This deck was balanced against the v0.20 placement rules, where a meld landed as a
    connected pattern. Under v0.21 the map ends about <strong>20% smaller</strong> and
    players hold fewer tiles, so the chains are harder across the board — and no longer
    evenly hard. Measured passively, they now range from about <strong>1% to 28%</strong>
    where they once sat in a much narrower band, and <em>Mountain Pass</em>,
    <em>Coastal Chain</em> and <em>Clearing</em> have all but stopped happening.</p>
    <p>Treat the twelve as a draft. They are still playable — nothing here contradicts the
    base rules — but the promise that all twelve are equally reachable is not currently
    true, and the flat 4 points needs revisiting once v0.21 has been played.</p>
  </div>
  <p class="fine">Twelve cards is enough for four players to be dealt two each with four
  still unseen, so no table ever sees the whole deck.</p>

  <div class="note">
    <span class="tag">Building in the open</span>
    <p>Your objective is secret; your map is not. Every chain uses ordinary, useful ground,
    so the early tiles of one look like plain expansion \u2014 but the third tile is the tell.
    A rival who guesses right can settle the space you needed, and a chain broken at the
    last tile is worth nothing. Build the ambiguous end first.</p>
  </div>

  <div class="h2"><span class="num">02</span><h2>The objectives</h2></div>
  {cards_html}

  <div class="h2"><span class="num">03</span><h2>Going further</h2></div>
  <p>Two variants once the layer is second nature:</p>
  <ul>
    <li><strong>Open objectives.</strong> Deal two face up beside the map, shared by
    everyone, each player scoring it if they build it. A gentler, more readable game \u2014
    good for teaching the patterns.</li>
    <li><strong>Keep both.</strong> Deal two and keep both, each still worth its full
    value. More points in play and a broader target, at the cost of some focus.</li>
  </ul>
</section>
</main>

<div class="pad"><footer>Blink \u00b7 advanced module \u00b7 map objectives \u00b7 {VTAG} \u00b7
companion to the base rules</footer></div>

</div>
</body>
</html>"""

out = pathlib.Path("./Blink-map-objectives.html")
out.write_text(HTML)
print("wrote", out, len(HTML), "bytes")
