# -*- coding: utf-8 -*-
"""THE A4 PICTORIAL PLAYER AID: every stage of a round, and every decision.

The folded 88x63 card is a reference - you look something up on it. This sheet
is a MAP: it answers "what happens next" and, for each of the three things a
player holds, "what are my options". Three questions come up at a table over
and over, and none of them was answerable from one place:

    what can I do with THIS CARD?
    what can I do with THIS COIN?
    what can I do with a card in my VICTORY ROW?

So each gets a panel of its own, drawn as a fan of choices rather than written
as a list, because a list of four things reads as a sequence and these are
alternatives: ONE of them, not all of them in order.

Everything it says comes from aid_data.py, shared with the folded card, and the
A/B/C effect wording is generated from app/engine.js at build time rather than
typed - the bands and the ladder have both moved before, and a card that
describes an effect the engine no longer has is the failure this project keeps
finding.

Run from source/:  python3 build_aid_visual.py
"""
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from aid_data import (ROUND, COIN_USES, VROW_USES, FREE, card_uses, terrain,
                      MELD, FLOW, FLOW_ASIDE, RECYCLE, OBJECTIVES,
                      INCOME)                                       # noqa: E402
from version import VTAG                                                     # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent

INK, SOFT, FAINT = "#2A2E2B", "#6B6F68", "#B9B4A8"
PAPER, PANEL, LINE = "#FBFAF6", "#F1EEE5", "#CDC7B8"
GOLD, FOREST, OCEAN, STONE, RED = "#C9992B", "#37704A", "#256A8C", "#8A837A", "#C0392B"

W, H = 210.0, 297.0                      # A4 portrait, mm
M = 11.0                                 # margin


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def T(x, y, s, size=3.4, anchor="start", col=INK, weight="400", mono=False,
      spacing=None, italic=False):
    fam = ('"IBM Plex Mono",monospace' if mono
           else '"IBM Plex Sans",-apple-system,Helvetica,sans-serif')
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    it = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{col}" '
            f'font-family=\'{fam}\' font-weight="{weight}" '
            f'text-anchor="{anchor}"{sp}{it}>{esc(s)}</text>')


# THE REAL ADVANCE WIDTHS, read straight out of the faces this sheet is set
# in. See gen_metrics.py for how the table is made and why it replaced a
# guessed one: the guess was right on average and wrong per character - "W" is
# 0.891 em and it said 0.72 - so a capital-heavy line overran its box while
# the arithmetic said it fitted. Every text-outside-its-border bug on this
# sheet, and there have been three rounds of them, came from that gap.
_METRICS = json.loads((HERE / "font_metrics.json").read_text(encoding="utf8"))


def text_w(s, size, weight="400", spacing=0.0, mono=False):
    """Advance width in mm, from the font's own metrics.

    `weight` 700 is measured against the 600 face on purpose: only 400, 500
    and 600 exist as files, so 600 is what a renderer actually uses for 700.
    """
    face = "mono400" if mono else ("sans600" if weight in ("600", "700") else "sans400")
    tbl = _METRICS[face]["w"]
    dflt = _METRICS[face]["default"]
    total = 0.0
    for ch in s:
        total += size * tbl.get(ch, dflt) + spacing
    # A HAIR OF HEADROOM, and no more. The widths above are exact; this covers
    # hinting and the renderer's own rounding, which move a long line by well
    # under a percent. It is NOT a fudge factor for a bad estimate any more.
    return total * 1.01


def split(s, w_mm, size, weight="400", mono=False):
    """The lines `s` breaks into inside `w_mm`."""
    lines, line = [], ""
    for word in s.split():
        t = (line + " " + word).strip()
        if text_w(t, size, weight, mono=mono) > w_mm - 0.6 and line:
            lines.append(line); line = word
        else:
            line = t
    lines.append(line)
    return lines


def wrap(x, y, s, w_mm, size=3.0, col=SOFT, lead=None, anchor="start",
         weight="400", mono=False):
    """Returns (svg, lines_used). Width is MILLIMETRES, not characters."""
    lead = lead or size * 1.30
    lines = split(s, w_mm, size, weight, mono)
    out = "".join(T(x, y + i * lead, ln, size, anchor=anchor, col=col,
                    weight=weight) for i, ln in enumerate(lines))
    return out, len(lines)


def head(x, y, title, sub, size=4.6):
    """A section heading with its subtitle placed AFTER it, not under it."""
    out = T(x, y, title, size, weight="600", spacing="0.5")
    if sub:
        out += T(x + text_w(title, size, "600", 0.5) + 5.5, y, sub, 3.2, col=SOFT)
    return out


