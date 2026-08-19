# -*- coding: utf-8 -*-
"""Verify the printed rulebook against the code that plays the game.

Every number in the rulebook exists twice: once as prose a person reads, once
as a constant a program obeys. The v0.22 audit found four places where the two
had drifted apart — tier unit counts, rank caps, the victory row's scoring, and
the trick. This checks the survivors match, so the next drift is caught by a
build rather than by a playtest.

Sources of truth:
  * app/engine.js  — the playable client, which is what has been measured
  * sim/engine.py  — the simulator
Run after build_html.py and board_a4.py:  python3 check_rules.py
"""
import html
import json
import re
import sys
from pathlib import Path
from version import RULES_HTML

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
fails = []


def text_of(path):
    raw = path.read_text(encoding="utf8")
    t = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(t))


def check(cond, what):
    if not cond:
        fails.append(what)


# ---------------------------------------------------------------- the code
js = (ROOT / "app" / "engine.js").read_text(encoding="utf8")
m = re.search(r"const BANDS = \[(.*?)\];", js, re.S)
if not m:
    sys.exit("cannot find BANDS in app/engine.js")
# ["Tribe", units, meldLimit, food, freeMoves, ascension, rankCap]
bands = []
for row in re.finditer(r'\["([A-Za-z]+)",\s*([\d,\s]+)\]', m.group(1)):
    name, nums = row.group(1), [int(x) for x in row.group(2).split(",") if x.strip()]
    bands.append((name, *nums))
check(len(bands) == 5, f"engine has {len(bands)} tiers, not 5")
UNITS = [b[1] for b in bands]
MELD = [b[2] for b in bands]
FOOD = [b[3] for b in bands]
MOVES = [b[4] for b in bands]
ASC = [b[5] for b in bands]
CAPS = [b[6] for b in bands]
check(sum(UNITS) == 20, f"the five tiers hold {sum(UNITS)} units, not 20")

py = (ROOT / "sim" / "engine.py").read_text(encoding="utf8")
pyb = re.findall(r'\("(?:Tribe|Settlement|Kingdom|Empire|Civilization)",([\d,\s]+)\)', py)
if pyb:
    pyn = [[int(x) for x in r.split(",") if x.strip()] for r in pyb[:5]]
    check([r[0] for r in pyn] == UNITS,
          f"sim tier units {[r[0] for r in pyn]} != app {UNITS}")
    check([r[5] for r in pyn] == CAPS,
          f"sim rank caps {[r[5] for r in pyn]} != app {CAPS}")

# ------------------------------------------------------------- the rulebook
# version.py exists so a bump cannot leave a file behind; this line used to
# hardcode v0.22 and would have quietly checked the wrong rulebook after one.
rules = text_of(HERE / RULES_HTML)

# 1. the tier table, in order, as "Tribe 2 2 1 free 11"
row = re.search(r"Tribe (\d+) (\d+) (\d+) free (\d+)", rules)
check(bool(row), "cannot find the Tribe row of the tier table")
if row:
    u, ml, mv, cap = (int(x) for x in row.groups())
    check(u == UNITS[0], f"Tribe prints {u} units, engine has {UNITS[0]}")
    check(ml == MELD[0], f"Tribe prints meld limit {ml}, engine has {MELD[0]}")
    check(mv == MOVES[0], f"Tribe prints {mv} free moves, engine has {MOVES[0]}")
    check(cap == CAPS[0], f"Tribe prints rank cap {cap}, engine has {CAPS[0]}")
for i, name in enumerate(["Settlement", "Kingdom", "Empire", "Civilization"], start=1):
    r = re.search(rf"{name} (\d+) (\d+) (\d+) (\d+) (\d+)", rules)
    check(bool(r), f"cannot find the {name} row of the tier table")
    if r:
        u, ml, mv, food, cap = (int(x) for x in r.groups())
        check(u == UNITS[i], f"{name} prints {u} units, engine has {UNITS[i]}")
        check(ml == MELD[i], f"{name} prints meld limit {ml}, engine has {MELD[i]}")
        check(mv == MOVES[i], f"{name} prints {mv} moves, engine has {MOVES[i]}")
        check(food == FOOD[i], f"{name} prints food {food}, engine has {FOOD[i]}")
        check(cap == CAPS[i], f"{name} prints cap {cap}, engine has {CAPS[i]}")

# 2. setup and quick reference repeat the unit counts; they must agree
setup = "/".join(str(u) for u in UNITS)
check(f"tiers of {' / '.join(str(u) for u in UNITS)}" in rules,
      f"the quick reference does not print tiers of {' / '.join(str(u) for u in UNITS)}")
check(", ".join(str(u) for u in UNITS) + " from the top" in rules,
      f"setup does not print {', '.join(str(u) for u in UNITS)} from the top")
caps_ref = "/".join(str(c) for c in CAPS)
check(caps_ref in rules, f"the quick reference does not print the caps as {caps_ref}")

# 3. ascension coins
check(" / ".join(str(a) for a in ASC[1:]) in rules,
      f"ascension coins {ASC[1:]} are not printed as a run")

# 4. the trick, as the engine resolves it under the default rule
check('trickRule || "dock"' in js, "the app's default trick rule is no longer 'dock'")

