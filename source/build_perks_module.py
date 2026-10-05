# -*- coding: utf-8 -*-
"""Blink — the perks module, as a document of its own.

Perks left the base rulebook in the v0.26 print pass (Toby, 5 Oct 2026): they
are an optional module, published separately like the expansions. This is
where their rules live now.

ONE LIST. The perks printed here are read from build_perks.PERKS, the list the
token sheet is printed from, so the document and the tokens cannot disagree
about what a token is called or what it does. check_rules.py reads both.

The rule itself is the one app/engine.js plays (Player.armPerk, perkChoices,
perkSlotNeeds, hasPerk, perkReady/spendPerk, refreshPerks, dealPerks):

  * PERK_DEAL tokens to each player, one on each of slots PERK_SLOTS (1-4);
    slot 5 stays empty. Free to rearrange until the row holds a card.
  * slot s is reachable when the row holds (6 - s) cards.
  * at each recycle, after income and before the hand comes back: every token
    turns face up again, and the player arms ONE perk from those their row
    reaches at that moment (or none).
  * the armed perk runs until the next recycle, whatever happens to the row.
  * a `once` perk turns face down when used, and comes back at the recycle.

Reuses the rulebook CSS, like the variants catalogue, so it is part of the set.

    python3 build_perks_module.py   ->  Blink-perks-module.html
"""
import pathlib
import re

from version import VTAG
from build_html import CSS
from build_perks import PERKS

HERE = pathlib.Path(__file__).resolve().parent
JS = (HERE.parent / "app" / "engine.js").read_text(encoding="utf8")

# ---- read the numbers the engine owns, rather than typing them twice ------
_deal = int(re.search(r"const PERK_DEAL = (\d+);", JS).group(1))
_slots = [int(x) for x in re.search(r"const PERK_SLOTS = \[([\d, ]+)\];", JS)
          .group(1).split(",")]
assert re.search(r"function perkSlotNeeds\(slot\) \{ return 6 - slot; \}", JS), \
    "perkSlotNeeds changed - the slot table below assumes 6 - slot"
NEEDS = {s: 6 - s for s in _slots}

# Which printed perks the app plays: those in the engine's PERKS table without
# `todo`. Only the count is printed, in the designer's note.
_block = re.search(r"const PERKS = \{(.*?)\n\};", JS, re.S).group(1)
_wired = set()
for m in re.finditer(r'name:\s*"([^"]+)"[^}]*\}', _block):
    if "todo: true" not in m.group(0):
        _wired.add(m.group(1))
N_APP = sum(1 for _k, name, _r in PERKS if name in _wired)

NUMWORD = {2: "two", 3: "three", 4: "four", 5: "five", 16: "sixteen",
           17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty"}
N_TOKENS = len(PERKS)

EXTRA = """
@page{size:A4;margin:16mm 16mm 16mm 16mm}
body{font-size:9.6pt;line-height:1.42}
.sheet{max-width:none;box-shadow:none;background:#fff}
.pad{padding:0}
.mast{padding:0 0 .8rem}
section{padding:.8rem 0 .2rem}
h3{margin:.8rem 0 .3rem}
table{font-size:8.8pt;margin:.4rem 0 .7rem}
table.perks td:first-child{white-space:nowrap;font-weight:600}
table.perks td:nth-child(2){white-space:nowrap;font-family:"IBM Plex Mono",monospace;
  font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:#5A5F59}
footer{padding:.8rem 0 0;break-before:avoid}
@media print{
  p,li{orphans:2;widows:2}
  ul,.note{break-inside:avoid}
  /* the long perk list may run on to the next page, a whole row at a time,
     rather than leave half a page blank in front of it */
  table.perks{break-inside:auto}
}
/* the step circles are 1.5rem; at this body size a one-line step is shorter */
.seq>li{min-height:1.75rem}
"""


def slot_rows():
    bets = {
        4: "Working almost at once. The safe place for the perk you want most.",
        3: "Reachable in most games.",
        2: "Late, and only if you keep researching.",
        1: "A long shot: fill the row and never spend it down.",
    }
    out = []
    for s in sorted(NEEDS, reverse=True):
        n = NEEDS[s]
        held = "all 5" if n == 5 else f"{n} cards"
        out.append(f'<tr><td class="num-cell">{s}</td><td class="num-cell">{held}</td>'
                   f'<td>{bets.get(s, "")}</td></tr>')
    return "\n      ".join(out)


def perk_rows():
    rows = []
    for kind, name, rule in sorted(PERKS, key=lambda p: p[1]):
        rows.append(f"<tr><td>{name}</td><td>{'Spend' if kind == 'spend' else 'Standing'}"
                    f"</td><td>{rule}</td></tr>")
    return "\n      ".join(rows)


HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Blink — Perks module</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400..600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}{EXTRA}</style>
</head>
<body>
<div class="sheet"><div class="pad">

<header class="mast">
  <p class="eyebrow">An optional module for the base rules {VTAG}</p>
  <h1 style="font-size:2.6rem;line-height:1">Perks</h1>
  <p class="sub" style="font-size:1.05rem">A job for every slot of your victory row</p>