def panel(x, y, w, h, accent=None, fill=PAPER):
    return (f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'rx="2.2" fill="{fill}" stroke="{accent or LINE}" '
            f'stroke-width="{0.7 if accent else 0.4}"/>')


# ---------------------------------------------------------------- pictograms
def hexgon(cx, cy, r, fill, stroke=None, dash=False):
    pts = []
    for k in range(6):
        import math
        a = math.pi / 180 * (60 * k - 90)
        pts.append(f"{cx + r * math.cos(a):.2f},{cy + r * math.sin(a):.2f}")
    ds = ' stroke-dasharray="1.2 1"' if dash else ""
    return (f'<polygon points="{" ".join(pts)}" fill="{fill}" '
            f'stroke="{stroke or "none"}" stroke-width="0.5"{ds}/>')


def disc(cx, cy, r, fill, stroke=None):
    return (f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{fill}" '
            f'stroke="{stroke or "none"}" stroke-width="0.5"/>')


def coin(cx, cy, r=2.4):
    return (disc(cx, cy, r, "#F0D98A", "#9B7A16")
            + disc(cx, cy, r * 0.5, "none", "#9B7A16"))


def minicard(x, y, w=6.4, h=9.0, col=LINE, fill=PAPER, label=None):
    out = (f'<rect x="{x:.2f}" y="{y:.2f}" width="{w}" height="{h}" rx="1" '
           f'fill="{fill}" stroke="{col}" stroke-width="0.5"/>')
    if label is not None:
        out += T(x + w / 2, y + h / 2 + 1.4, label, 3.6, anchor="middle",
                 col=col, weight="600")
    return out


def tick(cx, cy, r=1.8, col="#37704A"):
    """A DRAWN tick, not U+2713.

    The latin subset of IBM Plex these documents embed has no U+2713 and no
    U+2717, so a tick set as text depended on the renderer silently borrowing
    some other font for that one character - and printed as an empty box
    wherever it could not. Two paths cost nothing and always print.
    """
    return (f'<path d="M{cx - r:.2f} {cy - r * 0.15:.2f} '
            f'L{cx - r * 0.25:.2f} {cy + r * 0.72:.2f} '
            f'L{cx + r:.2f} {cy - r * 0.85:.2f}" fill="none" stroke="{col}" '
            f'stroke-width="{r * 0.42:.2f}" stroke-linecap="round" '
            f'stroke-linejoin="round"/>')


def cross(cx, cy, r=1.6, col="#C0392B"):
    """A DRAWN cross - see tick() for why it is not U+2717."""
    return (f'<path d="M{cx - r:.2f} {cy - r:.2f} L{cx + r:.2f} {cy + r:.2f} '
            f'M{cx + r:.2f} {cy - r:.2f} L{cx - r:.2f} {cy + r:.2f}" '
            f'fill="none" stroke="{col}" stroke-width="{r * 0.44:.2f}" '
            f'stroke-linecap="round"/>')


def up_arrow(cx, cy, h=3.2, col="#256A8C"):
    """A DRAWN up arrow - U+2191 is not in the subset either."""
    w = h * 0.42
    return (f'<path d="M{cx:.2f} {cy + h / 2:.2f} L{cx:.2f} {cy - h / 2:.2f} '
            f'M{cx - w:.2f} {cy - h / 2 + w:.2f} L{cx:.2f} {cy - h / 2:.2f} '
            f'L{cx + w:.2f} {cy - h / 2 + w:.2f}" fill="none" stroke="{col}" '
            f'stroke-width="0.65" stroke-linecap="round" stroke-linejoin="round"/>')


def arrow(x1, y, x2, col=FAINT):
    return (f'<path d="M{x1:.2f} {y:.2f} L{x2 - 1.6:.2f} {y:.2f}" stroke="{col}" '
            f'stroke-width="0.6" fill="none"/>'
            f'<path d="M{x2 - 1.8:.2f} {y - 1.0:.2f} L{x2:.2f} {y:.2f} '
            f'L{x2 - 1.8:.2f} {y + 1.0:.2f} Z" fill="{col}"/>')


def down(x, y1, y2, col=FAINT):
    return (f'<path d="M{x:.2f} {y1:.2f} L{x:.2f} {y2 - 1.6:.2f}" stroke="{col}" '
            f'stroke-width="0.6" fill="none"/>'
            f'<path d="M{x - 1.0:.2f} {y2 - 1.8:.2f} L{x:.2f} {y2:.2f} '
            f'L{x + 1.0:.2f} {y2 - 1.8:.2f} Z" fill="{col}"/>')


