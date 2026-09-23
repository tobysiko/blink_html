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
import pathlib
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
# The wall a tier's ground holds at is two under its rank cap. Defined here,
# beside the rest of the ladder, because the tier-table checks below need it -
# it used to be defined 550 lines down next to the board figure.
WALLS = [c - 2 for c in CAPS]
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

# 1. the tier table, in order. Under the full economy Tribe's food cell reads
# "free"; under lean (v0.26) the column is gone and the row is four numbers.
_TRIBE_FULL = r"Tribe (\d+) (\d+) (\d+) free (\d+)"
# FOUR NUMBERS AS OF v0.26: units, meld limit, rank cap, wall. Free moves left
# the ladder with the fold - movement comes from the meld, one per card played.
# This pattern has now been wrong twice by counting columns, so the width is
# derived from what the engine prints rather than written down here.
_TRIBE_LEAN = r"Tribe (\d+) (\d+) (\d+) (\d+)"
row = (re.search(_TRIBE_LEAN, rules)
       if re.search(r'ECONOMY = opts\.economy === "full" \? "full" : "lean"', js)
       else re.search(_TRIBE_FULL, rules))
check(bool(row), "cannot find the Tribe row of the tier table")
if row:
    u, ml, cap, wall = (int(x) for x in row.groups())
    check(u == UNITS[0], f"Tribe prints {u} units, engine has {UNITS[0]}")
    check(ml == MELD[0], f"Tribe prints meld limit {ml}, engine has {MELD[0]}")
    check(cap == CAPS[0], f"Tribe prints rank cap {cap}, engine has {CAPS[0]}")
    check(wall == WALLS[0], f"Tribe prints wall {wall}, engine has {WALLS[0]}")
# The FOOD column left the table in v0.26, so the row is one number shorter.
# Reading it positionally without noticing that is how a checker ends up
# comparing the rank cap against the food column and reporting a cap of 18.
_LEAN_ROW = bool(re.search(r'ECONOMY = opts\.economy === "full" \? "full" : "lean"', js))
for i, name in enumerate(["Settlement", "Kingdom", "Empire", "Civilization"], start=1):
    cols = 4 if _LEAN_ROW else 5
    r = re.search(rf"{name}" + r"\s+(\d+)" * cols, rules)
    check(bool(r), f"cannot find the {name} row of the tier table")
    if r:
        vals = [int(x) for x in r.groups()]
        u, ml = vals[0], vals[1]
        # lean: units, meld, cap, wall.  full: units, meld, food, cap, wall.
        cap = vals[2] if _LEAN_ROW else vals[3]
        wall = vals[3] if _LEAN_ROW else vals[4]
        check(u == UNITS[i], f"{name} prints {u} units, engine has {UNITS[i]}")
        check(ml == MELD[i], f"{name} prints meld limit {ml}, engine has {MELD[i]}")
        if not _LEAN_ROW:
            check(vals[2] == FOOD[i], f"{name} prints food {vals[2]}, engine has {FOOD[i]}")
        check(cap == CAPS[i], f"{name} prints cap {cap}, engine has {CAPS[i]}")
        check(wall == WALLS[i], f"{name} prints wall {wall}, engine has {WALLS[i]}")

# WHICH ECONOMY IS PRINTED. Read here because four separate checks below
# change shape with it; the paragraph that enforces its absence is at the
# bottom of the file with the other v0.26 blocks.
LEAN = bool(re.search(r'ECONOMY = opts\.economy === "full" \? "full" : "lean"', js))
# WHERE MOVEMENT COMES FROM. Off the ladder as of v0.26: the engine reads
# opts.cardMoves and defaults to "meld", one step per card played. The board
# then prints no MOVES column, so it must not gloss the term either - and the
# check below asked for the gloss unconditionally, which failed the build on a
# board that was right. Read from the engine so there is one source for it.
MELD_MOVES = bool(re.search(r'CARD_MOVES = opts\.cardMoves === "ladder" \? "ladder" : "meld"', js))

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

# 3. ascension coins - only when there are any
if not LEAN:
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

# THE ROUND AND THE TURN LEFT THE BOARD FOR THE PLAYER AID, so the checks
# follow them. What has to be true is that the printed set says these things
# ONCE, in the document a player can pick up — not that the board repeats them
# under everybody's units.
board_txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", board))
aid_file = HERE / "Blink-player-aid.html"
aid_txt = (re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", aid_file.read_text(encoding="utf8")))
           if aid_file.exists() else "")
check(bool(aid_txt), "the player aid has not been built — run build_aid.py")
for step in ["Declare A", "highest total wins", "spend in that order"]:
    check(step.lower() in aid_txt.lower(),
          f"the aid's round order is missing: {step}")

# ...AND IN THAT ORDER. The three checks above only ask whether the words are
# on the sheet, so the aid could list the whole round backwards and pass. That
# nearly mattered: v0.26 moved the declare step from before the melds to after
# the reveal, and the aid's line was rewritten by hand with nothing checking
# that it had been. The engine decides this, so read it from there.
a_timing = re.search(r'opts\.aTiming === "blind" \? "blind" : "(\w+)"', js)
check(bool(a_timing), "cannot find the engine's A_TIMING default")
if a_timing and a_timing.group(1) == "afterReveal":
    low = aid_txt.lower()
    i_declare, i_reveal = low.find("declare a"), low.find("turn over together")
    check(i_declare > i_reveal > -1,
          "the engine declares A after the melds are turned over, but the aid's "
          "round order still puts the declare step first")
    check("blind" not in rules.lower().split("glossary")[0],
          "the rulebook still calls the A declaration blind, but the melds are "
          "face up before anyone declares")
check("ROUND" not in board_txt,
      "the round order is back on the player board — it belongs on the aid")

# The map phase is the half a player forgets, and every item in it is a rule
# the engine enforces — so the board's turn menu is checked against the
# engine's own numbers rather than trusted.
# WHETHER TERRAIN IS SCORED AT ALL, and if so under which of the two rules.
#
# "majority" reads as most units, which is the engine's OTHER option; "area"
# scores the largest connected stretch, which the rulebook calls dominance. As
# of v0.26 the default is "off" — dominance left the base game, because map
# objectives pay for the same behaviour and two rules pricing one behaviour is
# how a player does the arithmetic twice and feels neither.
#
# The regex reads the ternary the engine actually writes rather than the older
# `opts.majority || "area"` idiom. It matched nothing after the rewrite, and
# the check said only "cannot find the engine's MAJORITY default" — which is
# the right failure, but it is worth noting it took a REGEX to notice that a
# scoring rule had been removed.
maj = re.search(r'\["off", "area", "units"\]\.includes\(opts\.majority\)\s*'
                r'\?\s*opts\.majority\s*:\s*"([a-z]+)"', js)
check(bool(maj), "cannot find the engine's MAJORITY default")
if maj and maj.group(1) == "area":
    check("majority" not in board_txt.lower(),
          "the board says terrain MAJORITY, but the engine scores the largest "
          "connected stretch — majority is the other rule")
    check(re.search(r"biggest connected stretch", board_txt),
          "the board does not say the terrain point is the biggest connected stretch")
    check("majorit" not in rules.lower(),
          "the rulebook says terrain majority, but the engine scores area")
