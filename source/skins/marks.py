# -*- coding: utf-8 -*-
"""The effect marks. Twelve effects exist in the whole deck — four rank bands
times A / B / C — so the card bottom can be drawn instead of written.

Everything is built from six pieces: a hex, a unit, a fortification, a reach,
a coin, and a numeral. Learn those six and every card in the deck is legible.

The hex is pointy-top, the same orientation `figs.py` draws the map in, so the
mark on the card and the tile on the table are the same shape.
"""

import itertools

_uid = itertools.count()

SQ = 0.8660254            # sin 60°: half-width of a pointy-top hex, per unit R

COLOUR = {
    "plains":   {"ink": "#9B7A16", "pale": "#F7ECC9", "strong": "#B07E10"},
    "forest":   {"ink": "#1E4229", "pale": "#DCEBE0", "strong": "#2E7A4A"},
    "ocean":    {"ink": "#123D53", "pale": "#D8E9F2", "strong": "#1B7099"},
    "mountain": {"ink": "#5A544C", "pale": "#E9E6E1", "strong": "#6E6459"},
}
ORDER = ("plains", "forest", "ocean", "mountain")

R = 8.4                   # hex radius used by every B mark
HW = R * SQ               # 7.27 — half-width
CY = 11.2                 # every mark is drawn in a 22-high field


def hex_points(cx, cy, r=R):
    pts = [(cx, cy - r), (cx + r * SQ, cy - r / 2), (cx + r * SQ, cy + r / 2),
           (cx, cy + r), (cx - r * SQ, cy + r / 2), (cx - r * SQ, cy - r / 2)]
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)


def _hex(cx, cy, ink, pale, r=R, fortified=False):
    out = (f'<polygon points="{hex_points(cx, cy, r)}" fill="{pale}" '
           f'stroke="{ink}" stroke-width="1.3" stroke-linejoin="round"/>')
    if fortified:
        out = _rampart(cx, cy, ink, r) + out
    return out


def _rampart(cx, cy, ink, r=R):
    """Fortified: a wall drawn around the tile. A ring costs no footprint of its
    own, which a badge does — and at 6 mm a badge and a hex and a unit disc all
    inside one square just merge."""
    return (f'<polygon points="{hex_points(cx, cy, r + 1.9)}" fill="none" '
            f'stroke="{ink}" stroke-width="1.1" stroke-linejoin="round" '
            f'opacity=".9"/>')


def _hex_any(cx, cy, r=R, fortified=False):
    """A hex of any terrain: four strata, one per suit."""
    u = f"any{next(_uid)}"
    band = 2 * r / 4
    strata = "".join(
        f'<rect x="{cx - r}" y="{cy - r + i * band}" width="{2 * r}" '
        f'height="{band + .02}" fill="{COLOUR[t]["pale"]}"/>'
        for i, t in enumerate(ORDER))
    ring = _rampart(cx, cy, "#6B6660", r) if fortified else ""
    return (f'<g>{ring}<clipPath id="{u}"><polygon points="{hex_points(cx, cy, r)}"/>'
            f'</clipPath><g clip-path="url(#{u})">{strata}</g>'
            f'<polygon points="{hex_points(cx, cy, r)}" fill="none" '
            f'stroke="#6B6660" stroke-width="1.3" stroke-linejoin="round"/></g>')


def _unit(cx, cy, ink):
    return (f'<circle cx="{cx}" cy="{cy}" r="3" fill="{ink}" '
            f'stroke="#fff" stroke-width="1.05"/>')


def shield_at(cx, cy, ink, r=4.1):
    """Fortified. Sits on a hex's upper-right vertex, white-backed so it reads
    over whatever it overlaps."""
    return (f'<path d="M{cx} {cy - r} l{r} {r * .42} v{r * .72} '
            f'c0 {r * .62} -{r * .55} {r * .95} -{r} {r * 1.28} '
            f'c-{r * .45} -{r * .33} -{r} -{r * .66} -{r} -{r * 1.28} '
            f'v-{r * .72} z" fill="#fff" stroke="{ink}" stroke-width="1.2" '
            f'stroke-linejoin="round"/>')