# ------------------------------------------------ the A/B/C wording, from js
def effect_bands():
    """Ask the ENGINE what A, B and C say, rather than writing it down here."""
    js = HERE.parent / "app" / "engine.js"
    node = subprocess.run(
        ["node", "-e", f"""
        const E = require({json.dumps(str(js))});
        const g = new E.Game(3, 1, {{ humans: [] }});
        const out = [3, 8, 13, 18].map((r) => {{
          const t = E.effectText(r, {{ meldScore: g.MELD_SCORE, aSumLadder: g.A_SUM_LADDER }});
          return {{ rank: r, a: t.aShort, b: t.bShort, c: t.cShort }};
        }});
        console.log(JSON.stringify(out));
        """], capture_output=True, text=True)
    if node.returncode != 0:
        raise SystemExit("could not ask the engine for the effect text:\n" + node.stderr)
    return json.loads(node.stdout)


# ------------------------------------------------------------------ the sheet
def option_box(x, y, w, key, detail, accent, icon, keycol=None, right=None,
               key_size=3.5, det_size=2.6):
    """One choice in a panel: an icon, a name, and a line or two about it.

    THE BOX IS AS TALL AS ITS TEXT. Fixed heights were how the first build put
    "...into your discard" outside its own border.
    """
    tx = x + 14.5
    tw = w - (tx - x) - 3
    lines = split(detail, tw, det_size)
    h = max(11.6, 6.2 + len(lines) * det_size * 1.28 + 2.2)
    out = (f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
           f'rx="1.6" fill="{PAPER}" stroke="{accent}" stroke-width="0.6"/>')
    out += icon(x + 8.0, y + h / 2)
    out += T(tx, y + 4.6, key, key_size, weight="700",
             col=keycol or accent, spacing="0.2")
    if right:
        # THE PRICE ONLY SHARES THE LINE IF IT FITS. "RESEARCH" and "1, then 2"
        # were drawn from opposite ends of the same 30 mm and overlapped into
        # "RESEARCH, then 2" - a price that read as part of the word.
        need = (text_w(key, key_size, "700", 0.2)
                + text_w(right, 3.1, "700", mono=True) + 6)
        if need <= w - (tx - x) - 3:
            out += T(x + w - 3, y + 4.6, right, 3.1, anchor="end", col=GOLD,
                     weight="700", mono=True)
        else:
            out += T(tx + text_w(key, key_size, "700", 0.2) + 2, y + 4.6,
                     right, 2.9, col=GOLD, weight="700", mono=True)
    out += wrap(tx, y + 8.6, detail, tw, det_size, SOFT)[0]
    return out, h