elif maj and maj.group(1) == "off":
    # Nothing scores terrain any more, so nothing printed may promise it. A
    # scoring line nobody deleted is worth more points on paper than in the
    # game, which is the worst kind of wrong: the table adds them up and the
    # app does not.
    # The AID is in this list because it is the sheet on the table when the
    # scores are added up. The board and the rulebook were checked and the aid
    # was not, which is how a removed scoring rule could have survived in the
    # one document a player actually reads at the end of the game.
    for name, txt in (("player board", board_txt), ("rulebook", rules),
                      ("player aid", aid_txt)):
        check("majorit" not in txt.lower(),
              f"the {name} still scores terrain majority, which v0.26 removed")
        check(not re.search(r"dominat|dominanc", txt, re.I),
              f"the {name} still scores terrain dominance, which v0.26 removed")
        # ...AND THE SAME RULE WITHOUT ITS NAME. The two checks above look for
        # the WORD, and the player aid never used it: it said "3 per terrain",
        # which is the rule spelled as arithmetic, on the one sheet that is on
        # the table while the scores are added up. It survived both checks and
        # the rulebook rewrite, and would have shipped. Anything that pays
        # points FOR A TERRAIN is the rule, whatever it is called.
        check(not re.search(r"\d\s*(?:points?|pts?|/)?\s*(?:per|a|each)\s+terrain",
                            txt, re.I),
              f"the {name} still pays points per terrain, which v0.26 removed "
              f"(it does not have to say 'dominance' to be the same rule)")

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
sys.path.insert(0, str(HERE))
from aid_data import card_uses as _cu          # noqa: E402
card_uses_for_check = _cu("", "", "", "")
check(bool(obj_sec), "the rulebook has no map objectives section")
check(bool(perk_sec), "the rulebook has no perks section")

n_obj = len(re.findall(r'\["[A-Z][a-z]+[^"]*",\s*"(?:mountain|forest|plains|ocean)"', js))
check(n_obj > 0, "cannot find the objective cards in app/engine.js")
words = {12: "twelve", 6: "six", 8: "eight", 10: "ten", 14: "fourteen"}
check(words.get(n_obj, str(n_obj)) in obj_sec,
      f"section 12 does not say there are {n_obj} objective cards")
# WHAT AN OBJECTIVE PAYS, read from whichever rule the engine is printing.
# `points: 4` on the card is the "once" rule's figure and is no longer the
# printed one, so checking it against the book asked section 12 for a number
# the game had stopped using.
obj_rule = re.search(r'OBJ_SCORING = \[[^\]]*\]\s*\n?\s*'
                     r'\.includes\(opts\.objectiveScoring\) \? opts\.objectiveScoring '
                     r': "(\w+)"', js)
check(bool(obj_rule), "cannot find the engine's objective scoring rule")
if obj_rule and obj_rule.group(1) == "perInstance":
    per = re.search(r"OBJ_PER = opts\.objectivePer === undefined \? (\d+)", js)
    check(bool(per), "cannot find the engine's per-instance objective value")
    if per:
        check(f"{per.group(1)} points" in obj_sec,
              f"section 12 does not print an objective as worth {per.group(1)} "
              f"points an arrangement")
    check(re.search(r"each arrangement|every such arrangement", obj_sec, re.I),
          "section 12 does not say an objective pays for EACH arrangement \u2014 "
          "which is the whole of the change from paying once")
    check(not re.search(r"does not pay twice", obj_sec, re.I),
          "section 12 still says building the pattern twice does not pay twice")
else:
    pts = re.search(r"points:\s*(\d+)", js)
    check(bool(pts) and f"{pts.group(1)} points" in obj_sec,
          f"section 12 does not print an objective as worth {pts and pts.group(1)} points")
for mode in ["Secret", "Open", "Keep both"]:
    check(mode in obj_sec, f"the objectives module is missing the {mode} mode")
# The engine went from `opts.objectives || "off"` to a whitelist ternary when
# v0.26 added the "showone" deal, and this regex matched neither the new shape
# nor anything else - so it reported that objectives were no longer off by
# default, which was false. It reads the whitelist form now.
# MAP OBJECTIVES ARE BASE GAME IN v0.26 and this check has flipped with them.
# They have to be: dominance was removed because objectives pay for the same
# behaviour, so with both off the printed game scores nothing at all for the
# SHAPE of what a player holds - and the printed board already lists them
# under SCORING.
modes = re.search(r'OBJECTIVES_MODE = \[[^\]]*\]\s*\n?\s*\.includes\(opts\.objectives\)'
                  r'\s*\?\s*opts\.objectives\s*:\s*"([a-z]+)"', js)
check(bool(modes), "cannot find the engine's objectives default")
if modes:
    check(modes.group(1) != "off",
          "map objectives are off by default, so the printed game scores nothing "
          "for the shape of what you hold and the board's SCORING block lies")
    check(not re.search(r"\bA module\b", obj_sec),
          "section 12 still calls map objectives a module, and the engine deals "
          "them in every game")

# HOW MANY PERKS RUN AT ONCE, and does the book say the same number.
#
# v0.26 runs exactly one, armed at the recycle. The old rule ran every perk
# whose slot the row reached, so a full row ran four - and the difference is
# invisible in a rulebook that just says a perk "wakes up when its slot holds
# a card", which is true under both and complete under neither.
perk_rule = re.search(r'PERK_RULE = opts\.perkRule === "depth" \? "depth" : "(\w+)"', js)
check(bool(perk_rule), "cannot find the engine's PERK_RULE default")
if perk_rule and perk_rule.group(1) == "one":
    check(re.search(r"exactly one perk runs at a time", rules, re.I),
          "the engine runs one perk at a time and the rulebook does not say so")
    check(re.search(r"keeps running until your next recycle", rules, re.I),
          "the rulebook does not say an armed perk survives losing the card "
          "that unlocked it \u2014 which is the whole point of the change")
    check(not re.search(r"works for the rest of the\s+game until you spend the card", rules, re.I),
          "the rulebook still describes the v0.25 perk rule (a perk runs until "
          "you spend the card under it)")



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

# the aid sets it in small caps with CSS, so the markup reads "Your turn"
check("your turn" in aid_txt.lower(),
      "the player aid does not say what a turn may contain")
# BOTH halves, and not as one phrase: the wording moved once and the check
# followed it, which is a check that tests the wording rather than the rule.
check("twice" in aid_txt,
      "the aid no longer says research is twice a turn")
check(re.search(r"1 (gold )?then 2|1 then 2 gold", aid_txt),
      f"the aid does not print the 1-then-2 research price (engine default "
      f"{re.search(chr(34) + 'twice' + chr(34), js) and 'twice'})")
# The board's job is now to name its own parts, so THAT is what is pinned.
_TERMS = ["MELD", "BUY UP TO", "RESERVE", "VICTORY ROW"]
if not MELD_MOVES:
    _TERMS += ["MOVES"]
if not LEAN:
    _TERMS += ["FOOD", "ASCENSION"]
for term in _TERMS:
    check(term in board_txt, f"the board no longer glosses its own term: {term}")
# "MV" and the meld chip looked like the same small numbered box from across a
# table, which is a poor way to draw the two numbers a player uses most. MOVES
# is spelled out now, and MELD is a fan of that many cards.
check("MV" not in board_txt,
      "the board is abbreviating MOVES again — it reads as another chip")
for item in ["SETTLE", "EXPLORE", "ATTACK", "CASH", "MOVE", "RESEARCH",
             "FORTIFY", "COLONY"]:
    check(item in aid_txt, f"the aid's turn menu is missing: {item}")
# the unit slots, counted per row: this is the component players actually load
import collections
rows = collections.Counter()
for c in re.finditer(r'<circle[^>]*cy="([\d.]+)"[^>]*r="6.50"', board):
    rows[round(float(c.group(1)), 1)] += 1
drawn = [n for _, n in sorted(rows.items())]
check(drawn == UNITS, f"the board draws {drawn} unit slots per tier, engine has {UNITS}")

# the meld fan: one small card per card you may play, counted off the sheet
fans = re.findall(r'<g transform="rotate\([^"]*"><rect[^>]*width="7\.0"', board)
melds_js = [int(m) for m in re.findall(r'\["\w+", \d+, (\d+),', js)]
check(len(fans) == sum(melds_js),
      f"the board fans {len(fans)} cards across the five tiers; the engine's "
      f"meld limits total {sum(melds_js)}")
# A tier NAME points at the reserve it governs - one lead line per row - and a
# single faint arrow runs down the column to say which end you take from. That
# last rule is the only one on this board with no number to print, so if the
# arrow goes it goes silently.
leads = re.findall(r'<path d="M[\d.]+ [\d.]+ L[\d.]+ [\d.]+" fill="none" '
                   r'stroke="#B9B4A8" stroke-width="0\.4"', board)
