# -*- coding: utf-8 -*-
"""Print-and-play sheet for the victory row perk tokens.

PROPOSAL. Nothing here is in the engine or the rulebook — see VROW-PERKS.md.
This exists so the idea can be cut out and played with, which is the only way
to find out whether it is any good.

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

# One accent per deck, so a spread of tokens sorts itself by eye.
DECKS = {
    "WONDERS": ("#7B2018", "slot 1", "five cards in the row"),
    "WORKS":   ("#4A6670", "slot 2", "four cards in the row"),
    "CRAFTS":  ("#5E5233", "slot 3", "three cards in the row"),
    "CUSTOMS": ("#4F5E4A", "slot 4", "two cards in the row"),
}

# (deck, name, rule). Kept short on purpose: the token carries one line and the
# appendix carries the edge cases.
PERKS = [
    # --- WONDERS: powerful, interactive. Once per recycle; twice if the card
    #     in slot 1 is rank 11+, which can only have come from the market.
    ("WONDERS", "Coercion",
     "Force a rival to spend a victory card on B or C and discard it. "
     "At rank 11+, you choose which card."),
    ("WONDERS", "Displacement",
     "Move one enemy unit to a legal adjacent tile, instead of one of your "
     "own free moves."),
    ("WONDERS", "Terracing",
     "One of your tiles may hold one unit above its terrain limit."),
    ("WONDERS", "Pioneering",
     "A tile you lay need touch only ONE tile already on the map, not two."),
    ("WONDERS", "Salvage",
     "Take the card set aside against you into your hand, and discard one of "
     "yours to the shared pile instead."),
    # --- WORKS: map-facing, solid
    ("WORKS", "Roads", "One extra free move each turn."),
    ("WORKS", "Navigation",
     "Your water advantage triggers on EVERY sea move, not only the first."),
    ("WORKS", "Ramparts",
     "A fortification survives the first time its unit is disturbed. The coin "
     "stays; the next disturbance takes it."),
    ("WORKS", "Siegecraft",
     "Your attacks on Forest and Mountain cost 1 gold less, to a minimum of 0."),
    ("WORKS", "Outposts",
     "Your reach extends one tile further than the tiles you occupy."),
    # --- CRAFTS: the row, the hand, the market
    ("CRAFTS", "Arithmetic",
     "Friends of 10s: any two cards summing to 10, 20 or 30 are a legal meld."),
    ("CRAFTS", "Composition",
     "Combination melds: play two or more melds of 2+ cards together as one."),
    ("CRAFTS", "Archaeology",
     "Swap a card from your hand for one of rank 10 or under from the pile of "
     "spent cards."),
    ("CRAFTS", "Diplomacy",
     "When a rival matches your winning meld and loses, YOU choose which of "
     "their cards is set aside."),
    ("CRAFTS", "Scholarship",
     "Your rank cap is 1 higher than your tier prints."),
    ("CRAFTS", "Foresight",
     "Look at the top card of the upgrade deck before deciding whether to "
     "research."),
    # --- CUSTOMS: small, economic, frequent
    ("CUSTOMS", "Granary",
     "Pay one less food each recycle, to a minimum of none."),
    ("CUSTOMS", "Coinage", "One cashed card pays 2 gold instead of 1."),
    ("CUSTOMS", "Tribute",
     "Take 1 extra gold whenever your meld ranks last."),
    ("CUSTOMS", "Markets",
     "Move one face-up market card to a different grid position."),
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


def token(deck, name, rule):
    accent, slot, needs = DECKS[deck]
    return f"""<div class="tok">
  <div class="face up">
    <div class="bar" style="background:{accent}"></div>
    <div class="deck" style="color:{accent}">{deck}<span class="slot">{slot}</span></div>
    <div class="name">{name}</div>
    <div class="rule">{rule}</div>
    <div class="foot">READY &middot; needs {needs}</div>
  </div>
  <div class="fold"></div>
  <div class="face dn">
    <div class="bar" style="background:{FAINT}"></div>
    <div class="deck">{deck}</div>
    <div class="name">{name}</div>
    <div class="spent">SPENT</div>
    <div class="back">Turn this back over when your hand recycles.</div>
    <div class="foot">Blink &middot; {VTAG} &middot; proposal</div>
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
  <div class="warn">PROPOSAL &middot; UNTESTED &middot; NOT PART OF THE GAME</div>
  <h1>Victory row perks</h1>
  <p>One deck per victory row slot. A perk is live while its slot holds a card:
  <b>CUSTOMS</b> needs two cards in your row, <b>CRAFTS</b> three,
  <b>WORKS</b> four, <b>WONDERS</b> all five. Deal one token per slot face up at
  setup, shared by everyone. Spend a perk by turning its token over; turn every
  token back when your hand recycles.
  <b>WONDERS</b> may be spent twice between recycles if the card in slot 1 is
  rank 11 or higher.<br>
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
<title>Blink &middot; victory row perk tokens &middot; {VTAG}</title>
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