</header>
<div class="steprule"><i></i><i></i><i></i><i></i></div>

<main>

<section style="border-top:none">
  <div class="h2"><span class="num">01</span><h2>What the module adds</h2></div>
  <p class="lede">Perks give the slots of your victory row a job of their own. Every
  rule of the base game still applies; this module adds one step to the recycle and a
  small hand of tokens beside your board.</p>
  <p><strong>Exactly one perk runs at a time</strong>, and you choose which at every
  recycle, from the perks your row is deep enough to reach <em>at that moment</em>. A deep
  row does not run four perks — it chooses from four. No perk runs before your first
  recycle.</p>
  <p>Once armed, a perk <strong>keeps running until your next recycle</strong>, even if you
  spend the victory card that unlocked it. Spending a victory card costs you nothing now;
  it shows up at the next recycle, as a shorter menu.</p>
</section>

<section>
  <div class="h2"><span class="num">02</span><h2>Components</h2></div>
  <ul>
    <li><strong>{N_TOKENS} perk tokens</strong> — one of each perk listed in §05. Each is a
    fold-over token: a <b>ready</b> face and a <b>spent</b> face. Print them from the perk
    token sheet, cut along the dashed lines and fold along the dotted one.</li>
  </ul>
</section>

<section>
  <div class="h2"><span class="num">03</span><h2>Setup</h2></div>
  <p>Do this after the base game's setup, before the first card is played.</p>
  <ol class="seq">
    <li>Shuffle the perk tokens and <b>deal {NUMWORD.get(_deal, _deal)} to each
    player</b>. Return the rest to the box unseen.</li>
    <li>Lay one token on the table just above each of <strong>slots
    {", ".join(str(s) for s in sorted(_slots)[:-1])} and {sorted(_slots)[-1]}</strong> of
    your victory row, ready face up, in any order you like. <strong>Slot 5 stays
    empty</strong>: it fills on your first research, so a perk there would be a gift.</li>
    <li>You may rearrange your tokens until your first card reaches your victory row.
    From then on the arrangement is <strong>permanent</strong>.</li>
  </ol>

  <h3>Which slot</h3>
  <p>The victory row fills from the <strong>right</strong>, so the slot decides how long
  you wait before a perk can be armed:</p>
  <table class="wide">
    <thead><tr><th>Slot</th><th>Reachable when your row holds</th><th>The bet</th></tr></thead>
    <tbody>
      {slot_rows()}
    </tbody>
  </table>
  <p>Every perk is equal in strength; what differs is how soon you want each one, and how
  much of your row you will tie up to reach it.</p>
</section>

<section>
  <div class="h2"><span class="num">04</span><h2>Playing with perks</h2></div>
  <h3>At every recycle</h3>
  <p>The module adds one step to the recycle (base rules §08), after income and before
  you pick up your discard:</p>
  <ol class="seq">
    <li><strong>Collect your income</strong>, as in the base game.</li>
    <li><strong>Arm a perk.</strong> Turn all your perk tokens ready face up. Then choose
    <strong>one</strong> of the perks whose slot your row reaches right now, and turn that
    token sideways to show it is armed. Any perk you had armed before stops. If your row
    reaches none, or you would rather have none, nothing is armed.</li>
    <li><strong>Pick up your whole discard</strong> as your new hand, as in the base
    game.</li>
  </ol>
  <p>Only the armed perk works. The others wait, face up, for a later recycle.</p>

  <h3>The two kinds</h3>
  <ul>
    <li><strong>SPEND</strong> — use it once, then turn the token face down. It turns ready
    face up again at your next recycle.</li>
    <li><strong>STANDING</strong> — it simply works for as long as it is armed. These tokens
    never turn over.</li>
  </ul>
  <p>Each token says which kind it is.</p>

  <div class="note">
    <span class="tag">The price of a perk</span>
    <p>Every victory card you spend on A, B or C is a slot your row may no longer reach at
    the next recycle. The more you value your perks, the fewer effects you will spend — a
    player who wants every slot in reach has quietly given up their war chest.</p>
  </div>
</section>

<section>
  <div class="h2"><span class="num">05</span><h2>The perks</h2></div>
  <p>All {NUMWORD.get(N_TOKENS, N_TOKENS)} tokens, in alphabetical order. A perk works only
  while it is armed.</p>
  <table class="perks wide">
    <thead><tr><th>Perk</th><th>Kind</th><th>Effect</th></tr></thead>
    <tbody>
      {perk_rows()}
    </tbody>
  </table>
  <div class="note">
    <span class="tag">Designer's note</span>
    <p>The perks module has been played far less than the base game, and some tokens
    will need adjusting. The app currently includes {N_APP} of them. Tell me which ones
    your table arms, and which ones it never does.</p>
  </div>
</section>

</main>

<footer>Blink · perks module · for base rules {VTAG} · Toby Siko · deep-diversions.com/blink
· deep.diversions.com@gmail.com</footer>

</div></div>
</body>
</html>
"""

if __name__ == "__main__":
    out = HERE / "Blink-perks-module.html"
    out.write_text(HTML, encoding="utf-8")
    print(f"wrote {out.name} — {N_TOKENS} perks, {N_APP} in the app")