def sheet():
    b = ""
    y = M + 6

    # ---- masthead
    b += T(M, y, "BLINK", 8.5, weight="700", spacing="0.4")
    b += T(M + text_w("BLINK", 8.5, "700", 0.4) + 5, y,
           "player aid · every stage, every choice", 4.0, col=SOFT)
    b += T(W - M, y, f"rules {VTAG}", 3.4, anchor="end", col=FAINT, mono=True)
    y += 3.0
    b += f'<path d="M{M} {y} L{W - M} {y}" stroke="{INK}" stroke-width="0.7"/>'
    y += 8.5

    # ================================================== 1. THE ROUND
    b += head(M, y, "THE ROUND", "five beats · the table finishes each one before the next")
    y += 4.5
    bw = (W - 2 * M - 4 * 3) / 5
    top = y
    inner = bw - 6
    # the tallest card decides them all, so the row reads as one band
    bh = 0
    for key, what, who in ROUND:
        n1 = len(split(what, inner, 2.9))
        n2 = len(split(who, inner, 2.6))
        bh = max(bh, 11.5 + n1 * 3.8 + 1.6 + n2 * 3.4 + 2.5)
    for i, (key, what, who) in enumerate(ROUND):
        x = M + i * (bw + 3)
        b += panel(x, top, bw, bh, accent=GOLD if i in (2, 4) else None)
        b += disc(x + 5.6, top + 5.6, 3.0, INK)
        b += T(x + 5.6, top + 6.8, str(i + 1), 3.2, anchor="middle",
               col=PAPER, weight="700")
        b += T(x + 10.6, top + 6.9, key, 3.8, weight="700", spacing="0.2")
        w1, n1 = wrap(x + 3, top + 13.0, what, inner, 2.9, INK)
        b += w1
        b += wrap(x + 3, top + 13.0 + n1 * 3.8 + 1.6, who, inner, 2.6, FAINT)[0]
        if i < len(ROUND) - 1:
            b += arrow(x + bw + 0.4, top + bh / 2, x + bw + 2.6)
    y = top + bh + 3.8
    b += T(M, y, "Your hand runs out mid-turn? Recycle at once — the back of this "
                 "sheet says what that means.", 3.0, col=SOFT, italic=True)
    y += 7.5

    # ================================================== 1b. WHAT MAY I LAY?
    # The single largest omission on the one-page sheet: Blink is a
    # trick-taker and nothing on the aid said what a legal meld is. A player
    # could read the whole sheet and still not know they may lay 2-3-3-4-4.
    b += head(M, y, "WHAT MAY I LAY?", "one meld, face down, every round")
    y += 4.8
    mh = 19.0
    b += panel(M, y, W - 2 * M, mh, accent=GOLD)
    b += T(M + 4, y + 6.4, MELD["rule"], 4.4, weight="700", col=GOLD)
    b += T(M + 4 + text_w(MELD["rule"], 4.4, "700") + 4, y + 6.4,
           "· " + MELD["free"], 3.1, col=SOFT)
    # the worked example, in the mono face, with a tick and a cross
    ex = M + 4
    b += tick(ex + 1.8, y + 12.2, 1.8, FOREST)
    b += T(ex + 5, y + 13.4, MELD["ok"], 3.6, mono=True, weight="600")
    # MEASURED IN THE MONO FACE, because that is what these are set in. Sans
    # metrics are narrower, so "2-2-4-4" and "(no 3)" printed touching.
    ex2 = ex + 5 + text_w(MELD["ok"], 3.6, "600", mono=True) + 9
    b += cross(ex2 + 1.6, y + 12.2, 1.6, RED)
    b += T(ex2 + 5, y + 13.4, MELD["bad"], 3.6, mono=True, weight="600", col=SOFT)
    b += T(ex2 + 5 + text_w(MELD["bad"], 3.6, "600", mono=True) + 3, y + 13.4,
           "(" + MELD["why"] + ")", 3.0, col=RED)
    b += T(W - M - 4, y + 6.4, MELD["cap"], 3.1, anchor="end", col=SOFT)
    b += T(W - M - 4, y + 13.4, MELD["win"], 3.1, anchor="end", col=INK, weight="600")
    y += mh + 7.5

    # ================================================== 2. THE THREE DECISIONS
    b += head(M, y, "WHAT ARE MY OPTIONS?", "one of these, never all of them")
    y += 5
    colw = (W - 2 * M - 2 * 5) / 3
    ctop = y
    iw = colw - 6

    def hdr(x, title, icon):
        out = f'<rect x="{x:.2f}" y="{ctop:.2f}" width="{colw:.2f}" height="9.5" ' \
              f'rx="2.2" fill="{PANEL}"/>'
        out += icon(x + 6.0, ctop + 4.9)
        out += T(x + 12.0, ctop + 6.2, title, 3.6, weight="700")
        return out

    heights = []

    # ---------- a card in your meld
    x = M
    body = hdr(x, "A CARD IN YOUR MELD",
               lambda cx, cy: minicard(cx - 2.3, cy - 3.1, 4.6, 6.2, col=INK))
    cy = ctop + 14.5
    body += T(x + 3, cy, "does ONE of —", 3.0, col=SOFT)
    cy += 3.6

    def ic_settle(cx, cy_):
        return hexgon(cx, cy_, 4.0, "#EFE3C4", GOLD) + disc(cx, cy_, 1.7, RED, "#7B2018")

    def ic_explore(cx, cy_):
        return (hexgon(cx - 2.2, cy_, 3.4, "#E4EDE6", FOREST)
                + hexgon(cx + 2.8, cy_, 3.4, "none", FOREST, dash=True))

    def ic_attack(cx, cy_):
        return (hexgon(cx, cy_, 4.0, "#F6E3E0", RED)
                + f'<path d="M{cx - 2.3} {cy_ + 2.3} L{cx + 2.3} {cy_ - 2.3}" '
                  f'stroke="{RED}" stroke-width="1.1"/>'
                  f'<path d="M{cx + 2.3} {cy_ + 2.3} L{cx - 2.3} {cy_ - 2.3}" '
                  f'stroke="{RED}" stroke-width="1.1"/>')

    icons = {"SETTLE": ic_settle, "EXPLORE": ic_explore, "ATTACK": ic_attack,
             "CASH": lambda cx, cy_: coin(cx, cy_, 3.2)}
    for key, col, detail in card_uses(GOLD, FOREST, RED, STONE):
        box, h = option_box(x + 3, cy, iw, key, detail, col, icons[key])
        body += box; cy += h + 1.2
    body += f'<path d="M{x + 3} {cy + 0.6} L{x + colw - 3} {cy + 0.6}" ' \
            f'stroke="{LINE}" stroke-width="0.4"/>'
    w, n = wrap(x + 3, cy + 4.4,
                "Every card: IN REACH — a tile you hold or one beside it — "
                "and its SUIT MATCHES THE GROUND.", iw, 2.8, INK)
    body += w
    heights.append(cy + 4.4 + n * 3.6 - ctop + 1.6)
    panel_a = body

    # ---------- a coin
    x = M + colw + 5
    body = hdr(x, "A COIN", lambda cx, cy_: coin(cx, cy_, 2.8))
    cy = ctop + 14.5
    body += T(x + 3, cy, "buys one of —", 3.0, col=SOFT)
    cy += 3.6

    def ic_research(cx, cy_):
        return (minicard(cx - 3.2, cy_ - 4.5, 6.4, 9.0, col=OCEAN)
                + up_arrow(cx, cy_, 3.4, OCEAN))

    def ic_fortify(cx, cy_):
        return hexgon(cx, cy_, 4.0, "#EFE3C4", GOLD) + coin(cx, cy_ - 0.2, 2.0)

    def ic_keep(cx, cy_):
        return coin(cx - 1.7, cy_ + 0.6, 2.2) + coin(cx + 1.5, cy_ - 0.9, 2.2)

    cicons = {"RESEARCH": ic_research, "FORTIFY": ic_fortify, "KEEP": ic_keep}
    for key, price, detail in COIN_USES:
        box, h = option_box(x + 3, cy, iw, key, detail, LINE, cicons[key],
                            keycol=INK, right=price)
        body += box; cy += h + 1.2
    body += f'<path d="M{x + 3} {cy + 0.6} L{x + colw - 3} {cy + 0.6}" ' \
            f'stroke="{LINE}" stroke-width="0.4"/>'
    w, n = wrap(x + 3, cy + 4.4,
                "Move coins freely on your own turn. Between turns they stand where "
                "you left them — which is when a wall is tested.", iw, 2.8, INK)
    body += w
    heights.append(cy + 4.4 + n * 3.6 - ctop + 1.6)
    panel_b = body

    # ---------- a victory-row card
    x = M + 2 * (colw + 5)
    body = hdr(x, "A VICTORY-ROW CARD",
               lambda cx, cy_: minicard(cx - 2.3, cy_ - 3.1, 4.6, 6.2, col=GOLD,
                                        fill="#FBF3DC"))
    cy = ctop + 14.5
    body += T(x + 3, cy, "spend it on ONE of —", 3.0, col=SOFT)
    cy += 3.6
    for key, when, detail in VROW_USES:
        def ring(cx, cy_, k=key):
            return (disc(cx, cy_, 4.0, PANEL, GOLD)
                    + T(cx, cy_ + 1.5, k, 4.4, anchor="middle", weight="700", col=GOLD))
        box, h = option_box(x + 3, cy, iw, when, detail, LINE, ring,
                            keycol=INK, key_size=3.1)
        body += box; cy += h + 1.2
    body += f'<path d="M{x + 3} {cy + 0.6} L{x + colw - 3} {cy + 0.6}" ' \
            f'stroke="{LINE}" stroke-width="0.4"/>'
    body += T(x + 3, cy + 4.4, "THEN IT LEAVES THE ROW", 3.0, weight="700", col=RED)
    w, n = wrap(x + 3, cy + 8.2,
                "– 1 point · your centre card may drop · a shallower perk "
                "menu next recycle. It goes to the BOTTOM of the shared pile: nothing "
                "leaves the game.", iw, 2.7, SOFT)
    body += w
    heights.append(cy + 8.2 + n * 3.5 - ctop + 1.6)
    panel_c = body

    ch = max(heights)
    for i in range(3):
        b += panel(M + i * (colw + 5), ctop, colw, ch)
    b += panel_a + panel_b + panel_c
    return b, ctop + ch


