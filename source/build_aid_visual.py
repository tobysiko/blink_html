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
from aid_data import ROUND, COIN_USES, VROW_USES, FREE, card_uses, terrain  # noqa: E402
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


def text_w(s, size, weight="400", spacing=0.0):
    """Rough advance width in mm.

    There is no text engine here, so every wrapped line and every heading used
    to be a GUESSED character count - and the first build of this sheet had
    text running out of nine different boxes, headings sitting on top of their
    own subtitles, and one sentence cut off mid-word.

    A single average per weight was not enough either: the second build still
    ran every SECTION HEADING into its own subtitle, because headings are bold
    ALL-CAPS and capitals in this family are half again as wide as lowercase.
    Per-character classes cost nothing and are right to within a percent or
    two, which is all a layout needs.
    """
    bold = 1.06 if weight in ("600", "700") else 1.0
    total = 0.0
    for ch in s:
        if ch == " ":
            k = 0.27
        elif ch.isupper():
            k = 0.72
        elif ch.isdigit():
            k = 0.56
        elif ch in ".,:;'\u2019!|":
            k = 0.26
        elif ch in "\u2014\u2013\u2192":
            k = 0.62
        elif ch in "ijlt":
            k = 0.28
        elif ch in "mw":
            k = 0.82
        else:
            k = 0.53
        total += size * k * bold + spacing
    # A FEW PER CENT OF HEADROOM. Measured widths came out about 4% short
    # against the real font, which is invisible on a heading and shows up as a
    # word touching the border on every fourth wrapped line. Cheaper to add it
    # here once than to pad twelve call sites.
    return total * 1.07


def split(s, w_mm, size, weight="400"):
    """The lines `s` breaks into inside `w_mm`."""
    lines, line = [], ""
    for word in s.split():
        t = (line + " " + word).strip()
        if text_w(t, size, weight) > w_mm - 0.6 and line:
            lines.append(line); line = word
        else:
            line = t
    lines.append(line)
    return lines


def wrap(x, y, s, w_mm, size=3.0, col=SOFT, lead=None, anchor="start",
         weight="400"):
    """Returns (svg, lines_used). Width is MILLIMETRES, not characters."""
    lead = lead or size * 1.30
    lines = split(s, w_mm, size, weight)
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
                + text_w(right, 3.1, "700") + 3)
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
    b += T(M, y, "Your hand runs out mid-turn? Recycle at once — take your discard "
                 "back and draw to ten — then carry on.", 3.0, col=SOFT, italic=True)
    y += 7.5

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
                + T(cx, cy_ + 1.6, "↑", 5.0, anchor="middle", col=OCEAN, weight="700"))

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
                "− 1 point · your centre card may drop · a shallower perk "
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


def build():
    b, y = sheet()
    y += 7

    # ================================================== 3. A, B and C, priced
    b += head(M, y, "WHAT A, B AND C ARE WORTH", "by the rank of the card you spend")
    y += 4.5
    rows = effect_bands()
    bands = ["1–5", "6–10", "11–15", "16–20"]
    tw = W - 2 * M
    colx = [M + 3, M + 26, M + 66, M + 140]
    b += f'<rect x="{M}" y="{y}" width="{tw}" height="6" rx="1.6" fill="{PANEL}"/>'
    for cxx, h in zip(colx, ["RANK", "A · the trick", "B · the map", "C · gold"]):
        b += T(cxx, y + 4.2, h, 3.2, weight="700", spacing="0.2")
    y += 6
    for i, (band, r) in enumerate(zip(bands, rows)):
        if i % 2:
            b += (f'<rect x="{M}" y="{y}" width="{tw}" height="7" fill="{PANEL}" '
                  f'fill-opacity="0.5"/>')
        b += T(colx[0], y + 4.2, band, 3.2, mono=True, weight="600")
        b += T(colx[1], y + 4.2, r["a"], 3.2)
        b += T(colx[2], y + 4.2, r["b"], 3.2)
        b += T(colx[3], y + 4.2, r["c"], 3.2, col=GOLD, weight="700", mono=True)
        y += 6
    b += T(M, y + 4.2, "A is declared AFTER every meld is face up, leader first. "
                       "One effect per player per round.", 3.0, col=SOFT, italic=True)
    y += 9.5

    # ================================================== 4. free actions
    b += head(M, y, "FREE", "no card · any order · on your own turn")
    y += 4.5
    fw = (W - 2 * M - 2 * 3) / 3
    rowh = 0
    for key, when, detail in FREE:
        rowh = max(rowh, 7.4 + len(split(detail, fw - 6, 2.6)) * 3.3 + 1.4)
    for i, (key, when, detail) in enumerate(FREE):
        fx = M + (i % 3) * (fw + 3)
        fy = y + (i // 3) * (rowh + 2.5)
        b += panel(fx, fy, fw, rowh)
        b += T(fx + 3, fy + 4.9, key, 3.4, weight="700", spacing="0.2")
        if when:
            b += T(fx + fw - 3, fy + 4.9, when, 2.9, anchor="end", col=GOLD, mono=True)
        b += wrap(fx + 3, fy + 8.8, detail, fw - 6, 2.6, SOFT)[0]
    y += 2 * (rowh + 2.5) + 2

    # THE TERRAIN STRIP IS NOT HERE ON PURPOSE. It is reference, not a
    # decision, it is already on the folded card, and with every box on this
    # sheet sized from its own text there was no longer room for both. The
    # footer says where it lives.
    b += f'<path d="M{M} {y} L{W - M} {y}" stroke="{LINE}" stroke-width="0.4"/>'
    b += T(M, y + 4.4, "Blink · deep-diversions.com/blink", 2.8, col=FAINT)
    b += T(W - M, y + 4.4,
           "the folded card carries the tier ladder and the meld rule",
           2.8, anchor="end", col=FAINT)

    bottom = y + 6
    if bottom > H - M:
        raise SystemExit(f"!! the sheet runs past the page: {bottom:.1f}mm > {H - M:.1f}mm")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" '
           f'viewBox="0 0 {W} {H}">'
           f'<rect width="{W}" height="{H}" fill="{PAPER}"/>{b}</svg>')
    (HERE / "Blink-aid-visual.svg").write_text(svg, encoding="utf8")
    print(f"  Blink-aid-visual.svg  (A4 portrait, content ends at "
          f"{bottom:.0f}mm of {H:.0f})")
    return svg


if __name__ == "__main__":
    build()
