# -*- coding: utf-8 -*-
"""Shared print-and-play card stock: page geometry, terrain art, palettes.

Two decks are produced from one set of drawings: a colour version and a
black-and-white version that survives a mono laser printer. The B/W version
never relies on hue -- every terrain carries its own hatch pattern *and* its own
glyph, so a photocopied card is still readable.
"""

import re

TER_ORDER = ("mountain", "forest", "plains", "ocean")

HOLDS = {"plains": 3, "forest": 2, "ocean": 1, "mountain": 1}
ATTACK = {"plains": 0, "ocean": 0, "forest": 1, "mountain": 2}

COLOUR = {
    "plains":   {"top": "#D2A93A", "side": "#9B7A16", "pale": "#F7ECC9"},
    "forest":   {"top": "#37704A", "side": "#1E4229", "pale": "#DCEBE0"},
    "ocean":    {"top": "#256A8C", "side": "#123D53", "pale": "#D8E9F2"},
    "mountain": {"top": "#8A837A", "side": "#5A544C", "pale": "#E9E6E1"},
}

HATCH_ID = {t: f"h-{t}" for t in TER_ORDER}

# Hatch patterns, one per terrain, at four clearly different angles/densities.
# Used only by the B/W deck.
HATCH = """
<pattern id="h-mountain" width="6" height="6" patternUnits="userSpaceOnUse">
  <rect width="6" height="6" fill="#fff"/>
  <path d="M0 6 L6 0 M-1 1 L1 -1 M5 7 L7 5 M0 0 L6 6 M-1 5 L1 7 M5 -1 L7 1"
        stroke="#000" stroke-width=".55"/></pattern>
<pattern id="h-forest" width="5" height="5" patternUnits="userSpaceOnUse">
  <rect width="5" height="5" fill="#fff"/>
  <path d="M0 5 L5 0 M-1 1 L1 -1 M4 6 L6 4" stroke="#000" stroke-width=".6"/></pattern>
<pattern id="h-plains" width="7" height="7" patternUnits="userSpaceOnUse">
  <rect width="7" height="7" fill="#fff"/>
  <circle cx="1.6" cy="1.6" r=".65" fill="#000"/>
  <circle cx="5.1" cy="5.1" r=".65" fill="#000"/></pattern>
<pattern id="h-ocean" width="8" height="6" patternUnits="userSpaceOnUse">
  <rect width="8" height="6" fill="#fff"/>
  <path d="M0 3 q2 -2.2 4 0 t4 0" fill="none" stroke="#000" stroke-width=".6"/></pattern>
"""

# Terrain glyphs, drawn in a 24x24 box. Distinct in silhouette, so they carry
# the identification on their own when hue is gone.
GLYPH = {
    "mountain": ('<path d="M2 20 L9 6.5 L13 13 L15.5 9.5 L22 20 Z" fill="{ink}"/>'
                 '<path d="M9 6.5 L6.2 11.9 L9 10.7 L11.3 12.1 Z" fill="{page}"/>'),
    "forest":   ('<path d="M12 2.6 L18.2 12 L14.8 12 L19.6 19 L4.4 19 L9.2 12'
                 ' L5.8 12 Z" fill="{ink}"/>'
                 '<rect x="11" y="18" width="2" height="3.6" fill="{ink}"/>'),
    "plains":   ('<path d="M2.6 19.6 h18.8" stroke="{ink}" stroke-width="1.8"'
                 ' fill="none" stroke-linecap="round"/>'
                 '<path d="M6 19.6 q0 -6 2.4 -8 M11.2 19.6 q-.6 -7.4 1.6 -10'
                 ' M16.6 19.6 q0 -6 2.2 -7.6" stroke="{ink}" stroke-width="1.6"'
                 ' fill="none" stroke-linecap="round"/>'),
    "ocean":    ('<path d="M2.4 8 q3 -3 6 0 t6 0 t5.4 0 M2.4 13.8 q3 -3 6 0 t6 0 t5.4 0'
                 ' M2.4 19.6 q3 -3 6 0 t6 0 t5.4 0" fill="none" stroke="{ink}"'
                 ' stroke-width="1.8" stroke-linecap="round"/>'),
}