# THE FREE ACTIONS THIS SHEET DOES NOT REPEAT.
#
# RESEARCH and FORTIFY are both PRICED IN COINS and are already spelled out, in
# full, in the "A COIN" column. COLONY is effect B and is already in the
# victory-row column. GOLD (shifting coins between reserve and walls) is
# already the closing note of the coin column.
#
# All four were printed twice on the one-page sheet, word for word, about 60mm
# apart - a third of the lower half was a second copy of the upper half. A
# player aid that says a thing twice is not being thorough, it is making the
# reader check whether the two copies agree.
#
# What is left here is what genuinely has no other home: the two ways a unit
# moves without a card.
FREE_ONLY = ("MOVE", "WATER")


def free_actions():
    return [f for f in FREE if f[0] in FREE_ONLY]


def _page(body, y, label, note):
    """Close a page: rule, footer, guard, and the wrapped SVG."""
    body += f'<path d="M{M} {y} L{W - M} {y}" stroke="{LINE}" stroke-width="0.4"/>'
    body += T(M, y + 4.4, "Blink · deep-diversions.com/blink", 2.8, col=FAINT)
    body += T(W - M, y + 4.4, note, 2.8, anchor="end", col=FAINT)
    bottom = y + 6
    if bottom > H - M:
        raise SystemExit(f"!! {label} runs past the page: "
                         f"{bottom:.1f}mm > {H - M:.1f}mm")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" '
            f'viewBox="0 0 {W} {H}">'
            f'<rect width="{W}" height="{H}" fill="{PAPER}"/>{body}</svg>'), bottom


