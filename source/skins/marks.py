# -*- coding: utf-8 -*-
"""The effect marks. Twelve effects exist in the whole deck — four rank bands
times A / B / C — so the card bottom can be drawn instead of written.

Everything is built from six pieces: a tile, a unit, a fortification, a reach,
a coin, and a numeral. Learn those six and every card in the deck is legible.
"""

COLOUR = {
    "plains":   {"ink": "#9B7A16", "pale": "#F7ECC9"},
    "forest":   {"ink": "#1E4229", "pale": "#DCEBE0"},
    "ocean":    {"ink": "#123D53", "pale": "#D8E9F2"},
    "mountain": {"ink": "#5A544C", "pale": "#E9E6E1"},
}
ORDER = ("plains", "forest", "ocean", "mountain")


def _tile(x, y, ink, pale, w=15, h=13):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="1.8" '
            f'fill="{pale}" stroke="{ink}" stroke-width="1.1"/>')


def _tile_any(x, y, w=15, h=13):
    """A tile of any terrain: quartered into the four."""
    hw, hh = w / 2, h / 2
    q = ORDER
    parts = "".join(
        f'<rect x="{x + (i % 2) * hw}" y="{y + (i // 2) * hh}" '
        f'width="{hw}" height="{hh}" fill="{COLOUR[q[i]]["pale"]}"/>'
        for i in range(4))
    return (f'<g><clipPath id="q{x}{y}"><rect x="{x}" y="{y}" width="{w}" '
            f'height="{h}" rx="1.8"/></clipPath>'
            f'<g clip-path="url(#q{x}{y})">{parts}</g>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="1.8" '
            f'fill="none" stroke="#6B6660" stroke-width="1.1"/></g>')


def _unit(cx, cy, ink):
    return (f'<circle cx="{cx}" cy="{cy}" r="2.9" fill="{ink}" '
            f'stroke="#fff" stroke-width="1"/>')


def shield_at(cx, cy, ink, s=1.0):
    r = 4.4 * s
    return (f'<path d="M{cx} {cy - r} l{r} {r * .42} v{r * .72} '
            f'c0 {r * .62} -{r * .55} {r * .95} -{r} {r * 1.28} '
            f'c-{r * .45} -{r * .33} -{r} -{r * .66} -{r} -{r * 1.28} '
            f'v-{r * .72} z" fill="#fff" stroke="{ink}" stroke-width="1.05" '
            f'stroke-linejoin="round"/>')


def mark_a(rank, ink, ties):
    """A · card phase. Add this card's own rank to the meld total; on two of
    the four bands, also take ties."""
    w = 46 if ties else 26
    tie = ""
    if ties:
        tie = (f'<g stroke="{ink}" stroke-width="1.5" fill="none" '
               f'stroke-linecap="round">'
               f'<path d="M30 8h11M30 14h11"/>'
               f'<path d="M31.5 20.5l2.6 2.6L41 16.4"/></g>')
    return (f'<svg class="mk" viewBox="0 0 {w} 24" aria-hidden="true">'
            f'<rect x="0" y="1.5" width="25" height="21" rx="3.4" fill="{ink}"/>'
            f'<text x="12.5" y="17.4" text-anchor="middle" fill="#fff" '
            f'font-family="Fraunces, Georgia, serif" font-weight="600" '
            f'font-size="13.5">+{rank}</text>{tie}</svg>')


def mark_b(band, suit):
    """B · map phase. Found a colony, and what the four bands add to it."""
    ink, pale = COLOUR[suit]["ink"], COLOUR[suit]["pale"]
    if band == 0:                                    # 1 tile, this suit
        return (f'<svg class="mk" viewBox="0 0 23 24" aria-hidden="true">'
                f'{_tile(2, 6, ink, pale)}{_unit(8.5, 14.5, ink)}'
                f'{shield_at(17.4, 6.6, ink)}</svg>')
    if band == 1:                                    # …up to 2 tiles out
        return (f'<svg class="mk" viewBox="0 0 40 24" aria-hidden="true">'
                f'<g stroke="{ink}" stroke-width="1.4" fill="none" '
                f'stroke-linecap="round" stroke-dasharray="1.2 2.6" '
                f'opacity=".85"><path d="M1.5 12.5h14"/></g>'
                f'<circle cx="4.5" cy="12.5" r="1.5" fill="{ink}"/>'
                f'<circle cx="10" cy="12.5" r="1.5" fill="{ink}"/>'
                f'{_tile(18, 6, ink, pale)}{_unit(24.5, 14.5, ink)}'
                f'{shield_at(33.4, 6.6, ink)}</svg>')
    if band == 2:                                    # 2 tiles, 1 unit
        return (f'<svg class="mk" viewBox="0 0 39 24" aria-hidden="true">'
                f'{_tile(2, 6, ink, pale)}'
                f'{_tile(18, 6, ink, pale)}{_unit(24.5, 14.5, ink)}'
                f'{shield_at(33.4, 6.6, ink)}</svg>')
    return (f'<svg class="mk" viewBox="0 0 41 24" aria-hidden="true">'
            f'{_tile_any(2, 6)}{_unit(8.5, 14.5, "#3C3833")}'
            f'{shield_at(17.4, 6.6, "#6B6660")}'
            f'{_tile_any(20, 6)}{_unit(26.5, 14.5, "#3C3833")}'
            f'{shield_at(35.4, 6.6, "#6B6660")}</svg>')


def mark_c(gold, ink):
    """C · take gold."""
    return (f'<svg class="mk" viewBox="0 0 22 24" aria-hidden="true">'
            f'<circle cx="11" cy="12.5" r="9.6" fill="#EFD489" '
            f'stroke="{ink}" stroke-width="1.15"/>'
            f'<circle cx="11" cy="12.5" r="6.6" fill="none" stroke="{ink}" '
            f'stroke-width=".7" opacity=".6"/>'
            f'<text x="11" y="17" text-anchor="middle" fill="#4A3A0C" '
            f'font-family="Fraunces, Georgia, serif" font-weight="600" '
            f'font-size="10.5">{gold}</text></svg>')
