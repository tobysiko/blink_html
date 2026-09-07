# -*- coding: utf-8 -*-
"""Blink card back — the seam between what was made and what is coming.

One diagonal from the lower-left to the upper-right splits the card. Below it,
parchment: warm, aged, drawn with the instruments of the old world. Above it,
a cold blue horizon drawn in circuitry and orbits. Both ornament layers are
drawn across the whole card and then clipped to their side, so the diagonal
cuts through the drawings themselves rather than politely avoiding them.

The wordmark is set twice in the same place — dark on the parchment side, pale
on the blue — and each copy is clipped to its own half. The letter the seam
happens to cross is therefore split along the diagonal, in ink on one side of
the cut and in light on the other.

Card is 63 x 88 mm; the SVG user unit is the millimetre.
"""

W, H = 63, 88
PAST_POLY = "0,6 63,82 63,88 0,88"
FUT_POLY = "0,0 63,0 63,82 0,6"

PARCHMENT_INK = "#5E4413"
FUTURE_INK = "#7FDCF2"


def _defs(uid):
    return f"""
<defs>
  <linearGradient id="past{uid}" gradientUnits="userSpaceOnUse"
      x1="31.5" y1="44" x2="-11" y2="79">
    <stop offset="0" stop-color="#F6ECD3"/>
    <stop offset=".45" stop-color="#E7D2A4"/>
    <stop offset="1" stop-color="#BB9346"/>
  </linearGradient>
  <linearGradient id="fut{uid}" gradientUnits="userSpaceOnUse"
      x1="31.5" y1="44" x2="74" y2="9">
    <stop offset="0" stop-color="#1D6E93"/>
    <stop offset=".42" stop-color="#0E3D5A"/>
    <stop offset="1" stop-color="#061826"/>
  </linearGradient>
  <linearGradient id="seam{uid}" gradientUnits="userSpaceOnUse"
      x1="0" y1="6" x2="63" y2="82">
    <stop offset="0" stop-color="#8A6B1E"/>
    <stop offset=".5" stop-color="#F2E4C0"/>
    <stop offset="1" stop-color="#6FD8F0"/>
  </linearGradient>
  <clipPath id="pc{uid}"><polygon points="{PAST_POLY}"/></clipPath>
  <clipPath id="fc{uid}"><polygon points="{FUT_POLY}"/></clipPath>
  <clipPath id="card{uid}"><rect width="{W}" height="{H}" rx="2.6"/></clipPath>
</defs>"""


def _past_ornaments():
    """Instruments of the made world: a cartwheel, an amphora, an arch, a
    ship, and the furrows of a ploughed field."""
    return f"""
<g fill="none" stroke="{PARCHMENT_INK}" stroke-width=".45" opacity=".26"
   stroke-linecap="round">
  <circle cx="11" cy="43" r="9"/><circle cx="11" cy="43" r="2.4"/>
  <path d="M11 34v18M2 43h18M4.6 36.6l12.8 12.8M17.4 36.6L4.6 49.4"/>
  <path d="M6 66q0-3 3-3.4V60h4v2.6q3 .4 3 3.4 0 6-2.5 9.5h-5Q6 72 6 66Z"/>
  <path d="M6.4 65q-2.6.6-2.6 3.4M15.6 65q2.6.6 2.6 3.4"/>
  <path d="M39 82V70a5.5 5.5 0 0 1 11 0v12"/>
  <path d="M36.5 70h16M37.6 82h13.8"/>
  <path d="M43 60h13l-2.2 4.6H45.2Z"/><path d="M49.5 60V47"/>
  <path d="M45.4 49.4q4.1-1.6 8.2 0v6.6q-4.1-1.6-8.2 0Z"/>
  <path d="M-2 78q10-3 20 0t20 0 20 0M-2 83q10-3 20 0t20 0 20 0"/>
  <path d="M28 52l-4.6 11M28 52l4.6 11M28 52a1.4 1.4 0 1 0 0-.1"/>
</g>"""