def back():
    """SIDE TWO: how the cards move, and what the map is worth.

    Side one answers "what do I do with this card, right now". This side
    answers the two questions that outlast a turn: where does a card GO, and
    what am I building towards. They were on neither sheet.
    """
    b = ""
    y = M + 6
    b += T(M, y, "BLINK", 8.5, weight="700", spacing="0.4")
    b += T(M + text_w("BLINK", 8.5, "700", 0.4) + 5, y,
           "the card loop · the recycle · what the map scores", 4.0, col=SOFT)
    b += T(W - M, y, f"rules {VTAG}", 3.4, anchor="end", col=FAINT, mono=True)
    y += 3.0
    b += f'<path d="M{M} {y} L{W - M} {y}" stroke="{INK}" stroke-width="0.7"/>'
    y += 8.5

    # ============================================= 1. WHERE YOUR CARDS GO
    # Measured: 10.6 cards a game reach the shared pile and 10.2 are drawn back
    # out by OTHER players - 96% recirculated. It is the only system in Blink
    # with no physical tell on the table, and a player who does not know it
    # hoards cards they would have got back anyway.
    b += head(M, y, "WHERE YOUR CARDS GO", "almost nothing leaves the game")
    y += 5.0
    n = len(FLOW)
    fw = (W - 2 * M - (n - 1) * 5.5) / n
    fh = 0
    for key, mid, sub in FLOW:
        fh = max(fh, 10.5 + len(split(mid, fw - 6, 2.9)) * 3.8
                 + 1.4 + len(split(sub, fw - 6, 2.6)) * 3.3 + 2.6)
    for i, (key, mid, sub) in enumerate(FLOW):
        x = M + i * (fw + 5.5)
        b += panel(x, y, fw, fh, accent=GOLD if i in (0, n - 1) else None)
        b += T(x + 3, y + 6.0, key, 3.4, weight="700", spacing="0.2")
        w1, n1 = wrap(x + 3, y + 11.0, mid, fw - 6, 2.9, INK)
        b += w1
        b += wrap(x + 3, y + 11.0 + n1 * 3.8 + 1.4, sub, fw - 6, 2.6, FAINT)[0]
        if i < n - 1:
            b += arrow(x + fw + 0.6, y + fh / 2, x + fw + 4.9, col=GOLD)
    # the loop closes: an arrow from the last box back under the row to the first
    ly = y + fh + 3.2
    b += (f'<path d="M{M + (n - 1) * (fw + 5.5) + fw / 2} {y + fh} '
          f'L{M + (n - 1) * (fw + 5.5) + fw / 2} {ly} L{M + fw / 2} {ly} '
          f'L{M + fw / 2} {y + fh}" fill="none" stroke="{GOLD}" '
          f'stroke-width="0.5" stroke-dasharray="1.6 1.4"/>')
    y = ly + 4.6
    # A FIXED SECOND COLUMN, not label-width + a gap. text_w() is an estimate
    # and it ran short here, so the label and its answer overprinted each
    # other on all three lines. A column cannot collide.
    col2 = M + 62
    for label, where in FLOW_ASIDE:
        b += T(M + 3, y, label, 3.0, weight="600")
        b += T(col2, y, where, 3.0, col=SOFT)
        y += 4.4
    y += 4.0

    # ============================================= 2. THE RECYCLE
    b += head(M, y, "THE RECYCLE", "the moment your hand runs out")
    y += 5.0
    rw = (W - 2 * M - 3 * 4) / 4
    rh = 0
    for key, tag, what in RECYCLE:
        rh = max(rh, 16.0 + len(split(what, rw - 7, 2.9)) * 3.8 + 2.4)
    for i, (key, tag, what) in enumerate(RECYCLE):
        x = M + i * (rw + 4)
        module = tag == "modules only"
        b += panel(x, y, rw, rh, accent=None if module else GOLD,
                   fill=PANEL if module else PAPER)
        b += T(x + 3, y + 6.0, key, 3.4, weight="700", spacing="0.2",
               col=SOFT if module else INK)
        # ON ITS OWN LINE. Right-aligned beside the key, "modules only" ran
        # straight through "2 · ARM A PERK" - the longest key on the row.
        b += T(x + 3, y + 10.2, tag, 2.7, col=FAINT if module else GOLD, mono=True)
        b += wrap(x + 3, y + 15.4, what, rw - 7, 2.9, SOFT if module else INK)[0]
        if i < len(RECYCLE) - 1:
            b += arrow(x + rw + 0.4, y + rh / 2, x + rw + 3.6)
    y += rh + 3.4
    b += T(M, y, "Greyed steps are MODULES ONLY — a base game recycles by refilling, "
                 "and nothing else.", 3.0, col=SOFT, italic=True)
    y += 8.0

    # ============================================= 3. THE MAP, AND WHAT IT PAYS
    b += head(M, y, "MAP OBJECTIVES", "the only points about the SHAPE of what you hold")
    y += 5.0
    ow = (W - 2 * M - 5) * 0.56
    iw2 = (W - 2 * M - 5) - ow
    otop = y

    ob = ""
    cy = y + 6.2
    ob += T(M + 4, cy, OBJECTIVES["show"], 3.8, weight="700", col=GOLD)
    cy += 5.2
    iwrap = ow - 13          # the panel is 4mm of padding a side; leave headroom
    for k in ("what", "bend", "deal"):
        w1, n1 = wrap(M + 4, cy, OBJECTIVES[k], iwrap, 2.9, INK if k == "what" else SOFT)
        ob += w1; cy += n1 * 3.8 + 1.8
    cy += 1.0
    # WRAPPED, not a single line: "2 points for every arrangement you hold at
    # the end" is longer than the panel and ran off its right edge.
    w1, n1 = wrap(M + 4, cy, OBJECTIVES["score"], iwrap, 3.4, INK, weight="700")
    ob += w1; cy += n1 * 4.4 + 1.2
    w1, n1 = wrap(M + 4, cy, OBJECTIVES["twice"], iwrap, 2.9, SOFT)
    ob += w1; cy += n1 * 3.8 + 1.4
    w1, n1 = wrap(M + 4, cy, OBJECTIVES["cost"], iwrap, 2.9, RED)
    ob += w1; cy += n1 * 3.8 + 2.4
    oh = cy - otop

    ib = ""
    ix = M + ow + 5
    cy2 = otop + 6.2
    ib += T(ix + 4, cy2, "INCOME", 3.8, weight="700", col=SOFT)
    ib += T(ix + iw2 - 4, cy2, "modules only", 2.7, anchor="end", col=FAINT, mono=True)
    cy2 += 5.0
    for key, what in INCOME:
        ib += T(ix + 4, cy2, key, 3.0, weight="600", col=SOFT)
        cy2 += 3.9
        w1, n1 = wrap(ix + 4, cy2, what, iw2 - 11, 2.8, FAINT)
        ib += w1; cy2 += n1 * 3.6 + 2.0
    ih = cy2 - otop
    h = max(oh, ih) + 1.5
    b += panel(M, otop, ow, h, accent=GOLD) + ob
    b += panel(ix, otop, iw2, h, fill=PANEL) + ib
    y = otop + h + 8.0

    # ============================================= 5. free, and only what is new
    b += head(M, y, "FREE", "no card · any order · on your own turn")
    y += 4.5
    acts = free_actions()
    fw2 = (W - 2 * M - (len(acts)) * 3) / (len(acts) + 1)
    rowh = 0
    for key, when, detail in acts:
        rowh = max(rowh, 7.4 + len(split(detail, fw2 - 6, 2.6)) * 3.3 + 1.4)
    rowh = max(rowh, 7.4 + 3 * 3.3 + 1.4)
    for i, (key, when, detail) in enumerate(acts):
        fx = M + i * (fw2 + 3)
        b += panel(fx, y, fw2, rowh)
        b += T(fx + 3, y + 4.9, key, 3.4, weight="700", spacing="0.2")
        if when:
            b += T(fx + fw2 - 3, y + 4.9, when, 2.9, anchor="end", col=GOLD, mono=True)
        b += wrap(fx + 3, y + 8.8, detail, fw2 - 6, 2.6, SOFT)[0]
    # and a pointer rather than a second copy
    fx = M + len(acts) * (fw2 + 3)
    b += panel(fx, y, fw2, rowh, fill=PANEL)
    b += T(fx + 3, y + 4.9, "RESEARCH · FORTIFY", 3.2, weight="700", col=SOFT)
    b += wrap(fx + 3, y + 8.8,
              "both cost coins — priced in full on the front, under A COIN. "
              "COLONY is effect B, in the victory-row column.",
              fw2 - 8, 2.6, FAINT)[0]
    y += rowh + 8.0

    # ============================================= 6. the terrain, at last
    # CUT FROM THE ONE-PAGE SHEET FOR ROOM, and the footer used to send the
    # reader to the folded card for it. It is the table you actually look up
    # mid-turn - how many units fit, and what the ground is worth to a
    # defender - and side two has the space the single sheet never had.
    b += head(M, y, "THE GROUND", "what each terrain holds, and what it is worth to defend")
    y += 4.8
    ter = terrain(GOLD, FOREST, OCEAN, STONE)
    tww = (W - 2 * M - 3 * 4) / 4
    th = 13.0
    for i, (name, colr, note) in enumerate(ter):
        tx = M + i * (tww + 4)
        b += panel(tx, y, tww, th)
        b += hexgon(tx + 6.5, y + 6.6, 3.4, colr)
        b += T(tx + 12.5, y + 6.0, name, 3.4, weight="700")
        b += T(tx + 12.5, y + 10.4, note, 2.9, col=SOFT)
    y += th + 3.0

    return _page(b, y, "side two",
                 "side one carries the round, the meld rule and your options")