check(len(leads) == len(UNITS),
      f"{len(leads)} tier names point at their reserve row; there are {len(UNITS)} tiers")
check(re.search(r'<path d="M[\d.]+ [\d.]+ L[\d.]+ [\d.]+ L[\d.]+ [\d.]+" '
                r'fill="none" stroke="#B9B4A8" stroke-width="0\.6"', board),
      "the reserve has lost the arrow that says which end to take units from")

# CAP is drawn as the INDEX CORNER of a card, one per tier, each carrying its
# own rank. A bare number was the one column on this board with no shape at all.
corners = re.findall(r'<path d="M[\d.]+ [\d.]+ L[\d.]+ [\d.]+ Q[^"]*"\s*'
                     r'fill="none" stroke="#2A2E2B"', board)
check(len(corners) == len(CAPS),
      f"the board draws {len(corners)} rank corners for {len(CAPS)} tiers")
# The HEADING, not just the glossary: reverting the column label alone left the
# explanatory line behind and the first version of this check passed anyway.
check(not re.search(r">\s*CAP\s*<", board),
      "the board still heads the rank column CAP - the app calls it 'buy up to'")
check("BUY UP TO" in board_txt,
      "the rank column has lost its heading")

# ...and the count is printed on the top card of each fan, so the number can be
# read without counting the cards
for limit in melds_js:
    check(re.search(rf'<rect[^>]*width="7\.0"[^>]*/>\s*<text[^>]*>{limit}</text>',
                    board),
          f"the meld fan for a limit of {limit} does not carry the number on its "
          "top card")

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
# THE FIGURES TEACH TOO, and check_figs.py only measures geometry — it cannot
# see that a drawing is of the previous edition. The combat figure went a whole
# version showing a gold coin being paid and the caption "one defender removed",
# both rules that had already been replaced, and every text-level check above
# passed the whole time because none of them look inside an <svg>.
figs = json.load(open(HERE / "figs.json"))

# ---- EVERY PICTURE OF THE BOARD SHOWS EVERY NUMBER ON IT --------------------
#
# A tier prints six things and they only work read together: the meld you may
# play, the units it holds, the free moves, the food, the highest rank you may
# BUY and the wall your ground HOLDS at. Each representation had been built at a
# different time and each was missing a different one - the tier table in the
# rulebook had the cap and not the wall, and the board figure had the wall and
# not the cap, so a reader who checked one against the other found neither
# complete. Nothing above catches that, because each document was internally
# consistent. This asks all of them for the whole ladder.
board_fig = figs.get("board", "")
fig_nums = re.findall(r"<text[^>]*>([^<]*)</text>", board_fig)
for cap, wall in zip(CAPS, WALLS):
    check(str(cap) in fig_nums,
          f"the board figure does not print rank cap {cap}")
    check(str(wall) in fig_nums,
          f"the board figure does not print the wall {wall}")
    check(f">{wall}<" in board,
          f"the printed player board does not show the wall {wall}")
    check(str(wall) in aid_txt,
          f"the player aid does not show the wall {wall}")
_raw_for_table = (HERE / RULES_HTML).read_text(encoding="utf8")
tier_table = _raw_for_table[_raw_for_table.find("<th>Tier</th>"):]
tier_table = tier_table[:tier_table.find("</table>")]
# NO "Free moves" HEADING: movement comes from the meld in v0.26, so a column
# for it on the ladder would be a number that decides nothing.
_HEADS = ["Units", "Meld limit", "Rank cap", "Wall"]
if not LEAN:
    _HEADS.insert(3, "Food per recycle")
for head in _HEADS:
    check(f">{head}<" in tier_table,
          f"the rulebook's tier table has no {head} column")
for wall in WALLS:
    check(f">{wall}<" in tier_table,
          f"the rulebook's tier table does not print the wall {wall}")
combat_fig = figs.get("combat", "")
fig_text = " ".join(re.findall(r"<text[^>]*>([^<]*)</text>", combat_fig))
check("attack" in fig_text and "defence" in fig_text,
      "the combat figure does not show two sides to a fight")
check(re.search(r"\d \+ \d = \d+", fig_text),
      "the combat figure does not show the ground added to the defender")
check("takes the ground" in fig_text,
      "the combat figure does not show the winner taking the tile")
check("#E8C25A" not in combat_fig,
      "the combat figure still draws a gold coin — the duel charges none")
for terr in ("forest", "mountain"):
    if terr.capitalize() in fig_text:
        check(f"+ {def_js[terr]}" in fig_text or f"+{def_js[terr]}" in fig_text,
              f"the combat figure names {terr.capitalize()} without its "
              f"+{def_js[terr]}")

# THE FRONTIER PAYS, and the rank it pays up to is a number that exists twice.
frontier = re.search(r'FRONTIER = \[[^\]]*\]\s*\.includes\(opts\.frontier\)\s*'
                     r'\?\s*opts\.frontier\s*:\s*"(\w+)"', js, re.S)
check(bool(frontier) and frontier.group(1) == "low",
      "the engine no longer pays for exploring with a low card by default")
rank = re.search(r"FRONTIER_RANK = opts\.frontierRank \|\| (\d+)", js)
check(bool(rank), "cannot find the frontier rank in app/engine.js")
if rank:
    check(f"rank {rank.group(1)} or under" in rules,
          f"section 06 does not say the frontier pays at rank {rank.group(1)} or under")
    # and the boundary has to be the starting deck / upgrade line, or the rule
    # stops explaining itself
    check(int(rank.group(1)) == 10,
          "the frontier rank is no longer the starting-deck boundary")

# WHOSE CARDS FIGHT. The first duel asked the attacker for a card from hand as
# well as the meld card they had already spent, which is not what anybody
# expects and left the rank of the spent card doing nothing at all. Both halves
# are pinned, because the engine and the book drifted apart here once already.
check(re.search(r"\*_duelCard\(q, role, tile, against(?:, by)?(?:, floor)?\)", js),
      "the defender is no longer told what they are answering")
check("_duelCard(p, \"attack\"" not in js,
      "the attacker is being asked for a card from hand again")
check(re.search(r"attack is the card you spent", rules, re.I),
      "section 06 does not say the spent card IS the attack")

# THE FORTIFICATION is the rule most rewritten in this game — absorb, then the
# assault, and now the WALL — and each time the book and the engine drifted
# apart for a version. Every half of it is pinned.
#
# The wall is a LADDER: two under the tier's rank cap, so 10/12/14/16/18. And
# it is a FLOOR, not a substitute — the defender may still answer with a better
# card, and a wall must never make its owner weaker than the card they held.
check(re.search(r'opts\.fortify\s*\?\s*opts\.fortify\s*:\s*"wall"', js)
      or re.search(r'\.includes\(opts\.fortify\)\s*\?\s*opts\.fortify\s*:\s*"wall"', js),
      "fortify no longer defaults to the printed wall rule")
check(re.search(r'opts\.wallRank === undefined \|\| opts\.wallRank === "cap"', js),
      "a wall no longer climbs with the tier by default")
check(re.search(r"opts\.wallOffset === undefined \? -2", js),
      "the wall ladder is no longer two under the rank cap")
check(re.search(r"c\.r > coin\.r", js),
      "the wall is no longer a floor — the defender's better card must still fight, "
      "and it must be compared against the coin's own ladder value")
for phrase, why in [
    ("wall", "section 07 never names the wall"),
    ("10", "section 07 does not print the ladder"),
    ("floor, not a substitute",
     "section 07 does not say a wall is a floor rather than a substitute"),
    ("higher of the two",
     "section 07 does not say the higher of wall and card fights")]:
    check(phrase.lower() in rules.lower(), why)
# ...and the figure has to show both halves of it: what bounces, what breaks
fort_text = " ".join(re.findall(r"<text[^>]*>([^<]*)</text>", figs.get("fortify", "")))
check("bounces" in fort_text, "the fortify figure no longer shows a dealt card bouncing")
check("breaks it" in fort_text, "the fortify figure no longer shows a researched card breaking a wall")
check("FLOOR" in fort_text, "the fortify figure does not say the wall is a floor")
check("unit survives" not in fort_text,
      "the fortify figure still promises the unit survives — a coin no longer does that")

