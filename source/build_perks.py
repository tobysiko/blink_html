# -*- coding: utf-8 -*-
"""Print-and-play sheet for the victory row perk tokens.

AN OPTIONAL MODULE, not part of the base rulebook. The rules are in
Blink-perks-module.html (build_perks_module.py), which reads its list of
perks from PERKS below - one list, so the sheet and the document cannot
disagree about what a token does.

Each token is a FOLD-OVER tile: the available face and the spent face sit side
by side on one side of the sheet, and you fold along the middle. That is
deliberate. Duplex registration is the thing print-and-play does worst, and a
two-sided token whose faces are two millimetres out looks broken; folding
removes back-to-front alignment from the problem entirely and comes out double
thickness, which is welcome at token size.

The fold is VERTICAL and folds backwards, so the spent panel ends up behind the
available one, printed side out, reading right-way-up when you turn the token
over. No panel needs rotating.

    python3 build_perks.py   ->  Blink-perk-tokens.html
"""
import pathlib

from version import VTAG

# ---- palette, matching the player board ---------------------------------
INK, SOFT, FAINT = "#2A2E2B", "#6B6F68", "#B9B4A8"
PAPER, PANEL, LINE = "#FBFAF6", "#EFECE3", "#CDC7B8"

# The tokens used to carry a deck name — WONDERS, WORKS, CRAFTS, CUSTOMS. Those
# named a slot, and once the slot became the player's choice they survived as
# flavour. They are gone now, because "WONDERS" beside "CUSTOMS" implies a power
# order this design deliberately removed: a label that teaches something untrue
# is worse than no label.
#
# What replaces it is the one distinction that changes what you DO with the
# token. SPEND perks are used once and turned face down until your hand
# recycles. STANDING perks are rates — they simply run while they are armed,
# and never turn over at all.
KINDS = {
    "spend":    ("#4A6670", "SPEND \u00b7 turn me over"),
    "standing": ("#4F5E4A", "STANDING \u00b7 always on"),
}

# (deck, name, rule). Kept short on purpose: the token carries one line and the
# appendix carries the edge cases.
PERKS = [
    # v0.26 print pass: every token here has to DO something under the printed
    # rules. Siegecraft discounted a gold price on attacks that the duel does
    # not charge, so it now works on the duel itself; Granary paid for an
    # upkeep the printed economy does not have, so it is no longer printed;
    # and the tokens that named "the shared pile" or "the pile of spent cards"
    # now name the market, which is what that pile is called.
    ("spend", "Coercion",
     "Force a rival to spend a victory card on B or C now. "
     "At rank 11+, you choose which card."),
    ("spend", "Displacement",
     "Move one enemy unit to a legal adjacent tile, instead of one of your "
     "own movements."),
    ("spend", "Terracing",
     "One of your tiles may hold one unit above its terrain limit."),
    ("spend", "Pioneering",
     "A tile you lay need touch only ONE tile already on the map, not two."),
    ("spend", "Salvage",
     "When you must set a card aside, set aside a card from your hand "
     "instead: every card of your meld still acts."),
    ("spend", "Roads", "One extra movement in a turn."),
    ("standing", "Navigation",
     "You may take the water advantage more than once a turn."),
    ("spend", "Ramparts",
     "A fortification survives the first time its unit is disturbed. The coin "
     "stays; the next disturbance takes it."),
    ("spend", "Siegecraft",
     "In one attack on Forest or Mountain, the ground adds nothing to the "
     "defender."),
    ("spend", "Outposts",
     "One card may act one tile further out than your reach."),
    ("standing", "Arithmetic",
     "Friends of 10s: any two cards summing to 10, 20 or 30 are a legal meld."),
    ("standing", "Composition",
     "Combination melds: play two or more melds of 2+ cards together as one."),
    ("spend", "Archaeology",
     "Look through the market and swap a card from your hand for one of rank "
     "10 or under; bury yours at its bottom."),
    ("spend", "Diplomacy",
     "When a rival matches your winning meld and loses, YOU choose which of "
     "their cards is set aside."),
    ("spend", "Scholarship",
     "One research may take a card one rank above your rank cap."),
    ("spend", "Foresight",
     "Look at the top card of the upgrade deck before deciding whether to "
     "research."),
    ("spend", "Coinage", "One cashed card pays 2 gold instead of 1."),
    ("spend", "Tribute",
     "When your meld ranks last, take 1 extra gold on top of the usual coin."),
    ("spend", "Markets",
     "Move one face-up card in the innovation space to a different grid "
     "position."),
]

# ---- geometry ------------------------------------------------------------
W, H = 40.0, 40.0                 # finished token, mm
COLS, ROWS = 2, 6                 # 12 a page, less the header row on page 1