def _future_ornaments():
    """The world still being drawn: orbits, a printed trace, a lattice, a
    signal."""
    return f"""
<g fill="none" stroke="{FUTURE_INK}" stroke-width=".45" opacity=".3"
   stroke-linecap="round">
  <circle cx="47" cy="19" r="3"/>
  <ellipse cx="47" cy="19" rx="11" ry="4.4" transform="rotate(-28 47 19)"/>
  <ellipse cx="47" cy="19" rx="11" ry="4.4" transform="rotate(34 47 19)"/>
  <circle cx="56.6" cy="14.2" r="1" fill="{FUTURE_INK}" stroke="none"/>
  <path d="M34 44h6v-7h7v-5h9"/><path d="M34 50h11v6h11"/>
  <path d="M40 44v6"/>
  <circle cx="34" cy="44" r=".9" fill="{FUTURE_INK}" stroke="none"/>
  <circle cx="34" cy="50" r=".9" fill="{FUTURE_INK}" stroke="none"/>
  <circle cx="56" cy="32" r=".9" fill="{FUTURE_INK}" stroke="none"/>
  <circle cx="56" cy="56" r=".9" fill="{FUTURE_INK}" stroke="none"/>
  <rect x="43" y="62" width="12" height="9" rx=".8"/>
  <path d="M43 64.5h-2.6M43 66.75h-2.6M43 69h-2.6M55 64.5h2.6M55 66.75h2.6M55 69h2.6"/>
  <path d="M9 6l3 1.7v3.5L9 13l-3-1.8V7.7Z"/>
  <path d="M15 9.5l3 1.7v3.5l-3 1.8-3-1.8v-3.5Z"/>
  <path d="M21 13l3 1.7v3.5L21 20l-3-1.8v-3.5Z"/>
  <path d="M26 30h3l2-5 3 10 2.4-5H41"/>
</g>"""


def _wordmark(uid, fill, clip):
    letters = [("B", 21), ("L", 35.5), ("I", 50), ("N", 64.5), ("K", 79)]
    body = "".join(
        f'<text x="31.5" y="{y}" fill="{fill}">{c}</text>' for c, y in letters)
    return (f'<g clip-path="url(#{clip}{uid})" font-family="Fraunces, Georgia, serif" '
            f'font-weight="600" font-size="13.5" text-anchor="middle" '
            f'letter-spacing=".4">{body}</g>')


def back(uid="a", version="v0.24"):
    return f"""
<svg class="cardback" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg"
     role="img" aria-label="Blink card back">
{_defs(uid)}
<g clip-path="url(#card{uid})">
  <polygon points="{PAST_POLY}" fill="url(#past{uid})"/>
  <polygon points="{FUT_POLY}" fill="url(#fut{uid})"/>
  <g clip-path="url(#pc{uid})">{_past_ornaments()}</g>
  <g clip-path="url(#fc{uid})">{_future_ornaments()}</g>
  <line x1="0" y1="6" x2="63" y2="82" stroke="url(#seam{uid})"
        stroke-width="3.2" opacity=".3"/>
  <line x1="0" y1="6" x2="63" y2="82" stroke="url(#seam{uid})"
        stroke-width=".55" opacity=".95"/>
  {_wordmark(uid, "#42300C", "pc")}
  {_wordmark(uid, "#E6F6FC", "fc")}
  <g clip-path="url(#pc{uid})" font-family="'IBM Plex Mono', monospace"
     font-size="2.1" letter-spacing=".5" fill="#5E4413" opacity=".65">
    <text x="4.5" y="85.5">{version}</text>
  </g>
</g>
<rect x=".35" y=".35" width="{W-.7}" height="{H-.7}" rx="2.4" fill="none"
      stroke="#00000022" stroke-width=".7"/>
</svg>"""