# 4b. v0.23: the trick goes to the highest TOTAL RANK, not the most cards.
#     Four rules moved at once in v0.23, and the whole point of this file is
#     that a rulebook and an engine cannot drift apart quietly — so each of the
#     four is pinned on both sides.
check('opts.meldScore === "count" ? "count" : "sum"' in js,
      "the engine's default trick scoring is no longer the highest total")
check("highest total wins" in rules,
      "the rulebook does not say the highest total wins the trick")
check("Most cards wins the trick" not in rules,
      "the rulebook still says most cards wins")
# the worked example has to be worked the new way, or it teaches the old rule
check(re.search(r"8 \+ 8 for.{0,40}16", rules),
      "the worked example does not add the winning meld up")

# 4c. research runs up to twice a turn, at a rising price
check('? opts.researchRule : "twice"' in js,
      "the engine's default is no longer two researches a turn")
check("up to twice per turn" in rules.lower(),
      "the rulebook still prints research as once a turn")
check(re.search(r"first research of your turn costs 1 gold, the second costs 2", rules),
      "the rulebook does not print the rising research price")

# 4d. effect A adds the card's own rank
check('let A_SUM_LADDER = "rank"' in js,
      "the engine's effect A no longer adds the card's own rank")
check("+1 card" not in rules and "+2 cards" not in rules,
      "the rulebook still prints effect A as +1/+2 cards")
eff = text_of(HERE / "Blink-card-effects.html")
check("rank" in eff and "+1 card" not in eff,
      "the effects document still prints effect A as +1 card")
check("set aside" in rules, "the rulebook never mentions setting a card aside")
check("winner spends one extra card" not in rules.lower(),
      "the rulebook still promises the winner an extra card")
check("discards one card" not in rules.lower(),
      "the rulebook still discards a card from hand for matching the winner")

# 5. the victory row scores 1 per card PLUS the centre rank
check(re.search(r"1 point per card", rules), "the row's per-card point is not printed")
worked = re.search(r"5 cards — 6, 9, 14, 16, 17.*?= (\d+)", rules)
check(bool(worked) and worked.group(1) == "19",
      f"the worked five-card row scores {worked.group(1) if worked else '?'}, expected 19")

# 6. research: automatic placement, lowest card retired, and the caps again
check("highest rank" in rules and "Nobody chooses this" in rules,
      "§10 does not say the draw is placed automatically")
check("lowest-ranked card in your hand" in rules,
      "§10 does not restrict the retire to the lowest card")
check('retireRule || "lowest"' in js,
      "the app's default retire rule is no longer 'lowest'")
check("or discard" not in rules.split("Retire the lowest")[1][:200],
      "§10 still offers to retire from the discard, which nothing implements")

# 7. effect B founds ground, in reach, 2 out for the 6-10 band
check("may not explore" not in rules,
      "the stale 'B may not explore' sentence is still in §10")
check("within your reach" in rules and "up to two tiles out" in rules,
      "§10 does not state B's reach, or the 6-10 band's exception")
check("reachOut(this.m, p.i, dist)" in js,
      "the engine no longer applies a reach to colonies")

# 8. the market is nine positions in both the rules and the engine
check("nine" in rules and "3 × 3" in rules, "the market is not printed as 3 x 3 = nine")
check("opts.gridSize || 9" in js, "the engine's market is no longer nine positions")

# 9. attack costs and capacities
for terr, holds, cost in [("Plains", 3, "free"), ("Ocean", 1, "free"),
                          ("Forest", 2, "1"), ("Mountain", 1, "2")]:
    check(re.search(rf"{terr} {holds} {cost}", rules),
          f"the terrain table does not print {terr} {holds} / {cost}")
check('plains: 3, forest: 2, ocean: 1, mountain: 1' in js.replace('"', '')
      or 'HOLDS' in js, "cannot find the engine's terrain capacities")

# ------------------------------------------------------------- the board
board = (HERE / "board_a4.svg").read_text(encoding="utf8")
for cap in CAPS:
    check(f">{cap}<" in board, f"the player board does not print rank cap {cap}")
# the unit slots, counted per row: this is the component players actually load
import collections
rows = collections.Counter()
for c in re.finditer(r'<circle[^>]*cy="([\d.]+)"[^>]*r="6.50"', board):
    rows[round(float(c.group(1)), 1)] += 1
drawn = [n for _, n in sorted(rows.items())]
check(drawn == UNITS, f"the board draws {drawn} unit slots per tier, engine has {UNITS}")

# ------------------------------------------------------------- the tutorial
tut = text_of(HERE / "Blink-first-game.html")
check(", ".join(str(u) for u in UNITS) + " from the top" in tut,
      "the tutorial still prints the old tier unit counts")
check("winner spends one extra card" not in tut.lower(),
      "the tutorial still promises the winner an extra card")
check("lowest-ranked card in your hand" in tut,
      "the tutorial does not teach the lowest-card retire")

print("\n".join("FAIL: " + f for f in fails) if fails else
      "rulebook agrees with the engine: tiers "
      + "/".join(str(u) for u in UNITS)
      + ", caps " + "/".join(str(c) for c in CAPS)
      + ", meld limits " + "/".join(str(m) for m in MELD)
      + ", the highest-total trick, research twice a turn, effect A adding the card\u2019s rank, the lowest-card retire, and B in reach")
sys.exit(1 if fails else 0)