# THE TERRAIN FIGURE carries the two numbers that decide every fight and every
# settlement, once per terrain, and it prints the defence bonus twice — as the
# rule ("+2") and as the thing a player actually needs ("beat them by 3"). Two
# renderings of one fact is two chances to be wrong, so both are read back.
ter_text = " ".join(re.findall(r"<text[^>]*>([^<]*)</text>", figs.get("terrain", "")))
for terr in ("plains", "ocean", "forest", "mountain"):
    seg = ter_text[ter_text.find(terr.capitalize()):]
    seg = seg[:120]
    check(bool(seg), f"the terrain figure has no {terr.capitalize()} column")
    holds = holds_js[terr]
    check(f"{holds} unit" in seg,
          f"the terrain figure does not give {terr.capitalize()} its {holds}-unit limit")
    bonus = int(def_js[terr])
    check(f"+{bonus}" in seg,
          f"the terrain figure does not give {terr.capitalize()} defence +{bonus}")
    check(f"beat them by {bonus + 1}" in seg,
          f"the terrain figure says the wrong margin for {terr.capitalize()}: "
          f"+{bonus} means beating them by {bonus + 1}")
# and the sea's own rule, which is the reason this figure is not just a table
check("ANY terrain" in ter_text and "once a turn" in ter_text,
      "the terrain figure no longer shows the water advantage")

# THE WORKED ROUND is two figures and a page of prose, and all three can drift
# apart from each other and from the engine. The first draft of the map figure
# drew three Mountains in a ROW while the setup three lines above it said
# triangle.
#
# The layout is compared against the engine's own STARTS[3] rather than against
# section 03, so the picture, the printed setup and the simulator are one fact.
starts3 = re.search(r"3:\s*\[\[(.*?)\]\],\s*\[\[(.*?)\]\]\]", js)
check(bool(starts3), "cannot find the three-player start in app/engine.js")
if starts3:
    want = set()
    for group in starts3.groups():
        for pair in re.findall(r"(\d+),\s*(\d+)", group):
            want.add((int(pair[0]), int(pair[1])))
    # HERE, not a bare name: this script has to work from any directory,
    # and build_pdfs.sh happens to run it from source/ so a relative path
    # passed there and crashed for anyone standing at the project root.
    fig_src = (HERE / "build_figs.py").read_text(encoding="utf8")
    wm = fig_src[fig_src.index("def worked_map():"):fig_src.index('F["worked_map"]')]
    drawn = {(int(a_), int(b_)) for a_, b_ in
             re.findall(r"\((\d+),\s*(\d+)\)", wm[:wm.index("NEW =") + 40])}
    check(want <= drawn,
          "the worked-round map does not draw the engine's three-player start: "
          f"missing {sorted(want - drawn)}")

# The trick figure carries arithmetic, and arithmetic in a drawing is never
# re-checked by anybody. Every sum printed on it has to be true, and the meld
# marked as the winner has to be the largest.
trick_text = " ".join(re.findall(r"<text[^>]*>([^<]*)</text>", figs.get("trick", "")))
totals = []
for expr in re.findall(r"(\d+(?: \+ \d+)+) = (\d+)", trick_text):
    parts = [int(x) for x in expr[0].split(" + ")]
    check(sum(parts) == int(expr[1]),
          f"the trick figure prints {expr[0]} = {expr[1]}, which is {sum(parts)}")
    totals.append(sum(parts))
check(len(totals) >= 2, "the trick figure shows fewer than two melds to compare")
loose = [int(x) for x in re.findall(r"(?<![+=] )\b(\d+)\b(?! [+=])", trick_text)]
check(totals and max(totals) == max(totals + [t for t in loose if t < 21]),
      "the trick figure's winning meld is not the highest total shown")
check("winner" in trick_text and "meld" in trick_text,
      "the trick figure does not say the winner's die shows the meld size")

# The market figure told the same kind of lie: it offered a CHOICE of which
# position to bury, years after the rule became "cover the highest rank, nobody
# chooses". Both halves are checked, because "highest" appearing is not proof
# that "any position you like" has gone.
market_text = " ".join(re.findall(r"<text[^>]*>([^<]*)</text>", figs.get("market", "")))
check("highest rank" in market_text,
      "the market figure does not say a draw covers the highest rank")
check("any position you like" not in market_text,
      "the market figure still offers a choice of which position to bury")

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
check(bool(rank) and f"rank {rank.group(1)} or under" in tut,
      f"the tutorial does not teach the frontier coin at rank {rank and rank.group(1)}")
check("the tile is yours" in tut, "the tutorial does not say a won duel takes the ground")
for terr in ("plains", "ocean", "forest", "mountain"):
    check(f"{terr.capitalize()} +{def_js[terr]}" in tut
          or f"{terr.capitalize()} and Ocean +{def_js[terr]}" in tut
          or re.search(rf"{terr.capitalize()}[^.]{{0,30}}\+{def_js[terr]}", tut),
          f"the tutorial does not give {terr.capitalize()} its +{def_js[terr]}")
check("lowest-ranked card in your hand" in tut,
      "the tutorial does not teach the lowest-card retire")

# --- the starting map is as far apart as the rulebook says it is -----------
# The book claimed "every start exactly three tiles from every other". At four
# players it is not: five of the six pairs are three apart and one is five.
# Nobody caught it because each document was internally consistent, which is
# this project's whole failure mode. So the distance is computed from the
# layout the figure actually draws, and the claim is checked against it.
def _hex_distance(a, b):
    """Ring-by-ring search on the same offset grid build_figs draws."""
    def nbrs(c, r):
        odd = r & 1
        return [(c + 1, r), (c - 1, r), (c + odd, r - 1), (c - 1 + odd, r - 1),
                (c + odd, r + 1), (c - 1 + odd, r + 1)]
    if a == b:
        return 0
    front, seen, n = [a], {a}, 0
    while front and n < 12:
        n += 1
        nxt = []
        for cell in front:
            for q in nbrs(*cell):
                if q == b:
                    return n
                if q not in seen:
                    seen.add(q)
                    nxt.append(q)
        front = nxt
    return 99


# Read the layouts out of the figure builder rather than keeping a second copy
# here. A constant duplicated across two files is how the last four of these
# bugs happened.
_figsrc = (HERE / "build_figs.py").read_text(encoding="utf8")
_block = re.search(r"LAYOUTS = \[(.*?)\n    \]", _figsrc, re.S)
check(_block is not None, "check_rules cannot find LAYOUTS in build_figs.py")
_LAYOUTS = {}
if _block:
    for _line in re.finditer(r'"(\d) players", \[(.*?)\],\s*\[(.*?)\]\)',
                             _block.group(1).replace("\n", " "), re.S):
        _LAYOUTS[int(_line.group(1))] = [
            tuple(int(v) for v in m.groups())
            for m in re.finditer(r"\((\d+), (\d+)\)", _line.group(3))]
check(sorted(_LAYOUTS) == [2, 3, 4],
      f"check_rules read {sorted(_LAYOUTS)} player counts out of build_figs, wanted 2/3/4")
_dists = []
for _n, _pls in _LAYOUTS.items():
    for _i in range(len(_pls)):
        for _j in range(_i + 1, len(_pls)):
            _dists.append(_hex_distance(_pls[_i], _pls[_j]))
_lo, _hi = min(_dists), max(_dists)
check(_lo == 3, f"the closest two starts are {_lo} tiles apart, not 3")
check("no start closer than three tiles" in rules,
      "the rulebook no longer states the minimum distance between two starts")
check("exactly three tiles from every other" not in rules,
      f"the rulebook claims every start is exactly three apart; they run {_lo}\u2013{_hi}")

