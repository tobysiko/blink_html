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

# 2b. §04's PROSE, and the board FIGURE, hold their own copies of that column —
#     and both kept the v0.22 numbers through the v0.23 change while the table
#     beside them was correct, so §04 contradicted itself and the figure caption
#     described a board nobody has. Every place the column appears is checked
#     now, not only the one that was easy to parse.

# Read the numbers out of the sentence rather than matching a fixed phrase, so
# the prose stays free to say "2, then 3, then 5, then 5, then a final 5".
m = re.search(r"20 units in five tiers\s*[—-]\s*((?:\d+[^0-9]{1,20}){4}\d+)", rules)
check(bool(m), "cannot find §04's sentence naming the five tiers")
if m:
    prose_units = [int(x) for x in re.findall(r"\d+", m.group(1))]
    check(prose_units == UNITS,
          f"§04's opening sentence says the tiers are {prose_units}, the engine "
          f"has {UNITS} — the sentence has its own copy of the column and can "
          "disagree with the table printed directly below it")
fig = (HERE / "build_figs.py").read_text(encoding="utf8")
m = re.search(r"bands = \[(.*?)\]\n", fig, re.S)
check(bool(m), "cannot find the board figure's own tier table")
if m:
    fig_units = [int(x) for x in re.findall(r'"\w+", \d+, (\d+),', m.group(1))]
    check(fig_units == UNITS,
          f"the board figure draws {fig_units} units per tier, engine has {UNITS}")

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
# ...and §10's OWN body, not just the quick reference. A phrase-anywhere check
# passed while §10 still opened "Once per turn, during your map phase" and its
# step 3 still said "Pay 1 gold" — the section contradicted the summary of
# itself two pages later, which is exactly the drift this file exists to catch.
sec10 = rules.split("Research and the market")[-1].split("A worked example")[0]
check("Once per turn, during your map phase" not in sec10,
      "§10 still opens by saying research is once per turn")
check("up to twice per turn" in sec10.lower(),
      "§10's own body never says research may be taken twice")
check(re.search(r"1 gold the first time this turn, 2 the second", sec10),
      "§10's steps do not state the rising price where a player follows them")
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
# The trick payout was the single hardest thing to keep straight while the rule
# changed, because the old "bonus" rule (the winner spends one card MORE than
# they played) can be written a dozen ways and the first version of this check
# looked for exactly one of them — "winner spends one extra card" — a sentence
# the rulebook never actually contained. It passed for months while the lede
# and section 01 both still promised the bonus card.
#
# So match the SHAPE of the claim rather than one wording, and let a negation
# through, because section 04 says out loud that there is no bonus card and
# that sentence is the correct one.
BONUS_CLAIMS = [
    r"one card more than (?:you|they|the winner) (?:played|play)",
    r"spends? (?:one )?(?:an )?(?:extra|additional|bonus) card",
    r"(?:extra|additional|bonus) card from (?:your|their|the winner's) hand",
    r"winner'?s bonus card",
]
NEGATED = re.compile(r"\b(?:no|not|never|nothing|neither|rather than|instead of)\b[^.]{0,60}$")


def no_bonus_rule(doc, where):
    """The printed trick payout must be `dock`, which is what the engine plays."""
    for pat in BONUS_CLAIMS:
        for m in re.finditer(pat, doc, re.I):
            before = doc[max(0, m.start() - 90):m.start()]
            if NEGATED.search(before):
                continue          # "there is no winner's bonus card" — correct
            quote = doc[max(0, m.start() - 40):m.end() + 20].strip()
            fails.append(f"{where} still describes the winner's bonus card: ...{quote}...")


no_bonus_rule(rules, "the rulebook")
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

# 9. capacities and the defence bonus. The second column used to be a gold
# price; under the duel it is what the ground adds to the DEFENDER's card, and
# both numbers are read out of the engine rather than written here twice.
holds_js = dict(re.findall(r"(\w+):\s*(\d+)",
                           re.search(r"HOLDS = \{([^}]*)\}", js).group(1)))