def build():
    b, y = sheet()
    y += 7.0

    # THE PRICES BELONG BESIDE THE COLUMN THEY PRICE. A, B and C are the three
    # boxes of the victory-row column directly above this table; on the back
    # they were a page-turn away from the only thing that reads them, and the
    # two sides came out 226mm and 273mm.
    b += head(M, y, "WHAT A, B AND C ARE WORTH", "by the rank of the card you spend")
    y += 4.5
    rows = effect_bands()
    bands = ["1–5", "6–10", "11–15", "16–20"]
    tw = W - 2 * M
    colx = [M + 3, M + 26, M + 66, M + 140]
    b += f'<rect x="{M}" y="{y}" width="{tw}" height="6" rx="1.6" fill="{PANEL}"/>'
    for cxx, hd in zip(colx, ["RANK", "A · the trick", "B · the map", "C · gold"]):
        b += T(cxx, y + 4.2, hd, 3.2, weight="700", spacing="0.2")
    y += 6
    for i, (band, r) in enumerate(zip(bands, rows)):
        if i % 2:
            b += (f'<rect x="{M}" y="{y}" width="{tw}" height="6" fill="{PANEL}" '
                  f'fill-opacity="0.5"/>')
        b += T(colx[0], y + 4.2, band, 3.2, mono=True, weight="600")
        b += T(colx[1], y + 4.2, r["a"], 3.2)
        b += T(colx[2], y + 4.2, r["b"], 3.2)
        b += T(colx[3], y + 4.2, r["c"], 3.2, col=GOLD, weight="700", mono=True)
        y += 6
    b += T(M, y + 4.2, "A is declared AFTER every meld is face up, leader first. "
                       "One effect per player per round.", 3.0, col=SOFT, italic=True)
    y += 9.0

    b += T(M, y, "TURN OVER for where your cards go, the recycle, and what the "
                 "map scores.", 3.2, col=SOFT, italic=True)
    y += 3.0
    front, fb = _page(b, y, "side one",
                      "side two carries the card loop, the recycle and the objectives")
    (HERE / "Blink-aid-visual.svg").write_text(front, encoding="utf8")
    rear, rb = back()
    (HERE / "Blink-aid-visual-2.svg").write_text(rear, encoding="utf8")
    print(f"  Blink-aid-visual.svg    (A4 side 1, ends at {fb:.0f}mm of {H:.0f})")
    print(f"  Blink-aid-visual-2.svg  (A4 side 2, ends at {rb:.0f}mm of {H:.0f})")
    return front


if __name__ == "__main__":
    build()