# --- the objective pattern is a bend, not a row ---------------------------
# The lede said "three tiles in a row" and the section three paragraphs later
# said the ends need not touch each other. Both cannot be true, and the card
# art draws some patterns straight and some bent, which teaches the wrong one.
check("three tiles in a row" not in rules,
      "the rulebook calls an objective three tiles in a row; the ends may sit "
      "anywhere around the middle")
check("a bend counts exactly as a straight line" in rules,
      "the rulebook no longer says a bent objective counts the same as a straight one")


# THE RECYCLE IS A PHASE NOW, and the figure that draws it has to exist. A
# section that promises a flow chart and prints nothing is worse than a
# section that never mentioned one. This sits at the bottom of the file
# because `figs` is not loaded until well below where the rest of the perk and
# objective checks live, and a NameError in a checker reads exactly like a
# failing check to anyone running it.
# THE DRAFT PASSES, read from the engine rather than trusted.
#
# v0.26 changed the draft from "keep four, then six, then eight" to "pass six,
# then four, then two" - the same schedule counted the other way round, but
# the pool is now ten cards every round and a card kept earlier may still be
# passed. Both descriptions are internally sensible, which is precisely why a
# book carrying the old one would not look wrong.
passes = re.search(r"DRAFT_PASSES\(\)\s*\{\s*return \[([0-9,\s]+)\]", js)
check(bool(passes), "cannot find the engine's draft schedule")
if passes:
    nums = [n.strip() for n in passes.group(1).split(",") if n.strip()]
    said = [n for n in nums if n != "0"]
    setup = rules[rules.find("Draft your hand"):][:900]
    for n in said:
        check(re.search(rf"\b{n}\b", setup),
              f"\u00a703 does not mention passing {n} cards, and the engine does")
    check(re.search(r"not\s+locked", setup, re.I),
          "\u00a703 does not say a card kept in an earlier round may still be "
          "passed \u2014 which is the change, not the numbers")

# THE ECONOMY, read from the engine.
#
# v0.26 removed the food bill and the ascension coins together - one switch,
# because removing ascension alone is the worst configuration ever measured
# here. Nothing printed may go on asking for food or promising a coin for
# climbing: a scoring or upkeep rule nobody deleted is worth more on paper than
# in the game, and the table adds it up while the app does not.
#
# The board outlived its own columns by exactly one build during this change:
# the ladder dropped FOOD and ASCENSION and the ON THE BOARD legend went on
# explaining both, so the sheet defined two things a player could not find on
# it. That is what this block is for.
econ = re.search(r'ECONOMY = opts\.economy === "full" \? "full" : "(\w+)"', js)
check(bool(econ), "cannot find the engine's ECONOMY default")
if econ and econ.group(1) == "lean":
    for name, txt in (("rulebook", rules), ("player board", board_txt),
                      ("player aid", aid_txt)):
        # The rulebook keeps ONE paragraph explaining that the rules are gone,
        # so it is allowed to name them - in the past tense, once.
        hits = len(re.findall(r"\bfood\b|\bascension\b", txt, re.I))
        allowed = 2 if name == "rulebook" else 0
        check(hits <= allowed,
              f"the {name} mentions food or ascension {hits} times and v0.26 "
              f"removed both (at most {allowed} allowed here)")
        # `feed` IS ON THIS LIST BECAUSE IT WAS NOT. The first version of this
        # block searched for "food", "ascension", "starve" and "upkeep", and
        # both the rulebook and the aid went on telling players to FEED THEIR
        # POPULATION at every recycle - one as step 2 of the recycle list,
        # pointing at a passage that had been deleted. The rule was removed
        # from the engine, the columns, the table and the prose, and the one
        # word that survived was the imperative a player actually reads.
        check(not re.search(r"\bstarve|\bupkeep\b|per recycle|\bfeed(s|ing)?\b",
                            txt, re.I),
              f"the {name} still tells a player to feed, starve or pay upkeep, "
              f"which v0.26 removed")

# PERKS ARE A MODULE, AND EVERY SURFACE HAS TO SAY SO.
#
# The engine deals none unless asked (`dealPerks(rng, n, opts.perks)` with no
# perks is null), the setup page opens OFF, and section 13 is headed "An
# optional module". What drifts is the places that describe the RECYCLE:
# arming a perk is two thirds of that phase when the modules are on and none
# of it when they are not, and both the rulebook's recycle list and the player
# aid had started teaching it as an ordinary step.
#
# Checked by wording rather than by structure because that is where it went
# wrong: the rule was never base, the prose just stopped mentioning it was not.
# ANCHORED ON THE SECTION ID, not on the first place the word appears. The
# first "Perks" in the book is in the CONTENTS line, and so is the first "The
# recycle" - so a naive find() reads the table of contents and then a thousand
# characters of section 01, which contains neither the claim nor its negation.
# Both checks passed on a rulebook with the wording deliberately removed.
check(re.search(r"optional module", perk_sec, re.I),
      "\u00a713 no longer calls perks an optional module")
recyc = section(raw_rules, "recycle")
check(bool(recyc), "the rulebook has no recycle section to check")
if recyc:
    check(re.search(r"if you are playing with perks", recyc, re.I),
          "the recycle no longer says arming a perk is only for tables playing "
          "with the perks module")
    check(re.search(r"base game a recycle is", recyc, re.I),
          "the recycle no longer says what the BASE game does at this moment, "
          "so a table with no modules cannot tell which steps are theirs")
# THE A4 PICTORIAL AID, against the engine.
#
# It is a SECOND rendering of the folded card's facts - the two share
# aid_data.py so they cannot say different things - plus the A/B/C table,
# which it generates by ASKING app/engine.js at build time rather than by
# repeating it. This block checks the parts it draws itself.
vis_file = HERE / "Blink-aid-visual.svg"
check(vis_file.exists(),
      "the pictorial aid has not been built - run: python3 build_aid_visual.py")
if vis_file.exists():
    # A GENERATED FILE OLDER THAN WHAT GENERATES IT IS LAST WEEK'S ANSWER.
    # Found the hard way: a deliberately broken aid_data.py made the builder
    # exit, the SVG on disk stayed as it was, and every check below happily
    # passed the PREVIOUS build. Exactly the failure the DOM tests had with a
    # stale play page, in a different file.
    _vis_age = vis_file.stat().st_mtime
    for _src in ("build_aid_visual.py", "aid_data.py"):
        _f = HERE / _src
        check(not _f.exists() or _f.stat().st_mtime <= _vis_age + 1,
              f"Blink-aid-visual.svg is older than {_src} - it is not this "
              f"version of the sheet; run: python3 build_aid_visual.py")
    vis = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ",
                                    vis_file.read_text(encoding="utf8")))
    # the five beats, in order
    beats = ["LAY", "REVEAL", "DECLARE", "RANK", "MAP"]
    at = [vis.find(x) for x in beats]
    check(all(i >= 0 for i in at) and at == sorted(at),
          "the pictorial aid does not show the five beats of a round in order")
    # the three questions it exists to answer
    for want in ["A CARD IN YOUR MELD", "A COIN", "A VICTORY-ROW CARD"]:
        check(want in vis, f"the pictorial aid no longer asks about {want}")
    # every card use, every coin use
    for key, _c, _d in card_uses_for_check:
        check(key in vis, f"the pictorial aid is missing the card option {key}")
    # the A/B/C numbers, read from the engine the same way the sheet does
    for band_c in ("2g", "3g", "4g", "5g"):
        check(band_c in vis, f"the pictorial aid does not price C at {band_c}")
    # and it must not describe rules v0.26 removed
    check(not re.search(r"\bfood\b|\bascension\b|\bfeed(s|ing)?\b", vis, re.I),
          "the pictorial aid still mentions food, ascension or feeding")

# ---- SIDE TWO. A two-sided aid whose back is a separate file is a back that
# goes unbuilt and unchecked; the only reason the front stayed honest this long
# is that something read it. So the back is read too, for the four things it
# exists to carry - none of which appeared anywhere on the one-page sheet.
vis2_file = HERE / "Blink-aid-visual-2.svg"
check(vis2_file.exists(),
      "the pictorial aid's SECOND SIDE has not been built - run: "
      "python3 build_aid_visual.py")