def_js = dict(re.findall(r"(\w+):\s*(\d+)",
                         re.search(r"TERRAIN_DEFENCE = \{([^}]*)\}", js).group(1)))
for terr in ("plains", "ocean", "forest", "mountain"):
    check(re.search(rf"{terr.capitalize()} {holds_js[terr]} \+{def_js[terr]}", rules),
          f"the terrain table does not print {terr.capitalize()} "
          f"{holds_js[terr]} / +{def_js[terr]}")
check('plains: 3, forest: 2, ocean: 1, mountain: 1' in js.replace('"', '')
      or 'HOLDS' in js, "cannot find the engine's terrain capacities")

# ------------------------------------------------------------- the board
board = (HERE / "board_a4.svg").read_text(encoding="utf8")
for cap in CAPS:
    check(f">{cap}<" in board, f"the player board does not print rank cap {cap}")

# The victory row scores TWICE under the default rule — a point per card AND
# the centre rank on top. The board printed only the rank half for a while,
# which makes a full row of five look worth five points less than it is. That
# was caught by a person reading the sheet, not by this file, so:
vrow_rule = re.search(r'let VROW_RULE = "([a-z+]+)"', js)
check(bool(vrow_rule), "cannot find VROW_RULE in app/engine.js")
if vrow_rule and vrow_rule.group(1) == "card+centre":
    board_txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", board))
    check(re.search(r"1\s+per card in your victory row", board_txt),
          "the player board does not print the victory row's point PER CARD")
    check(re.search(r"rank of its CENTRE card", board_txt, re.I),
          "the player board does not print the victory row's centre rank")
    check(re.search(r"1 point per card in the row", rules),
          "the rulebook does not print the victory row's point per card")

# The board now carries the order of play, so it can contradict the engine
# about how a trick is won just as easily as the rulebook could.
board_txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", board))
check("ROUND" in board_txt, "the player board has no order of play")
for step in ["Declare A effects", "Leader plays a meld", "Spend melds in initiative order",
             "leads the next round"]:
    check(step in board_txt, f"the board's round order is missing: {step}")
check(re.search(r"Highest TOTAL wins", board_txt),
      "the board's round order does not say the highest TOTAL wins the trick")

# The map phase is the half a player forgets, and every item in it is a rule
# the engine enforces — so the board's turn menu is checked against the
# engine's own numbers rather than trusted.
# "majority" reads as most units, which is the engine's OTHER option. The
# default scores the largest connected stretch, and the rulebook calls that
# dominance and never says majority — but the board did, in the one place a
# player would read it while adding up their score.
maj = re.search(r'opts\.majority \|\| "([a-z]+)"', js)
check(bool(maj), "cannot find the engine's MAJORITY default")
if maj and maj.group(1) == "area":
    check("majority" not in board_txt.lower(),
          "the board says terrain MAJORITY, but the engine scores the largest "
          "connected stretch — majority is the other rule")
    check(re.search(r"biggest connected stretch", board_txt),
          "the board does not say the terrain point is the biggest connected stretch")
    check("majorit" not in rules.lower(),
          "the rulebook says terrain majority, but the engine scores area")

# The market is ONE face-down deck with nine face up. The worked example set
# it up the v0.22 way — four suit decks, a four-card market — nine lines after
# the same section said "upgrade deck ... shuffled together".
check("four suit decks" not in rules and "four-card market" not in rules,
      "the rulebook still sets up the v0.22 four-suit market somewhere")
check(rules.count("3 \u00d7 3 grid") >= 2 or rules.count("3 × 3 grid") >= 2,
      "the rulebook does not consistently describe the 3x3 market grid")

# ---------------------------------------------- the two optional modules
# Both sit on top of the base rules, so they can go stale on their own without
# breaking anything the earlier checks look at.