CSS = f"""
@page {{ size: A4; margin: 9mm 8mm; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: {PAPER}; color: {INK};
       font-family: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
       -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.sheet {{ width: {COLS * 2 * W}mm; font-size: 0; }}
.pagebreak {{ page-break-after: always; }}

/* One token = two panels side by side with the fold between them. */
.tok {{ display: inline-block; vertical-align: top;
       width: {2 * W}mm; height: {H}mm; position: relative;
       border: .25mm dashed {FAINT}; }}
.face {{ position: absolute; top: 0; height: {H}mm; width: {W}mm;
        padding: 2.4mm 2.6mm; overflow: hidden; }}
.face.up {{ left: 0; }}
.face.dn {{ left: {W}mm; background: {PANEL}; }}
/* The fold itself, with a mark at each end so it cannot be mistaken for a
   cut line — they are the two dashed lines on the sheet and confusing them
   ruins the token. */
.fold {{ position: absolute; left: {W}mm; top: 0; height: {H}mm;
        border-left: .3mm dotted {SOFT}; }}
.fold::before, .fold::after {{ content: ""; position: absolute; left: -1.4mm;
        border-left: 1.4mm solid transparent; border-right: 1.4mm solid transparent; }}
.fold::before {{ top: 0; border-top: 1.8mm solid {SOFT}; }}
.fold::after {{ bottom: 0; border-bottom: 1.8mm solid {SOFT}; }}

.deck {{ font-size: 5.2pt; letter-spacing: .09em; font-weight: 600; }}
.slot {{ font-size: 4.4pt; color: {SOFT}; letter-spacing: .05em;
        float: right; font-weight: 400; }}
.name {{ font-size: 10pt; font-weight: 600; margin: 1.4mm 0 1.2mm;
        line-height: 1.05; }}
.rule {{ font-size: 6.1pt; line-height: 1.32; color: {INK}; }}
.foot {{ position: absolute; left: 2.6mm; right: 2.6mm; bottom: 1.8mm;
        font-size: 4.6pt; color: {SOFT}; letter-spacing: .04em; }}

/* the spent face: same token, obviously off */
.dn .name {{ color: {FAINT}; }}
.dn .deck {{ color: {FAINT}; }}
.spent {{ font-size: 8.4pt; font-weight: 600; letter-spacing: .16em;
         color: {SOFT}; margin-top: 1.2mm; }}
.back {{ font-size: 5.6pt; line-height: 1.3; color: {SOFT}; margin-top: 1.6mm; }}
.bar {{ height: 1.6mm; margin: 0 0 1.4mm; }}

.head {{ width: {COLS * 2 * W}mm; font-size: 0; margin-bottom: 3mm; }}
.head h1 {{ font-size: 12pt; margin: 0 0 1mm; font-weight: 600; }}
.head p {{ font-size: 6.4pt; line-height: 1.45; margin: 0; color: {SOFT};
          max-width: {COLS * 2 * W}mm; }}
.head b {{ color: {INK}; }}
.warn {{ display: inline-block; font-size: 5.4pt; letter-spacing: .12em;
        font-weight: 600; color: {PAPER}; background: {SOFT};
        padding: .8mm 1.6mm; margin-bottom: 1.6mm; }}
"""


def token(kind, name, rule):
    accent, label = KINDS[kind]
    # A STANDING perk never turns over, so its back cannot say SPENT. If one
    # does get flipped, the back is the place to say put me back.
    if kind == "standing":
        big, note = "ALWAYS ON", ("This one never turns over. Leave it face up "
                                  "for as long as it is armed.")
    else:
        big, note = "SPENT", "Turn this back over when your hand recycles."
    return f"""<div class="tok">
  <div class="face up">
    <div class="bar" style="background:{accent}"></div>
    <div class="deck" style="color:{accent}">{label}</div>
    <div class="name">{name}</div>
    <div class="rule">{rule}</div>
    <div class="foot">READY &middot; any of slots 1&ndash;4</div>
  </div>
  <div class="fold"></div>
  <div class="face dn">
    <div class="bar" style="background:{FAINT}"></div>
    <div class="deck">{label}</div>
    <div class="name">{name}</div>
    <div class="spent">{big}</div>
    <div class="back">{note}</div>
    <div class="foot">Blink &middot; {VTAG} &middot; perks module</div>
  </div>
</div>"""


def build():
    per_page = COLS * ROWS
    first = per_page - COLS          # the header takes the top row of page 1
    pages = []
    i = 0
    while i < len(PERKS):
        take = first if i == 0 else per_page
        chunk = PERKS[i:i + take]
        i += take
        pages.append('<div class="sheet">'
                     + "".join(token(*p) for p in chunk)
                     + "</div>")
    head = f"""<div class="head">
  <div class="warn">OPTIONAL MODULE</div>
  <h1>Perk tokens</h1>
  <p>The full rules are in the <b>perks module</b> document. In short: shuffle the
  {len(PERKS)} tokens and <b>deal four to each player</b>. Lay one above each of
  <b>slots 1 to 4</b> of your victory row, face up &mdash; your choice which goes
  where, and it is <b>permanent</b> once a card reaches the row. Slot 5 stays
  empty.<br>
  At each recycle, after income and before you pick up your discard, turn every
  token face up and <b>arm one perk</b> whose slot your row reaches: <b>slot 4 at
  two cards, slot 3 at three, slot 2 at four and slot 1 at all five</b>. Turn the
  armed token sideways. It runs until your next recycle, even if you spend the
  card that unlocked it. <b>SPEND</b> perks turn face down when used;
  <b>STANDING</b> perks never turn over.<br>
  <b>Cutting:</b> the dashed rectangles are cuts. The dotted line down the
  middle of each token, marked with a triangle at each end, is a
  <b>fold</b> &mdash; fold it backwards so both printed faces end up outside,
  and glue.</p>
</div>"""
    pages[0] = head + pages[0]
    globals()["_pages"] = len(pages)
    body = '<div class="pagebreak"></div>'.join(pages)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Blink &middot; perk tokens &middot; {VTAG}</title>
<style>{CSS}</style>
</head><body>
{body}
</body></html>
"""


if __name__ == "__main__":
    out = pathlib.Path("Blink-perk-tokens.html")
    out.write_text(build(), encoding="utf8")
    n_pages = build.__globals__.get("_pages", 0)
    print(f"wrote {out} — {len(PERKS)} tokens on {n_pages} page(s)")
