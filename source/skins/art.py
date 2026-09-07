# -*- coding: utf-8 -*-
"""Blink civ-ladder skin — tech illustrations and effect marks.

Every drawing is line art on a 48x48 field: one stroke weight, round caps and
joins, no interior shading. The colour comes from the card, not from the
drawing, so a single set of paths serves the colour deck and the b/w deck.
"""

TECH = {

    # ---------------- PLAINS · settlement, law, governance ---------------
    "plains-4": (  # Village
        '<path d="M7 38V29l6-5 6 5v9"/>'
        '<path d="M20 38V26l7-6 7 6v12"/>'
        '<path d="M24 38v-6h6v6"/>'
        '<path d="M35 38v-8l5-4 5 4v8"/>'
        '<path d="M3 38h42"/>'),

    "plains-8": (  # Marketplace
        '<path d="M7 18h34"/>'
        '<path d="M7 18q4.25 6 8.5 0t8.5 0 8.5 0 8.5 0"/>'
        '<path d="M9 24v16M39 24v16"/>'
        '<path d="M13 32h22M16 32v8M32 32v8"/>'
        '<circle cx="20" cy="28.6" r="2.6"/><circle cx="28" cy="28.6" r="2.6"/>'),

    "plains-12": (  # Guildhall
        '<path d="M9 40V23l13-9 13 9v17"/>'
        '<path d="M18 40v-9a4 4 0 0 1 8 0v9"/>'
        '<path d="M12.5 25h4.5v4.5h-4.5z"/><path d="M27 25h4.5v4.5H27z"/>'
        '<path d="M35 27h7M41.5 27v4"/><path d="M38 31h7v5h-7z"/>'
        '<path d="M5 40h40"/>'),

    "plains-18": (  # Parliament
        '<path d="M24 8v3"/>'
        '<path d="M14 25a10 10 0 0 1 20 0"/>'
        '<path d="M10 25h28"/>'
        '<path d="M13 27.5v9M19 27.5v9M29 27.5v9M35 27.5v9"/>'
        '<path d="M22 27.5v9M26 27.5v9" opacity=".45"/>'
        '<path d="M9 36.5h30M6 40.5h36"/>'),

    # ---------------- FOREST · tools, machines, knowledge ----------------
    "forest-4": (  # The Wheel
        '<circle cx="24" cy="23" r="13"/>'
        '<circle cx="24" cy="23" r="3.4"/>'
        '<path d="M24 10v26M11 23h26"/>'
        '<path d="M5 39h38"/>'),

    "forest-8": (  # Block and Tackle
        '<path d="M8 8h32"/>'
        '<path d="M20 8v5M28 8v5"/>'
        '<circle cx="24" cy="17" r="4.2"/>'
        '<path d="M20 18.5v8M28 18.5v8"/>'
        '<circle cx="24" cy="30" r="4.2"/>'
        '<path d="M18 34.5h12v7H18z"/>'),

    "forest-12": (  # The Lens
        '<path d="M24 9q9 15 0 30 -9-15 0-30Z"/>'
        '<path d="M4 15h11M4 24h11M4 33h11"/>'
        '<path d="M31 19.5l11 4.5M32 24h10M31 28.5l11-4.5"/>'
        '<circle cx="43" cy="24" r="1.7" fill="currentColor" stroke="none"/>'),

    "forest-18": (  # Electricity
        '<path d="M16 21a8 8 0 1 1 16 0c0 4.4-2.8 6-2.8 9h-10.4c0-3-2.8-4.6-2.8-9Z"/>'
        '<path d="M19 33.5h10M20.5 37.5h7"/>'
        '<path d="M26 13.5l-4.5 7.5h5l-3.5 7"/>'
        '<path d="M7 21h4M37 21h4M11 10l3 3M37 13l3-3"/>'),

    # ---------------- MOUNTAIN · metal, engineering, defence -------------
    "mountain-4": (  # Palisade
        '<path d="M6 39V21l3-5 3 5v18"/>'
        '<path d="M15 39V21l3-5 3 5v18"/>'
        '<path d="M27 39V21l3-5 3 5v18"/>'
        '<path d="M36 39V21l3-5 3 5v18"/>'
        '<path d="M4 25h40M4 33h40"/>'),

    "mountain-8": (  # Stonemasonry
        '<path d="M7 12h34v28H7z"/>'
        '<path d="M7 21.3h34M7 30.6h34"/>'
        '<path d="M19 12v9.3M31 12v9.3"/>'
        '<path d="M13 21.3v9.3M25 21.3v9.3M37 21.3v9.3"/>'
        '<path d="M19 30.6v9.4M31 30.6v9.4"/>'),

    "mountain-12": (  # Crossbow
        '<path d="M8 21h30v6H8z"/>'
        '<path d="M38 11q7 13 0 26"/>'
        '<path d="M38 11L22 24l16 13"/>'
        '<path d="M22 24h18"/><path d="M40 21.5L45 24l-5 2.5z" fill="currentColor"/>'
        '<path d="M14 27v5"/>'),

    "mountain-18": (  # Blast Furnace
        '<path d="M15 40V19l4-8h10l4 8v21Z"/>'
        '<path d="M15 26h18M15 33h18"/>'
        '<path d="M20 40v-4a4 4 0 0 1 8 0v4"/>'
        '<path d="M20 9q0-3.5 3-4t3-4"/><path d="M29 9q1.5-3 5-3"/>'
        '<path d="M7 40h34"/>'),

    # ---------------- OCEAN · seafaring, trade, frontier -----------------
    "ocean-4": (  # The Oar
        '<ellipse cx="35" cy="12" rx="4.4" ry="7.4" transform="rotate(38 35 12)"/>'
        '<path d="M31.5 16.5L13 39"/>'
        '<path d="M10.5 40.5l4.5-3.6"/>'
        '<path d="M3 43q4.5-3.2 9 0t9 0 9 0 9 0"/>'),

    "ocean-8": (  # Coinage
        '<circle cx="18" cy="24" r="12"/><circle cx="18" cy="24" r="7.5"/>'
        '<circle cx="18" cy="24" r="2.2" fill="currentColor" stroke="none"/>'
        '<ellipse cx="37" cy="31" rx="7" ry="2.6"/>'
        '<ellipse cx="37" cy="25" rx="7" ry="2.6"/>'
        '<path d="M30 25v6M44 25v6"/>'),

    "ocean-12": (  # Lighthouse
        '<path d="M18 39L21 16h6l3 23Z"/>'
        '<path d="M19.4 29h9.2M20.2 22.5h7.6"/>'
        '<path d="M19.5 16h9"/>'
        '<path d="M20 16v-5h8v5"/><path d="M19 11l5-4.5 5 4.5"/>'
        '<path d="M17.5 8L7 4M17 13.5L5 12M30.5 8L41 4M31 13.5l12-1.5"/>'
        '<path d="M3 43q4.5-3.2 9 0t9 0 9 0 9 0"/>'),

    "ocean-18": (  # Steamship
        '<path d="M6 29h36l-4.5 9H10.5z"/>'
        '<path d="M15 29v-5h13v5"/>'
        '<path d="M20 24v-9h5.5v9"/>'
        '<path d="M22 12.5q0-3 3-3.5t3-3.5"/><path d="M28.5 11q2-2.5 5-2.5"/>'
        '<path d="M34 29V13"/><path d="M30.5 17h7"/>'
        '<path d="M3 43q4.5-3.2 9 0t9 0 9 0 9 0"/>'),
}


def tech(suit, rank):
    """The illustration for one card, as an inline SVG."""
    body = TECH.get("%s-%s" % (suit, rank))
    if body is None:
        return ('<svg class="tech ghost" viewBox="0 0 48 48" aria-hidden="true">'
                '<path d="M12 36V16l12-8 12 8v20Z" stroke-dasharray="3 3"/></svg>')
    return ('<svg class="tech" viewBox="0 0 48 48" aria-hidden="true">'
            + body + '</svg>')