def glyph(ter, mono, size=22, ink=None, page="#fff"):
    """An inline SVG terrain glyph, sized in px."""
    if ink is None:
        ink = "#000000" if mono else COLOUR[ter]["side"]
    return (f'<svg class="gl" viewBox="0 0 24 24" width="{size}" height="{size}" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'{GLYPH[ter].format(ink=ink, page=page)}</svg>')


def swatch(ter, mono, w=63, h=13):
    """The wide terrain band across a card: solid colour, or hatch in B/W."""
    if mono:
        return (f'<svg class="sw" viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
                f'xmlns="http://www.w3.org/2000/svg"><defs>{HATCH}</defs>'
                f'<rect width="{w}" height="{h}" fill="url(#{HATCH_ID[ter]})"/>'
                f'<rect width="{w}" height="{h}" fill="none" stroke="#000" '
                f'stroke-width=".5"/></svg>')
    return (f'<svg class="sw" viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<rect width="{w}" height="{h}" fill="{COLOUR[ter]["side"]}"/></svg>')


# Three player colours have to stay three *distinguishable* things without hue,
# because the rulebook figures show players contesting the same tiles.
#   you    solid dark disc with a white rim -- stacks stay countable
#   rival  open disc, black rim
#   third  mid grey disc, black rim
DISC = {
    "#C0392B": ("#1A1A1A", "#FFFFFF", "#1A1A1A"),   # you    (fill, rim, shadow)
    "#EDEAE1": ("#FFFFFF", "#000000", "#7A7A7A"),   # rival
    "#3B3F8F": ("#8C8C8C", "#000000", "#3A3A3A"),   # third
    "#7A4E9B": ("#FFFFFF", "#000000", "#3A3A3A"),   # fourth
}
DISC_EDGE = {"#C0392B": "#7B2018", "#EDEAE1": "#5A544C",
             "#3B3F8F": "#232659", "#7A4E9B": "#4C2F63"}


def _grey(hexcol):
    """Perceptual luminance, so an unmapped colour still prints as a sane tone
    instead of surviving in full colour on a mono printer."""
    h = hexcol.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    y = round(0.2126 * r + 0.7152 * g + 0.0722 * b)
    return f"#{y:02X}{y:02X}{y:02X}"


def mono_svg(body):
    """Recolour a colour figure for black-and-white printing.

    Terrain top faces become hatch patterns -- the same four used on the cards --
    side walls become flat grey so the extrusion still reads, and coloured
    strokes become black, since a mono printer renders mid-tone outlines as mud.
    Anything not explicitly mapped falls through to its luminance grey.
    """
    out = body
    for t in TER_ORDER:
        out = out.replace(f'fill="{COLOUR[t]["top"]}"', f'fill="url(#{HATCH_ID[t]})"')
        out = out.replace(f'fill="{COLOUR[t]["side"]}"', 'fill="#D9D9D9"')
        out = out.replace(f'stroke="{COLOUR[t]["side"]}"', 'stroke="#000000"')
        out = out.replace(f'stroke="{COLOUR[t]["top"]}"', 'stroke="#000000"')
    for base, (fill, rim, shadow) in DISC.items():
        edge = DISC_EDGE[base]
        out = out.replace(f'fill="{edge}"', f'fill="{shadow}"')       # drop shadow
        out = out.replace(f'fill="{base}"', f'fill="{fill}"')
        out = out.replace(f'stroke="{edge}"', f'stroke="{rim}"')
    out = (out.replace('fill="#E8C25A"', 'fill="#FFFFFF"')            # gold
              .replace('stroke="#9B7A16"', 'stroke="#000000"')
              .replace('fill="#B4AFA3"', 'fill="#8A8A8A"')
              .replace('stroke="#B4AFA3"', 'stroke="#666666"')
              .replace('stroke="#5A544C"', 'stroke="#000000"'))
    # catch-all: any colour left standing becomes its luminance grey
    out = re.sub(r'(fill|stroke)="(#[0-9A-Fa-f]{3,6})"',
                 lambda m: f'{m.group(1)}="{_grey(m.group(2))}"', out)
    i = out.index(">") + 1                      # just after the opening <svg ...>
    return out[:i] + "<defs>" + HATCH + "</defs>" + out[i:]


PAGE_CSS = """
@page { size: A4; margin: 9mm 8mm; }
* { box-sizing: border-box; }
body { margin: 0; font-family: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
       -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.sheet { width: 189mm; font-size: 0; }
.card { width: 63mm; height: 88mm; display: inline-flex; flex-direction: column;
        vertical-align: top; position: relative; overflow: hidden; font-size: 9pt;
        border: .2mm dashed #aaa; }
.pagebreak { page-break-after: always; }
.sw { display: block; width: 100%; }
.gl { display: block; }
"""