if vis2_file.exists():
    _v2age = vis2_file.stat().st_mtime
    for _src in ("build_aid_visual.py", "aid_data.py"):
        _f = HERE / _src
        check(not _f.exists() or _f.stat().st_mtime <= _v2age + 1,
              f"Blink-aid-visual-2.svg is older than {_src}; run: "
              "python3 build_aid_visual.py")
    vis2 = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ",
                                      vis2_file.read_text(encoding="utf8")))
    for want, why in (
        ("WHERE YOUR CARDS GO", "the card loop - the one system with no tell on the table"),
        ("THE RECYCLE", "what happens when a hand runs out"),
        ("MAP OBJECTIVES", "the only points about the SHAPE of the map"),
        ("INCOME", "what a board earns at a recycle"),
    ):
        check(want in vis2, f"side two of the pictorial aid no longer shows "
                            f"{want} - {why}")
    # the objectives are BASE GAME and pay per arrangement: both halves matter
    check(re.search(r"SHOW ONE, KEEP ONE", vis2),
          "side two does not say that one objective is shown and one kept")
    _per = re.search(r"OBJ_PER = opts\.objectivePer === undefined \? (\d+)", js)
    _pts = _per.group(1) if _per else "2"
    check(re.search(rf"{_pts} points for every arrangement", vis2),
          f"side two does not price an objective at {_pts} points an "
          "arrangement, which is what the engine pays")
    # income is a MODULE and must be marked as one, or a base-game table goes
    # looking for a rule it does not have
    check(re.search(r"modules only", vis2, re.I),
          "side two does not mark income and perks as modules only")
    # and the redundancy that prompted the rebuild must not creep back: the
    # four free actions that the coin and victory-row columns already spell out
    for dup in ("stand it on a unit", "take a card at or under"):
        check(dup not in vis2,
              f"side two repeats \"{dup}...\" from the front - that duplication "
              "is what the second side was made to remove")

check(re.search(r"modules only", aid_txt, re.I),
      "the player aid lists the recycle steps without marking which belong "
      "to modules")

if "The recycle" in rules:
    check("recycle" in figs,
          "\u00a709 is called The recycle but there is no recycle figure to draw it")
    check(re.search(r"collect what your board has earned", rules, re.I),
          "\u00a709 no longer says what the recycle is FOR \u2014 it reads as a "
          "housekeeping list again")

# ------------------------------------------------ where a set-aside card goes
#
# A MELD CARD NEVER LEAVES ITS OWNER; only a victory-row card does. The engine
# and the book disagreed about this for the whole of v0.26 - the engine sent
# the set-aside card to the shared market and the book said so in six places,
# including the glossary, while the design had reversed it because a playtester
# found losing the card outright too harsh.
#
# Caught against the ENGINE rather than against a remembered rule: whichever
# pile the engine pushes it onto is the one the book has to name.
m = re.search(r"p\.discard\.push\(aside\)|this\.pile\.push\(aside\)", js)
check(m, "cannot find where the engine puts a set-aside card")
if m:
    to_owner = m.group(0).startswith("p.discard")
    if to_owner:
        check(re.search(r"goes into <strong>your own discard</strong>", raw_rules),
              "the engine returns a set-aside card to its owner's discard and §04 "
              "does not say so")
        check(not re.search(r"set aside[^.]{0,80}shared pile", rules, re.I),
              "§04 still sends the set-aside card to the shared pile, which is "
              "where it stopped going")
        check(re.search(r"A card from your meld\s+never leaves you", raw_rules),
              "the book never states the rule the routing follows — that a meld "
              "card stays with its owner and only a victory-row card leaves")
    else:
        check(re.search(r"set aside[^.]{0,80}shared pile", rules, re.I),
              "the engine sends the set-aside card to the shared pile and the book "
              "says it goes to the player's own discard")

# AND THE RECYCLE MUST NOT DRAW FROM A MARKET NOBODY REFILLS FROM. The market
# is stocked once at setup and read by trade; the recycle is your own discard
# coming back. The book told players to draw from it and to shuffle it, which
# is the rule from before the deck split moved.
# THIS CHECK WAS TOO LITERAL AND LET THE RULE BACK IN. It asked for the exact
# phrase "draw from the shared pile" and passed for weeks while §09's prose said
# "cards other players lost flow back to you", "every player refills to exactly
# ten" and "if it is ever empty when you must draw" - the same rule in four
# other sentences, three paragraphs under a boxed note denying it. The broader
# sweep is at the bottom of this file; this line stays as the narrow case.
check(not re.search(r"draw from the shared pile", rules, re.I),
      "§09 still tells players to refill from the shared pile — the market is "
      "stocked at setup and drawn from by trade, not by the recycle")
# The aid and the tutorial print the same step in fewer words, which is where a
# retired rule survives longest: nobody rereads a card they think is settled.
for _n in ("Blink-player-aid.html", "Blink-first-game.html"):
    if (HERE / _n).exists():
        check(not re.search(r"draw to ten|draw up to ten", text_of(HERE / _n), re.I),
              f"{_n} still tells a player to draw to ten at a recycle; the "
              "discard comes back as ten and nothing is drawn")

# ---------------------------------------------------------------- spoils
#
# THE COIN A WON TILE PAYS (§06). Caught by what the engine DEFAULTS to, not by
# the option existing: `spoils` has had three settings for months and the
# printed one was "none" the whole time. What matters is which one a game
# starts with, so that is what is read.
#
# And the rulebook is caught by the CONDITION, not by the word "spoils": the
# whole point of this rule is that the coin arrives only when the duel empties
# the tile and you settle it. A book that says a won duel pays a coin would be
# a different, measurably worse rule (fighters at 65.7% head to head), and it
# would read as correct to any check looking for the word.
m = re.search(r'this\.SPOILS\s*=.*?:\s*"(\w+)"', js, re.S)
check(m, "cannot find the SPOILS default in app/engine.js")
if m:
    spoils = m.group(1)
    if spoils == "none":
        check(not re.search(r"take <strong>1 gold</strong> from the\s+supply", raw_rules),
              "the engine pays no spoils but §06 tells players to take a coin")
    else:
        check(spoils == "ground",
              f'engine pays spoils "{spoils}"; only "ground" is printed — paying for '
              "every duel won measured at 65.7% head to head, which is compulsory "
              "rather than viable")
        check(re.search(r"take <strong>1 gold</strong>", raw_rules),
              "§06 never tells the player to take the coin a won tile pays")
        check(re.search(r"the tile is simply left empty \(and there are no spoils",
                        raw_rules),
              "§06 does not say the coin is withheld when the tile is emptied but "
              "NOT taken — without that clause the book reads as paying for every "
              "duel won, which is a different and worse rule")
        check(re.search(r"take it: \+1 gold|\+1 gold if you take it", aid_txt),
              "the player aid's ATTACK line does not mention the coin, so the only "
              "thing on the table during a map phase omits the rule that makes "
              "attacking worth doing")
        # AND THE FIGURE. A reader believes a diagram without checking it
        # against the text, so a combat figure that shows a fight paying
        # nothing teaches the rule that was replaced. This one drew the duel,
        # the ground changing hands, and no coin at all for the whole of the
        # day the rule was printed.
        _cf = figs.get("combat", "") if isinstance(figs, dict) else ""
        _cft = html.unescape(re.sub(r"<[^>]+>", " ", _cf))
        check("gold" in _cft.lower(),
              "the combat figure does not show the coin a won tile pays - the "
              "figure teaches the rule, and this one teaches the pre-v0.26 one")