def _colony(cx, ink, pale, any_terrain=False):
    """A founded colony: a fortified tile with one unit standing on it."""
    if any_terrain:
        return _hex_any(cx, CY, fortified=True) + _unit(cx, CY, "#3C3833")
    return _hex(cx, CY, ink, pale, fortified=True) + _unit(cx, CY, ink)


def _badge(x, ink, glyph):
    """A's badge is card-shaped — 16 x 22, the same 0.72 proportion as the card
    it is printed on. B is hexes because it acts on the map, C is discs because
    it is coins, and A is a little card because it acts in the card phase. The
    shape does the separating, so no rule or label has to."""
    return (f'<g><rect x="{x}" y="0" width="16" height="22" rx="2.2" '
            f'fill="{ink}"/><g transform="translate({x},0)" stroke="#fff" '
            f'stroke-width="2.5" stroke-linecap="round" fill="none">{glyph}</g></g>')


PLUS = '<path d="M8 5.4v11.2M2.4 11h11.2"/>'
EQUALS = '<path d="M3 8h10M3 14h10"/>'


def mark_a(ink, ties):
    """A · card phase. Add this card's own rank to the meld total; on two of
    the four bands, also take ties.

    The badge does NOT restate the rank. The rank is already printed in all four
    corners, the rule is the same on all eighty cards, and a numeral is the one
    thing here that cannot be read upside-down — which matters because a card in
    the victory row may be sitting the other way round. A plus and an equals sign
    are both unchanged by a half turn."""
    if not ties:
        return (f'<svg class="mk" viewBox="0 0 16 22" aria-hidden="true">'
                f'{_badge(0, ink, PLUS)}</svg>')
    return (f'<svg class="mk" viewBox="0 0 35 22" aria-hidden="true">'
            f'{_badge(0, ink, PLUS)}{_badge(19, ink, EQUALS)}</svg>')


def mark_b(band, suit):
    """B · map phase. Found a colony, and what the four bands add to it."""
    ink, pale = COLOUR[suit]["ink"], COLOUR[suit]["pale"]
    if band == 0:                                    # 1 hex, this suit
        return (f'<svg class="mk" viewBox="0 0 20 22" aria-hidden="true">'
                f'{_colony(10, ink, pale)}</svg>')
    if band == 1:                                    # …up to 2 hexes out
        return (f'<svg class="mk" viewBox="0 0 35 22" aria-hidden="true">'
                f'<path d="M1.6 {CY}h12.6" stroke="{ink}" stroke-width="1.5" '
                f'fill="none" stroke-linecap="round" stroke-dasharray="1.3 2.8" '
                f'opacity=".85"/>'
                f'<circle cx="3.6" cy="{CY}" r="1.7" fill="{ink}"/>'
                f'<circle cx="9.2" cy="{CY}" r="1.7" fill="{ink}"/>'
                f'{_colony(25, ink, pale)}</svg>')
    if band == 2:                                    # 2 hexes, the second held
        return (f'<svg class="mk" viewBox="0 0 37 22" aria-hidden="true">'
                f'{_hex(9, CY, ink, pale)}{_colony(27, ink, pale)}</svg>')
    return (f'<svg class="mk" viewBox="0 0 40 22" aria-hidden="true">'
            f'{_colony(10, ink, pale, any_terrain=True)}'
            f'{_colony(30, ink, pale, any_terrain=True)}</svg>')


def mark_c(gold, ink):
    """C · take gold. Counted in coins rather than written as a numeral: discs
    are unchanged by a half turn, and a row of them is countable from either end.
    Two to five is inside the range a person reads at a glance."""
    step, r = 9.6, 4.5
    coins = "".join(
        f'<g><circle cx="{5.2 + i * step}" cy="11" r="{r}" fill="#EFD489" '
        f'stroke="{ink}" stroke-width="1.1"/>'
        f'<circle cx="{5.2 + i * step}" cy="11" r="{r - 1.7}" fill="none" '
        f'stroke="{ink}" stroke-width=".6" opacity=".55"/></g>'
        for i in range(gold))
    w = (gold - 1) * step + 10.4
    return (f'<svg class="mk" viewBox="0 0 {w:.1f} 22" aria-hidden="true">'
            f'{coins}</svg>')