# 12 — map objectives. The card count, the points and the modes all live in the
# engine; the section must not invent its own.
# Scope each module check to its OWN section. Searching the whole document
# passes on coincidence — "12" is also a rank cap, and "4 points" appears in
# the dominance rule, so both checks were green no matter what section 12 said.
def section(html_src, sid):
    m = re.search(rf'<section id="{sid}">(.*?)</section>', html_src, re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", m.group(1)))) if m else ""

raw_rules = (HERE / RULES_HTML).read_text(encoding="utf8")
obj_sec = section(raw_rules, "objectives")
perk_sec = section(raw_rules, "perks")
check(bool(obj_sec), "the rulebook has no map objectives section")
check(bool(perk_sec), "the rulebook has no perks section")

n_obj = len(re.findall(r'\["[A-Z][a-z]+[^"]*",\s*"(?:mountain|forest|plains|ocean)"', js))
check(n_obj > 0, "cannot find the objective cards in app/engine.js")
words = {12: "twelve", 6: "six", 8: "eight", 10: "ten", 14: "fourteen"}
check(words.get(n_obj, str(n_obj)) in obj_sec,
      f"section 12 does not say there are {n_obj} objective cards")
pts = re.search(r"points:\s*(\d+)", js)
check(bool(pts) and f"{pts.group(1)} points" in obj_sec,
      f"section 12 does not print an objective as worth {pts and pts.group(1)} points")
for mode in ["Secret", "Open", "Keep both"]:
    check(mode in obj_sec, f"the objectives module is missing the {mode} mode")
modes = re.search(r'OBJECTIVES_MODE = opts\.objectives \|\| "([a-z]+)"', js)
check(bool(modes) and modes.group(1) == "off",
      "map objectives are no longer off by default in the engine")

# 13 — perks. Every number here is one the engine owns.
deal = re.search(r"const PERK_DEAL = (\d+);", js)
slots = re.search(r"const PERK_SLOTS = \[([\d, ]+)\];", js)
check(bool(deal) and bool(slots), "cannot find PERK_DEAL / PERK_SLOTS in app/engine.js")
if deal:
    numword = {2: "two", 3: "three", 4: "four", 5: "five"}.get(int(deal.group(1)))
    check(re.search(rf"deal\s+(?:{numword}|{deal.group(1)})\s+to each player",
                    perk_sec, re.I),
          f"section 13 does not say to deal {deal.group(1)} to each player")
if slots:
    nums = [int(x) for x in slots.group(1).split(",")]
    check(max(nums) == 4 and 5 not in nums,
          f"PERK_SLOTS is {nums}; the rulebook says slots 1 to 4 and slot 5 blank")
    check("slot 5 stays empty" in perk_sec.lower(),
          "section 13 does not say slot 5 stays empty")
# the wake-up thresholds, straight from perkSlotNeeds
for slot, needs in [(4, 2), (3, 3), (2, 4), (1, 5)]:
    hit = re.search(rf"\b{slot}\s+{needs} cards", perk_sec) or (slot == 1 and "all 5" in perk_sec)
    check(bool(hit), f"section 13 does not show slot {slot} waking at {needs} cards")
check("SPEND" in perk_sec and "STANDING" in perk_sec,
      "section 13 does not name the two kinds of token")
check("switches off" in perk_sec,
      "section 13 does not say that spending a card can switch a perk off")

check("YOUR TURN" in board_txt, "the player board does not say what a turn may contain")
check(re.search(r"Research: twice", board_txt),
      f"the board does not print research twice a turn (engine default "
      f"{re.search(chr(34) + 'twice' + chr(34), js) and 'twice'})")
check(re.search(r"Research: twice \u2014 1 gold, then 2|Research: twice — 1 gold, then 2", board_txt),
      "the board does not print the 1-then-2 research price")
for item in ["Fortify: 1 gold", "Move: up to MV", "refill to 10"]:
    check(item in board_txt, f"the board's turn menu is missing: {item}")
# the unit slots, counted per row: this is the component players actually load
import collections
rows = collections.Counter()
for c in re.finditer(r'<circle[^>]*cy="([\d.]+)"[^>]*r="6.50"', board):
    rows[round(float(c.group(1)), 1)] += 1
drawn = [n for _, n in sorted(rows.items())]
check(drawn == UNITS, f"the board draws {drawn} unit slots per tier, engine has {UNITS}")

# ------------------------------------------------------------------ combat
# The duel is the newest rule in the book and the one with a number per terrain,
# which is exactly the shape that goes stale quietly: change TERRAIN_DEFENCE and
# the table in section 06 keeps printing yesterday's game. So the table is read
# back out of the printed page and compared, terrain by terrain.
defence = dict(re.findall(r"(\w+):\s*(\d+)",
                          re.search(r"TERRAIN_DEFENCE = \{([^}]*)\}", js).group(1)))
check(len(defence) == 4, f"the engine defines {len(defence)} terrains, expected 4")
for terrain, bonus in defence.items():
    check(re.search(rf"\b{terrain.capitalize()} \+{bonus}\b", rules),
          f"the combat table does not print {terrain.capitalize()} +{bonus}")
# ...and the bonus must not have quietly turned back into a toll at the gate.
# Worded narrowly, because research legitimately costs 1 gold then 2, and the
# first version of this check tripped over that. What is banned is a PRICE ON
# AN ATTACK: this caught a terrain figure still labelled "costs 2 gold", a
# setup paragraph, a whole column of section 08 and two quick-reference rows,
# all teaching a rule the engine had already stopped playing.
toll = re.search(r"(?:attack|take|conquer)[^.]{0,60}costs? \d gold"
                 r"|costs? to attack"
                 r"|attack costs \d", rules, re.I)
check(not toll, "the rulebook is still charging gold to attack "
      f"(\u201c{toll.group(0) if toll else ''}\u201d) — the duel replaced that price")
check("the defender holds" in rules,
      "the rulebook does not say who wins a level duel")
check("suit matches the ground" in rules,
      "the rulebook does not print the suit tie-break for a level duel")
# winning a duel that empties the tile takes the ground. This is the change that
# made combat worth doing at all (DUEL-SPOILS.md), so the book must say it and
# the engine must default to it.
check(re.search(r"DUEL_TAKE = opts\.duelTake !== false", js),
      "the engine no longer settles a won duel by default")
check(re.search(r"ground changes hands", rules),
      "section 06 does not say a won duel takes the ground")
# a defence bonus is only a defence bonus if the rule adds it to the DEFENDER
check(re.search(r"Defence.{0,80}rank.{0,40}terrain.s defence bonus", rules, re.S),
      "section 06 no longer adds the terrain bonus to the defender's rank")

# ------------------------------------------------------------- the tutorial
tut = text_of(HERE / "Blink-first-game.html")
check(", ".join(str(u) for u in UNITS) + " from the top" in tut,
      "the tutorial still prints the old tier unit counts")
no_bonus_rule(tut, "the tutorial")
# the tutorial is where a player meets combat for the first time, so it has to
# teach the rule that is played and not the one that was replaced
check(not re.search(r"attacking into \w+ \(\d\)", tut, re.I),
      "the tutorial still charges gold to attack")
check("duel" in tut.lower(), "the tutorial never mentions the duel")
check("the tile is yours" in tut, "the tutorial does not say a won duel takes the ground")
for terr in ("plains", "ocean", "forest", "mountain"):
    check(f"{terr.capitalize()} +{def_js[terr]}" in tut
          or f"{terr.capitalize()} and Ocean +{def_js[terr]}" in tut
          or re.search(rf"{terr.capitalize()}[^.]{{0,30}}\+{def_js[terr]}", tut),
          f"the tutorial does not give {terr.capitalize()} its +{def_js[terr]}")
check("lowest-ranked card in your hand" in tut,
      "the tutorial does not teach the lowest-card retire")

print("\n".join("FAIL: " + f for f in fails) if fails else
      "rulebook agrees with the engine: tiers "
      + "/".join(str(u) for u in UNITS)
      + ", caps " + "/".join(str(c) for c in CAPS)
      + ", meld limits " + "/".join(str(m) for m in MELD)
      + ", the highest-total trick, research twice a turn, effect A adding the card\u2019s rank, the lowest-card retire, B in reach, and a duel defended at "
      + "/".join(defence[k] for k in ("plains", "ocean", "forest", "mountain")))
sys.exit(1 if fails else 0)