# ---------------------------------------------------------------- glyphs
#
# EVERY CHARACTER THE AIDS PRINT MUST EXIST IN THE FACE THEY ARE SET IN.
#
# The aids embed a LATIN SUBSET of IBM Plex - that is the whole point of
# subsetting, and it is what keeps the print kit small. A character outside it
# does not fail: the renderer quietly borrows some other font for that one
# glyph, so the document looks right in a browser, looks right in the PDF on
# the machine that made it, and prints an empty box on a machine that has no
# suitable fallback. It also drags a third font into a PDF that check_fonts.py
# is meanwhile certifying as Fraunces and IBM Plex only.
#
# Found by rendering the sheet in the REAL face for the first time: the tick,
# the cross, the up arrow in the research icon, "1 \u2192 2" and one minus sign
# were all outside the subset. Four of them had been shipping for weeks.
_metrics = ROOT / "source" / "font_metrics.json"
if _metrics.exists():
    _m = json.loads(_metrics.read_text(encoding="utf8"))
    _have = set()
    for _face in _m.values():
        _have |= set(_face["w"])
    _have |= set(" \n\t")
    for _name in ("Blink-aid-visual.svg", "Blink-aid-visual-2.svg"):
        _f = HERE / _name
        if not _f.exists():
            continue
        _txt = "".join(re.findall(r"<text[^>]*>(.*?)</text>", _f.read_text(encoding="utf8"), re.S))
        _txt = html.unescape(_txt)
        _bad = sorted({c for c in _txt if c not in _have})
        check(not _bad,
              f"{_name} prints " + ", ".join(f"U+{ord(c):04X} ({c})" for c in _bad)
              + " - not in the embedded IBM Plex subset, so it depends on a "
              "font substitution that is not guaranteed and prints as an empty "
              "box where it does not happen. Draw it as a path instead.")

# -------------------------------------------------- every printed document
#
# THE RULEBOOK WAS GUARDED AND ITS COMPANIONS WERE NOT.
#
# check_rules watched the rulebook, the board and the two player aids for rules
# v0.26 removed, and said nothing about the other five documents in the same
# print kit. So while the rulebook was correct, "Your first game" - the booklet
# a new player reads BEFORE the rulebook - was still telling them to put
# ascension coins on their printed spots and to pre-place food on their band's
# slots, on a board that has neither any more. It was published as v0.26 on the
# site. The card-effects sheet still explained effect C as something you take
# "when feeding falls short", and still described effect A as declared blind.
#
# A companion document is not a lesser document: it is the one people read
# first, and it is in the same kit under the same version number. Every built
# HTML file is read here now, and the archived rulebooks are skipped by name
# because a frozen version is SUPPOSED to describe the rules of its own day.
GONE = re.compile(r"\bfood\b|\bascension\b|\bfeed(s|ing)?\b|\bstarv\w+|"
                  r"\bupkeep\b|per recycle\b", re.I)
# Documents allowed to name a removed rule, and why.
GONE_OK = {
    # the variants catalogue exists to describe optional rules, and the full
    # economy is still one of them - it just has to say so, which is checked
    # separately below.
    "Blink-variants.html",
    # the perk tokens print one perk, Granary, whose whole effect is an economy
    # the base game no longer has. It is out of the playable pool and the token
    # says so in its own text, which is checked just below.
    "Blink-perk-tokens.html",
    # NOT PART OF THE KIT. build_pdfs.sh does not run build_deck_spec.py and
    # nothing prints this; it is a v0.24-era proposal about effect D, left on
    # disk. It is skipped rather than repaired because repairing it would imply
    # it is current, and it is not.
    "Blink-deck-with-D.html",
}
for _doc in sorted(HERE.glob("Blink-*.html")):
    _n = _doc.name
    if _n in GONE_OK or re.search(r"-v0\.\d+(-bw)?\.html$", _n):
        continue            # archived rulebooks describe their own day's rules
    if _n.startswith(RULES_HTML.rsplit(".", 1)[0]):
        continue            # the current rulebook has its own checks above
    _t = html.unescape(re.sub(r"<[^>]+>", " ", _doc.read_text(encoding="utf8")))
    _hits = sorted({m.group(0).lower() for m in GONE.finditer(_t)})
    check(not _hits,
          f"{_n} still describes rules v0.26 removed ({', '.join(_hits)}) - it "
          "ships in the same kit under the same version number as the rulebook")

# The Granary token must say it is inert in the printed game, or it is a card
# that gets dealt and does nothing.
_pt = HERE / "Blink-perk-tokens.html"
if _pt.exists():
    _ptt = html.unescape(re.sub(r"<[^>]+>", " ", _pt.read_text(encoding="utf8")))
    if re.search(r"granary", _ptt, re.I):
        check(re.search(r"FULL ECONOMY ONLY", _ptt),
              "the Granary perk token still reads as a live perk, and its whole "
              "effect is an upkeep the printed game does not have")

# And the variants catalogue, which MAY name them, must scope them as options.
_var = HERE / "Blink-variants.html"
if _var.exists():
    _vt = html.unescape(re.sub(r"<[^>]+>", " ", _var.read_text(encoding="utf8")))
    if re.search(r"\bfood\b|\bstarv\w+", _vt, re.I):
        check(re.search(r"needs the full economy", _vt, re.I),
              "Blink-variants.html describes starvation without saying that the "
              "printed economy is lean and nothing can starve in it")

# ------------------------------------------- the market is not a draw pile
#
# THE RULEBOOK SAID BOTH THINGS AT ONCE. §09 carries a boxed note - "you do not
# draw from it to refill" - and three paragraphs below it the prose still said
# "cards other players lost flow back to you" and "every player refills to
# exactly ten... if it is ever empty when you must draw". That is the previous
# version, where a player who matched the leader gave their set-aside card to
# the SHARED pile and came back a card short. v0.26 sends it to their own
# discard, so nothing is ever drawn from the market at a recycle, and the
# engine's top-up loop does not run once in a whole game.
#
# A contradiction inside one section is worse than either rule alone, because a
# player will read whichever paragraph they reach first. These patterns are the
# old rule's fingerprints; if one comes back, so has the contradiction.
for _doc, _txt in [("the rulebook", rules)] + [
        (n, text_of(HERE / n)) for n in ("Blink-first-game.html",)
        if (HERE / n).exists()]:
    # THE PATTERNS HAVE TO BE THE CLAIM, NOT THE WORDS. A first cut matched
    # "refills? from" and promptly failed on the corrected heading, "The market
    # is not what you refill from" - a check that forbids a word cannot tell a
    # rule from its denial. These are shapes that only appear when the retired
    # rule is being asserted.
    for _pat, _what in [
        (r"where every hand\s+refills from",  "calls the market the thing every hand refills from"),
        (r"pile everyone refills from",       "calls the pile the one everyone refills from"),
        (r"draw up to ten from the shared",   "has a recycle drawing from the shared pile"),
        (r"refills? to exactly ten",          "still says players refill to exactly ten"),
        (r"flow back to you",                 "still says other players' cards flow back to you"),
        (r"empty when you must draw",         "still tells players what to do if the pile runs out at a recycle"),
    ]:
        check(not re.search(_pat, _txt, re.I),
              f"{_doc} {_what} — the market is drawn from by TRADE only (\u00a709/\u00a710); "
              "nothing is drawn from it at a recycle")

# ...and it must still say what IS true, or the note has simply been deleted.
check(re.search(r"you do not\s+draw from it to refill", rules, re.I),
      "\u00a709 no longer tells the player that the market is not what they refill from")
# The pile is shuffled once. This is a rule with a visible consequence - what
# you bury in a trade comes round in its own time - and the engine agrees only
# because someone read the book; PILE_SHUFFLE defaulted the other way for a
# while. Ask both sides.
check(re.search(r"shuffled once, at setup, and never again", rules, re.I),
      "\u00a709 no longer prints that the market is shuffled once and never again")
check(re.search(r'PILE_SHUFFLE = opts\.pileShuffle === "recycle" \? "recycle" : "setup"', js),
      "the engine reshuffles the market at every recycle; the rulebook prints "
      "that it is shuffled once, at setup, and never again")

# ============ the four rulings of 23 Sep, and the checks that hold them ======
#
# Each of these was a place where the engine, the rulebook and a printed
# component said three different things and every check passed. What follows
# asks all the sides that disagreed.

