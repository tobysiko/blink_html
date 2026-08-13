# -*- coding: utf-8 -*-
"""Blink -- black-and-white versions of the booklets.

A post-processor, not a second set of builders. It reads the HTML the normal
builders produce and rewrites two things:

  * the CSS palette, so page furniture prints as tone rather than colour;
  * every inline <svg>, so terrain reads as hatch instead of hue.

Doing it this way means there is exactly one source for the words and one source
for the figures. A rules change cannot land in the colour booklet and miss the
mono one, which is the failure mode this whole project keeps running into.

  python3 build_bw.py                 # all four booklets + the player board
  python3 build_bw.py Blink-rules-v0.20.html   # or any one booklet
"""
import sys, re, pathlib
import cardstock as CS
from version import RULES_HTML

DEFAULT = [RULES_HTML, "Blink-first-game.html",
           "Blink-card-effects.html", "Blink-map-objectives.html"]

# Greys chosen so the four terrains stay ordered and separable. The rulebook's
# terrain chips encode elevation as *height* as well as colour, so plains and
# ocean -- the two short ones -- are pushed to opposite ends of the ramp.
PALETTE = {
    "--paper":    "#FFFFFF",     # white paper: no full-bleed tint to print
    "--page":     "#FFFFFF",
    "--ink":      "#000000",
    "--ink-soft": "#3F3F3F",
    "--plains":   "#B4B4B4",
    "--stone":    "#8A8A8A",
    "--forest":   "#5C5C5C",
    "--ocean":    "#2B2B2B",
    "--red":      "#000000",
    "--rule":     "#B0B0B0",
}

EXTRA_CSS = """
/* ---- black-and-white overrides ---- */
.sheet{box-shadow:none;border:none}
/* light chips need an outline or they vanish on white */
.chip::before{outline:.5px solid #000;outline-offset:-.5px}
/* the stepped rule is four tones; give it edges so they stay countable */
.steprule i{box-shadow:inset 0 0 0 .5px #000}
img,svg{filter:none}
@media print{ body{background:#fff} .sheet{background:#fff} }
"""

SVG_RE = re.compile(r"<svg\b.*?</svg>", re.S)


def recolour_css(html):
    """Drain the colour out of every <style> block.

    Named palette entries get a chosen grey; anything else left in the sheet --
    figure backgrounds, callout tints, the odd hard-coded red -- falls through to
    its luminance grey. Operating on the style blocks only means SVG payloads in
    the body are untouched here; mono_svg has already handled those.
    """
    def one_style(m):
        css = m.group(0)
        for name, grey in PALETTE.items():
            css = re.sub(rf"({re.escape(name)}\s*:\s*)#[0-9A-Fa-f]{{3,6}}",
                         rf"\g<1>{grey}", css)
        return re.sub(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b",
                      lambda c: CS._grey(c.group(0)), css)
    return re.sub(r"<style>.*?</style>", one_style, html, flags=re.S)


def convert(path):
    src = pathlib.Path(path)
    html = src.read_text(encoding="utf-8")

    n = 0
    def sub(m):
        nonlocal n
        n += 1
        return CS.mono_svg(m.group(0))
    body = SVG_RE.sub(sub, html)

    body = recolour_css(body)
    # appended after the greying pass so these greys are not re-greyed
    body = body.replace("</style>", EXTRA_CSS + "</style>", 1)

    left = re.findall(r"rgb\(|hsl\(", body)
    if left:
        print(f"  note: {len(left)} non-hex colour functions left in {src.name}")

    out = src.with_name(src.stem + "-bw.html")
    out.write_text(body, encoding="utf-8")
    print(f"{out.name:34s} {n:3d} figures converted")
    return out


if __name__ == "__main__":
    targets = sys.argv[1:] or DEFAULT
    for t in targets:
        if pathlib.Path(t).exists():
            convert(t)
        else:
            print(f"skipped (not built yet): {t}")

    # the player boards are standalone SVG, not HTML
    for svg in ("board_a4.svg", "board_blank.svg"):
        p = pathlib.Path(svg)
        if p.exists():
            o = p.with_name(p.stem + "-bw.svg")
            o.write_text(CS.mono_svg(p.read_text(encoding="utf-8")), encoding="utf-8")
            print(f"{o.name:34s}   1 board converted")