# ---- 1. TWO PILES, TWO NAMES ------------------------------------------------
# "The market" named both the face-down stack AND the 3x3 face-up grid, often
# in the same section: setup called the leftover pile the market in step 2 and
# the grid the market in step 6. A player at a table cannot be told that the
# rank cap governs what they may buy "from the market" and also that the market
# is the thing they may not draw from.
#
#   MARKET           = the face-down stack. Trade reaches it. Never shuffled.
#   INNOVATION SPACE = the 3x3 face-up grid. Research reaches it.
check("innovation space" in rules.lower(),
      "the rulebook never names the innovation space - the 3x3 grid research "
      "buys from, which is NOT the market")
for _bad, _why in [
    (r"buy from the market",        "says the rank cap governs buying from the market"),
    (r"3 . 3 grid\s+.{0,3}\s*the market", "still calls the 3x3 grid the market"),
    (r"the market is always the one buried next", "buries cards in the market"),
]:
    check(not re.search(_bad, rules, re.I),
          f"the rulebook {_why} - research reaches the INNOVATION SPACE; the "
          "market is the face-down stack trade reaches")

# ---- 2. A RESEARCHED CARD GOES WHERE THE PLAYER SAYS ------------------------
# The engine put it in the hand with no choice, the handover specified the
# discard with no choice, and the book said hand in §10 and discard in §09.
check(re.search(r'RESEARCH_TO = \["hand", "discard"\]\.includes\(opts\.researchTo\)', js),
      "the engine no longer offers a choice of where a researched card lands")
check(re.search(r':\s*"choose";', js),
      "the engine does not DEFAULT to letting the player choose where a "
      "researched card lands")
check(re.search(r"say where it goes: into your hand.{0,400}into your discard",
                rules, re.S | re.I),
      "§10 does not offer the player the choice of hand or discard")
check(not re.search(r"straight into your hand", rules, re.I),
      "§10 still says a researched card goes straight into your hand - it is a "
      "choice now")
check(not re.search(r"hands you one for your discard", rules, re.I),
      "§09 still says research hands you a card for your discard - it is a "
      "choice now")
check(re.search(r"to your hand or your discard, as you choose", rules, re.I),
      "§09 does not say the researched card goes where the player chooses")

# ---- 3. A FULL VICTORY ROW BUMPS ITS LOWEST TO THE MARKET --------------------
# Three rules at once: the engine refused the research, §10 said discard one of
# the five permanently, §09's note said it bumps. The note won, because it is
# the only one that keeps "nothing ever leaves the game" true.
check("_bumpRow" in js, "the engine has no victory-row bump")
check(not re.search(r"p\.vrow\.length >= 5\) return false", js),
      "the engine still refuses a research outright when the victory row is full")
check(not re.search(r"discard one of the five permanently", rules, re.I),
      "§10 still tells players to destroy a victory card to make room - a full "
      "row bumps its lowest to the market")
check(re.search(r"lowest of the six goes to the bottom of the market", rules, re.I),
      "§10 does not print the bump")
# and the glossary must not still say a spent victory card is simply gone
check(not re.search(r"spent once for an effect, and then are gone", rules, re.I),
      "the glossary still says a spent victory card is gone; it sinks to the "
      "bottom of the market")

# ---- 4. AN OBJECTIVE PAYS PER ARRANGEMENT, AND THE CARD SAYS SO -------------
# The twelve printed cards said 4 and their booklet said "full value once, or
# nothing"; the rulebook and the engine said 2 for EVERY arrangement. The
# number a player reads is the one on the card in their hand, so THAT is the
# one that had to move. Read from the engine, and asked of every surface.
_m = re.search(r"this\.OBJ_PER = opts\.objectivePer === undefined \? (\d+)", js)
check(_m, "cannot find the objective's point value in the engine")
if _m:
    _per = int(_m.group(1))
    check(re.search(rf"pays\s+<strong>{_per}</strong>\s*\n?\s*points for every such arrangement",
                    rules) or re.search(rf"{_per}\s*\n?\s*points for every such arrangement", rules),
          f"§12 does not say an objective pays {_per} for every arrangement")
    _obj = HERE / "Blink-objectives-colour.html"
    if _obj.exists():
        _pts = set(re.findall(r'class="pts">([^<]*)<', _obj.read_text(encoding="utf8")))
        check(_pts == {str(_per)},
              f"the objective CARDS print {sorted(_pts)} points; the engine pays "
              f"{_per} per arrangement - the card in a player's hand is the number "
              "they will use")
    _book = HERE / "Blink-map-objectives.html"
    if _book.exists():
        _bt = text_of(_book)
        check(not re.search(r"full value once", _bt, re.I),
              "the objectives booklet still says an objective scores its full "
              "value once; it pays per arrangement")
        check(not re.search(r"worth 4 points", _bt, re.I),
              "the objectives booklet still prints 4 points an objective")

# ---- 5. THE QUICK REFERENCE'S TIER LINE ------------------------------------
# It printed FOUR numbers a tier under a heading naming THREE things, because
# the free-moves column left the ladder and never left this sentence. Nothing
# checked it: check_rules reads the tier TABLE, and this is prose.
_qr = re.search(r"Melds, rank cap, wall:(.{0,400}?)Read them off", rules, re.S)
check(_qr, "cannot find the quick reference's tier line")
if _qr:
    for _name, _meld, _cap, _wall in zip(
            ["Tribe", "Settlement", "Kingdom", "Empire", "Civilization"],
            MELD, CAPS, WALLS):
        _row = re.search(rf"{_name}\s+([\d,\s]+?)\.", _qr.group(1))
        check(_row, f"the quick reference has no line for {_name}")
        if _row:
            _n = [int(x) for x in re.findall(r"\d+", _row.group(1))]
            check(_n == [_meld, _cap, _wall],
                  f"the quick reference prints {_name} as {_n}; the heading names "
                  f"three things and the engine has {[_meld, _cap, _wall]}")

# ---- 6. A WALL IS A DEFENDER, SO THE GROUND COUNTS --------------------------
# duelWinner adds TERRAIN_DEFENCE to whatever defends, and the wall coin is
# passed to it as the defending card - so a Tribe's wall of 10 holds at 12 on a
# Mountain. The book said "10 at Tribe, rising to 18" and stopped there, and
# then reasoned from it that one dealt rank can break the lowest wall. It
# cannot, on Forest or Mountain.
check(re.search(r"const b = \(dCard \? dCard\.r : 0\) \+ TERRAIN_DEFENCE\[terrain\]", js),
      "the duel no longer adds the terrain to the defender - the rulebook says "
      "it does")
check(re.search(r"plus the terrain's bonus, like any other defender", rules, re.I),
      "§06 does not say the terrain's bonus is added to a wall")
check(not re.search(r"exactly\s*\n?\s*<strong>one</strong> rank in a dealt hand", rules),
      "§07 still claims exactly one dealt rank can break the lowest wall; on "
      "Forest it takes a 12 and on a Mountain a 13, neither of which is dealt")

# ---------------------------------------------------------------- the verdict
#
# THIS HAS TO BE THE LAST THING IN THE FILE.
#
# It was not. `sys.exit` sat two thirds of the way down, and four blocks of
# checks added after it - the recycle figure, the draft schedule, the economy
# and the perks module - were never executed once. They were not wrong; they
# never ran, and a check that never runs prints exactly what a check that
# passes prints. Anything new goes ABOVE this line.
print("\n".join("FAIL: " + f for f in fails) if fails else
      "rulebook agrees with the engine: tiers "
      + "/".join(str(u) for u in UNITS)
      + ", caps " + "/".join(str(c) for c in CAPS)
      + ", meld limits " + "/".join(str(m) for m in MELD)
      + ", the highest-total trick, research twice a turn, effect A adding the card\u2019s rank, the lowest-card retire, B in reach, and a duel defended at "
      + "/".join(defence[k] for k in ("plains", "ocean", "forest", "mountain")))
sys.exit(1 if fails else 0)
